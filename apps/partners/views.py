from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from apps.billing.models import Plan
from apps.farms.models import Farm
from apps.providers import llm, satellite, weather

from .models import Organization, PilotCode, PilotFeedback
from .services import farm_stats


def _org_farms(user):
    if user.role == "admin" or user.is_superuser:
        return Farm.objects.all()
    return Farm.objects.filter(organization=user.organization) if user.organization_id else Farm.objects.none()


@login_required
def dashboard(request):
    if not request.user.is_partner:
        return HttpResponseForbidden("This page is for partner organisations.")
    farms = _org_farms(request.user).select_related("owner", "organization")
    rows = [farm_stats(f) for f in farms]
    totals = {
        "farms": len(rows), "fields": sum(r["fields"] for r in rows), "water_saved_l": sum(r["water_saved_l"] for r in rows),
        "decisions": sum(r["decisions"] for r in rows),
        "override_rate": round(sum(r["override_rate"] * r["decisions"] for r in rows) / max(sum(r["decisions"] for r in rows), 1)),
        "flags": sum(len(r["flags"]) for r in rows),
    }
    feedback = PilotFeedback.objects.filter(user__organization=request.user.organization)[:6] if request.user.organization_id else []
    return render(request, "partners/dashboard.html", {"active": "Partner", "rows": rows, "totals": totals, "org": request.user.organization, "feedback": feedback})


@login_required
@require_POST
def feedback(request):
    try:
        rating = max(1, min(5, int(request.POST.get("rating", 0))))
    except ValueError:
        rating = 0
    if rating:
        PilotFeedback.objects.create(user=request.user, rating=rating, text=request.POST.get("text", "")[:600])
        messages.success(request, "Thank you. Your feedback helps us improve the pilot.")
    return redirect(request.META.get("HTTP_REFERER", "/"))


@login_required
def pilot_results(request):
    """Simple 'pilot results' summary for the signed-in farmer's farms."""
    farms = Farm.objects.filter(owner=request.user)
    rows = [farm_stats(f) for f in farms]
    return render(request, "partners/pilot.html", {"active": "Account", "rows": rows, "feedback": PilotFeedback.objects.filter(user=request.user)[:5]})


@login_required
def system(request):
    if not (request.user.role == "admin" or request.user.is_superuser):
        return HttpResponseForbidden("Admins only.")
    User = get_user_model()
    from django.utils import timezone

    snap = weather.latest(Farm.objects.first()) if Farm.objects.exists() else None
    health = [
        {"name": "Weather (Open-Meteo)", "ok": bool(snap), "detail": f"last fetch {snap.fetched_at:%d %b %H:%M} ({snap.source})" if snap else "no snapshots yet"},
        {"name": "Satellite crop stress", "ok": True, "detail": type(satellite.get_provider()).__name__ + (" (simulated fallback)" if satellite.get_provider().simulated else "")},
        {"name": "AI explanations", "ok": True, "detail": "Claude" if llm.get_provider().name == "claude" else "Template fallback (no ANTHROPIC_API_KEY)"},
    ]
    if request.method == "POST" and request.POST.get("code"):
        PilotCode.objects.get_or_create(code=request.POST["code"].upper()[:20], defaults=dict(
            organization=Organization.objects.filter(pk=request.POST.get("org") or 0).first(), trial_days=int(request.POST.get("days") or 60)))
        return redirect("partners:system")
    return render(request, "partners/system.html", {
        "active": "System", "health": health, "users": User.objects.order_by("-date_joined")[:40], "plans": Plan.objects.all(),
        "codes": PilotCode.objects.all(), "orgs": Organization.objects.all(), "now": timezone.now(),
    })
