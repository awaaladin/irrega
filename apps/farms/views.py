import csv
import io
import json
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.accounts.models import ApiKey
from apps.assistant.models import ChatMessage
from apps.billing.services import within_plan
from apps.decisions.models import Decision
from apps.engine import explain
from apps.engine.charts import moisture_chart
from apps.engine.savings import BASELINE_NOTE, water_saved_l
from apps.engine.services import get_recommendation
from apps.partners.services import onboarding_steps
from apps.providers import satellite, weather

from .crops import growth_stage
from .forms import FarmForm, FieldForm, YieldForm
from .models import Farm, Field, MoistureReading


def user_field(user, pk):
    return get_object_or_404(Field.objects.select_related("crop", "farm"), pk=pk, farm__owner=user)


def _card(field, lang):
    rec = get_recommendation(field)
    p = explain.present(rec.payload, lang)
    latest = field.readings.first()
    ndvi = list(satellite.series(field, 45))
    return {"field": field, "rec": rec, "p": p, "latest": latest, "ndvi": ndvi, "ndvi_values": [n.ndvi for n in ndvi],
            "decided": rec.decisions.first(), "age_days": (timezone.localdate() - field.planting_date).days}


def _weather_strip(farm):
    snap = weather.refresh(farm)
    if not snap:
        return None
    from datetime import date

    days = []
    for d in snap.days[:5]:
        dt = date.fromisoformat(d["date"])
        days.append({**d, "dow": "Today" if dt == timezone.localdate() else dt.strftime("%a"), "heavy": d["rain_prob"] >= 60})
    age = weather.age_hours(snap)
    return {"days": days, "demo": snap.is_demo, "fetched": snap.fetched_at, "stale": (not snap.is_demo) and (age or 0) > 6, "source": snap.source}


def landing(request):
    from .landing_content import SCREENS

    return render(request, "landing.html", {"screens": SCREENS})


def guide(request):
    """The full how-to. Inside the dashboard shell when signed in; the same page for visitors, in a plain shell."""
    from . import landing_content as c

    return render(request, "guide.html", {
        "layout": "app.html" if request.user.is_authenticated else "public.html", "active": "Guide",
        "toc": c.TOC_GUIDE, "screens": c.SCREENS, "glossary": c.GLOSSARY, "quickstart": c.QUICKSTART,
        "daily": c.DAILY_ROUTINE, "situations": c.SITUATIONS, "actions": ["IRRIGATE_NOW", "IRRIGATE_LATER_TODAY", "SKIP_TODAY", "WATCH"],
    })


def home(request):
    """Signed-in farmers land on Today; everyone else sees the landing page that explains each screen."""
    if request.user.is_authenticated:
        return today(request)
    return landing(request)


@login_required
def today(request):
    farms = list(Farm.objects.filter(owner=request.user))
    lang = request.user.language
    fields = list(Field.objects.filter(farm__in=farms).select_related("crop", "farm"))
    if not farms or not fields:
        # Stay on Today and explain the next step, instead of bouncing a new farmer to another tab.
        return render(request, "farms/today_empty.html", {
            "active": "Today", "has_farm": bool(farms),
            "next_url": f"/farms/{farms[0].pk}/fields/new/" if farms else "/farms/onboarding/",
        })
    cards = [_card(f, lang) for f in fields]
    farm = farms[0]
    steps = onboarding_steps(request.user)
    ctx = {
        "active": "Today", "cards": cards, "farm": farm, "weather": _weather_strip(farm),
        "water_saved": sum(water_saved_l(f) for f in farms), "baseline_note": BASELINE_NOTE,
        "steps": steps, "steps_done": sum(s["done"] for s in steps), "show_checklist": not all(s["done"] for s in steps),
        "learned": learned_suggestions(request.user), "any_demo": any(c["rec"].is_demo for c in cards),
        "attention": [c for c in cards if c["p"]["action"] in ("IRRIGATE_NOW", "WATCH")],
    }
    return render(request, "farms/today.html", ctx)


