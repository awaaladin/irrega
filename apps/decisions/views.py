import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from apps.engine import explain
from apps.engine.savings import BASELINE_NOTE, water_saved_l
from apps.farms.models import Farm, Field
from apps.providers import satellite

from .models import Decision, Recommendation

ACTIONS = {"IRRIGATE", "SKIP", "LATER"}
REASONS = {"already_watered", "rain_started", "no_water", "know_my_soil", "crop_looks_thirsty", "other", ""}


@login_required
@require_POST
def api_decide(request):
    try:
        data = json.loads(request.body or "{}")
        rec = Recommendation.objects.select_related("field__farm").get(pk=data.get("recommendation"), field__farm__owner=request.user)
    except (Recommendation.DoesNotExist, ValueError, json.JSONDecodeError):
        return JsonResponse({"error": "We could not find that recommendation."}, status=404)
    kind = data.get("kind")
    if kind not in ("accept", "override", "snooze"):
        return JsonResponse({"error": "Unknown choice."}, status=400)
    action = data.get("farmer_action", "") if kind == "override" else ""
    litres = data.get("litres")
    if kind == "override":
        if action not in ACTIONS:
            return JsonResponse({"error": "Choose what you will do: water, skip, or water later."}, status=400)
        if action == "IRRIGATE":
            try:
                litres = float(litres)
                if not 0 < litres <= 5_000_000:
                    raise ValueError
            except (TypeError, ValueError):
                return JsonResponse({"error": "Enter how many litres you will use."}, status=400)
        else:
            litres = None
    else:
        litres = rec.volume_l if kind == "accept" and rec.action.startswith("IRRIGATE") else None
    reason = data.get("reason", "")
    if reason not in REASONS:
        reason = "other"
    d = Decision.objects.create(recommendation=rec, user=request.user, kind=kind, farmer_action=action, litres=litres,
                                reason=reason, note=(data.get("note") or "")[:300])
    return JsonResponse({"ok": True, "id": d.pk})


@login_required
def insights(request):
    from apps.engine.services import get_recommendation
    from apps.farms.views import _card

    farms = list(Farm.objects.filter(owner=request.user).prefetch_related("fields__crop"))
    lang = request.user.language
    fields = [f for farm in farms for f in farm.fields.all()]
    cards = [_card(f, lang) for f in fields]
    decisions = Decision.objects.filter(user=request.user).select_related("recommendation__field")[:30]
    total = Decision.objects.filter(user=request.user).count()
    over = Decision.objects.filter(user=request.user, kind="override").count()
    tiles = []
    for c in cards:
        vals = c["ndvi_values"][-6:]
        latest = c["ndvi"][-1] if c["ndvi"] else None
        # 3 x 3 heat tiles: a simple spread around the latest value so the tile reads as a patch, labelled simulated when it is
        tiles.append({"card": c, "latest": latest, "values": vals})
    return render(request, "decisions/insights.html", {
        "active": "Insights", "cards": cards, "tiles": tiles, "decisions": decisions, "farms": farms,
        "water_saved": sum(water_saved_l(f) for f in fields), "baseline_note": BASELINE_NOTE,
        "override_rate": round(100 * over / total) if total else 0, "total_decisions": total,
        "map_fields": json.dumps([{"name": f.name, "lat": f.lat, "lon": f.lon, "crop": f.crop.name, "id": f.pk} for f in fields]),
        "farm_centre": json.dumps([farms[0].latitude, farms[0].longitude] if farms else [4.9517, 8.3220]),
    })
