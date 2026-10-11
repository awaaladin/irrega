"""Water saved vs a fixed schedule. Assumption (stated in the UI): a typical fixed schedule waters every day
at the crop's daily need (ETc). We count litres NOT applied on days our recommendation was SKIP and the farmer
did not water, and litres of over-application avoided; we never count litres we cannot back with a recorded day."""
from apps.decisions.models import Recommendation

BASELINE_NOTE = "Compared with watering every day at the crop's daily need (a common fixed schedule)."


def water_saved_l(farm_or_field, days=30):
    from datetime import timedelta

    from django.utils import timezone

    since = timezone.localdate() - timedelta(days=days)
    qs = Recommendation.objects.filter(date__gte=since)
    qs = qs.filter(field=farm_or_field) if hasattr(farm_or_field, "crop") else qs.filter(field__farm=farm_or_field)
    saved = 0.0
    for r in qs.select_related("field"):
        p = r.payload
        etc, area, eff = p["balance"]["etc_mm"], p["inputs"]["area_m2"], p["inputs"]["efficiency"]
        baseline_l = etc * area / eff
        last = r.decisions.first()
        applied = r.volume_l if (last is None or last.kind == "accept") and r.action.startswith("IRRIGATE") else 0
        if last and last.kind == "override":
            applied = (last.litres or 0) if last.farmer_action != "SKIP" else 0
        saved += max(baseline_l - applied, 0)
    return round(saved)