def learned_suggestions(user):
    """'You overrode 3 of the last 10 skips.' Suggestion only; the engine never changes silently."""
    out = []
    for f in Field.objects.filter(farm__owner=user):
        skips = list(Decision.objects.filter(recommendation__field=f, recommendation__action="SKIP_TODAY").order_by("-created")[:10])
        over = [d for d in skips if d.kind == "override" and d.farmer_action == "IRRIGATE"]
        if len(skips) >= 5 and len(over) >= 3:
            out.append({"field": f, "text": f"You overrode {len(over)} of the last {len(skips)} skips on {f.name}. Want us to be more cautious here?"})
    return out


@login_required
def field_list(request):
    farms = Farm.objects.filter(owner=request.user)
    return render(request, "farms/field_list.html", {"active": "Fields", "farms": farms.prefetch_related("fields__crop")})


def _snaps(bal):
    return [{"at": round(bal["trigger_pct"] or bal["fc"], 1), "label": "Water-now line"}, {"at": bal["fc"], "label": "Field capacity"}, {"at": bal["sat"], "label": "Waterlogged"}]


@login_required
def field_detail(request, pk):
    field = user_field(request.user, pk)
    lang = request.user.language
    card = _card(field, lang)
    stage = growth_stage(field.crop.stages, card["age_days"])
    history = Decision.objects.filter(recommendation__field=field).select_related("recommendation")[:15]
    recs = field.recommendations.all()[:14]
    chat = [{"role": m.role, "text": m.text} for m in ChatMessage.objects.filter(field=field, user=request.user).order_by("-id")[:12][::-1]]
    bal = card["rec"].payload["balance"]
    ctx = {
        "active": "Fields", "field": field, "card": card, "chart": moisture_chart(field, card["rec"].payload),
        "stage": stage, "history": history, "recs": [{"r": r, "p": explain.present(r.payload, lang)} for r in recs], "chat": json.dumps(chat),
        "yields": field.yields.all()[:5], "yield_form": YieldForm(),
        "suggested": ["Why this?", "What if I wait a day?", "How much water if I only have 5 cans?", f"Is my {field.crop.name.lower()} stressed?"],
        "snaps": json.dumps(_snaps(bal)), "moisture_max": min(60, bal["sat"] + 10),
        "weather": _weather_strip(field.farm),
    }
    return render(request, "farms/field_detail.html", ctx)


@login_required
def onboarding(request):
    form = FarmForm(request.POST or None, initial={"latitude": 4.9517, "longitude": 8.3220})
    if request.method == "POST" and form.is_valid():
        farm = form.save(commit=False)
        farm.owner = request.user
        farm.organization = request.user.organization
        farm.save()
        return redirect("farms:field_new", farm_id=farm.pk)
    return render(request, "farms/onboarding.html", {"active": "Fields", "form": form, "has_farms": Farm.objects.filter(owner=request.user).exists()})


@login_required
def field_new(request, farm_id):
    farm = get_object_or_404(Farm, pk=farm_id, owner=request.user)
    ok, msg = within_plan(request.user)
    if not ok:
        messages.info(request, msg)
        return redirect("billing:plans")
    form = FieldForm(request.POST or None, initial={"planting_date": timezone.localdate() - timedelta(days=30)})
    if request.method == "POST" and form.is_valid():
        field = form.save(commit=False)
        field.farm = farm
        try:
            field.latitude = float(request.POST["latitude"]) if request.POST.get("latitude") else None
            field.longitude = float(request.POST["longitude"]) if request.POST.get("longitude") else None
        except ValueError:
            pass
        field.save()
        messages.success(request, f"{field.name} added. Add a soil moisture reading for a stronger answer.")
        return redirect("farms:field_detail", pk=field.pk)
    return render(request, "farms/field_form.html", {"active": "Fields", "form": form, "farm": farm, "title": "Add a field"})


@login_required
def field_edit(request, pk):
    field = user_field(request.user, pk)
    form = FieldForm(request.POST or None, instance=field)
    if request.method == "POST" and form.is_valid():
        form.save()
        get_recommendation(field, refresh=True)
        return redirect("farms:field_detail", pk=field.pk)
    return render(request, "farms/field_form.html", {"active": "Fields", "form": form, "farm": field.farm, "field": field, "title": f"Edit {field.name}"})


