from datetime import timedelta

from django.db.models import Count
from django.utils import timezone

from .models import PilotCode


def apply_pilot_code(user, code):
    """Attach a pilot invite code: longer free trial and linked to the partner organisation."""
    if not code:
        return False
    pc = PilotCode.objects.filter(code__iexact=code.strip(), active=True).first()
    if not pc or pc.uses >= pc.max_uses:
        return False
    pc.uses += 1
    pc.save(update_fields=["uses"])
    if pc.organization:
        user.organization = pc.organization
        user.save(update_fields=["organization"])
    sub = getattr(user, "subscription", None)
    if sub:
        sub.trial_ends = timezone.localdate() + timedelta(days=pc.trial_days)
        sub.save(update_fields=["trial_ends"])
    return True


def onboarding_steps(user):
    from apps.assistant.models import ChatMessage
    from apps.decisions.models import Decision
    from apps.farms.models import Field, MoistureReading

    fields = Field.objects.filter(farm__owner=user)
    steps = [
        ("Add your farm and a field", fields.exists(), "/farms/onboarding/"),
        ("Enter a soil moisture reading", MoistureReading.objects.filter(field__farm__owner=user).exists(), "/"),
        ("Respond to a recommendation", Decision.objects.filter(user=user).exists(), "/"),
        ("Ask a question", ChatMessage.objects.filter(user=user).exists(), "/farms/"),
        ("Turn on morning alerts", getattr(getattr(user, "notification_prefs", None), "sms", False) or getattr(getattr(user, "notification_prefs", None), "whatsapp", False), "/notifications/settings/"),
    ]
    return [{"label": l, "done": bool(d), "href": h} for l, d, h in steps]


def farm_stats(farm):
    """Per-farm numbers for the partner dashboard."""
    from apps.decisions.models import Decision, Recommendation

    recs = Recommendation.objects.filter(field__farm=farm)
    decisions = Decision.objects.filter(recommendation__field__farm=farm)
    total = decisions.count()
    overrides = decisions.filter(kind="override").count()
    from apps.engine.savings import water_saved_l

    return {
        "farm": farm,
        "fields": farm.fields.count(),
        "recs": recs.count(),
        "decisions": total,
        "override_rate": round(100 * overrides / total) if total else 0,
        "water_saved_l": water_saved_l(farm),
        "flags": data_quality_flags(farm),
    }


def data_quality_flags(farm):
    from apps.providers import weather

    flags = []
    for f in farm.fields.all():
        r = f.readings.first()
        if r is None:
            flags.append(f"{f.name}: no soil readings")
        elif (timezone.now() - r.taken_at).total_seconds() > 48 * 3600:
            flags.append(f"{f.name}: soil reading older than 2 days")
    snap = weather.latest(farm)
    if snap is None or (weather.age_hours(snap) or 0) > 6 and not snap.is_demo:
        flags.append("Weather forecast is stale")
    return flags