@login_required
@require_POST
def field_delete(request, pk):
    user_field(request.user, pk).delete()
    messages.success(request, "Field removed.")
    return redirect("farms:list")


@login_required
@require_POST
def yield_add(request, pk):
    field = user_field(request.user, pk)
    form = YieldForm(request.POST)
    if form.is_valid():
        y = form.save(commit=False)
        y.field = field
        y.save()
        get_recommendation(field, refresh=True)
        messages.success(request, "Harvest saved.")
    else:
        messages.error(request, "Could not save that harvest. Check the numbers and try again.")
    return redirect("farms:field_detail", pk=pk)


# ---------- soil moisture inputs ----------
def _save_reading(field, value, source="manual", when=None):
    try:
        value = float(value)
    except (TypeError, ValueError):
        raise ValueError("Enter soil moisture as a number between 0 and 60.")
    if not 0 <= value <= 60:
        raise ValueError("Soil moisture must be between 0 and 60 percent.")
    r = MoistureReading.objects.create(field=field, value=value, source=source, taken_at=when or timezone.now())
    get_recommendation(field, refresh=True)
    return r


@login_required
@require_POST
def api_moisture(request, pk):
    field = user_field(request.user, pk)
    try:
        data = json.loads(request.body or "{}")
        r = _save_reading(field, data.get("value"))
    except (ValueError, json.JSONDecodeError) as e:
        return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"ok": True, "id": r.pk})


@csrf_exempt
@require_POST
def api_readings(request):
    """POST /api/readings/  Authorization: Bearer <key>  {"field": 12, "value": 23.4, "taken_at": "2026-07-10T06:00:00Z"}
    A future sensor can call this. Keys are created on the Account page and scoped to one user's fields."""
    auth = request.headers.get("Authorization", "")
    key = ApiKey.objects.filter(key=auth[7:].strip()).select_related("user").first() if auth.startswith("Bearer ") else None
    if not key:
        return JsonResponse({"error": "Missing or invalid API key."}, status=401)
    try:
        data = json.loads(request.body or "{}")
        field = Field.objects.get(pk=data.get("field"), farm__owner=key.user)
        when = None
        if data.get("taken_at"):
            from django.utils.dateparse import parse_datetime

            when = parse_datetime(data["taken_at"])
            if when is None:
                raise ValueError("taken_at must be an ISO 8601 date-time.")
        r = _save_reading(field, data.get("value"), source="sensor", when=when)
    except (Field.DoesNotExist, TypeError):
        return JsonResponse({"error": "Unknown field."}, status=404)
    except (ValueError, json.JSONDecodeError) as e:
        return JsonResponse({"error": str(e)}, status=400)
    return JsonResponse({"ok": True, "id": r.pk}, status=201)


@login_required
@require_POST
def csv_import(request, pk):
    """CSV with columns: date, moisture  (date as YYYY-MM-DD or ISO date-time)."""
    field = user_field(request.user, pk)
    f = request.FILES.get("file")
    if not f or f.size > 1_000_000:
        messages.error(request, "Choose a CSV file under 1 MB.")
        return redirect("farms:field_detail", pk=pk)
    from datetime import datetime, time

    from django.utils.dateparse import parse_date, parse_datetime

    ok = bad = 0
    for row in csv.DictReader(io.StringIO(f.read().decode("utf-8-sig", errors="replace"))):
        row = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
        raw = row.get("date") or row.get("taken_at") or row.get("time")
        when = parse_datetime(raw) if raw else None
        if when is None and raw and parse_date(raw):
            when = timezone.make_aware(datetime.combine(parse_date(raw), time(6, 0)))
        try:
            if when is None:
                raise ValueError
            val = float(row.get("moisture") or row.get("value"))
            if not 0 <= val <= 60:
                raise ValueError
            MoistureReading.objects.create(field=field, value=val, source="csv", taken_at=when)
            ok += 1
        except (ValueError, TypeError):
            bad += 1
    get_recommendation(field, refresh=True)
    (messages.success if ok else messages.error)(request, f"Imported {ok} readings." + (f" Skipped {bad} rows we could not read." if bad else ""))
    return redirect("farms:field_detail", pk=pk)
