"""Glue between the database and the pure engine."""
from datetime import date as date_cls
from datetime import datetime, timedelta

from django.conf import settings
from django.utils import timezone

from apps.decisions.models import Recommendation
from apps.farms.models import METHODS, SOILS
from apps.providers import satellite, weather

from .core import DayWeather, EngineInput, recommend


def build_input(field, now=None):
    now = now or timezone.localtime()
    today = now.date()
    snap = weather.refresh(field.farm)
    forecast = []
    if snap:
        for d in snap.days:
            if date_cls.fromisoformat(d["date"]) >= today:
                forecast.append(DayWeather(date_cls.fromisoformat(d["date"]), d["rain_mm"], d["rain_prob"], d["et0"], d["tmax"], d["tmin"]))
    satellite.ensure_today(field)
    ndvi_rows = satellite.series(field, 45)
    reading = field.readings.first()
    yields = [{"amount_kg": y.amount_kg, "dry_spell": y.dry_spell} for y in field.yields.all()[:3]]
    return EngineInput(
        today=today, planting_date=field.planting_date, stages=field.crop.stages, root_depth_mm=field.crop.root_depth_mm,
        p=field.crop.depletion_fraction, sensitive_stage=field.crop.sensitive_stage, soil=SOILS[field.soil],
        area_m2=field.area_m2, efficiency=METHODS[field.method]["eff"], method=field.method,
        moisture=reading.value if reading else None,
        moisture_age_h=(now - reading.taken_at).total_seconds() / 3600 if reading else None,
        moisture_simulated=bool(reading and reading.is_simulated),
        forecast=forecast, weather_age_h=weather.age_hours(snap) if snap and not snap.is_demo else (0.0 if snap else None),
        weather_demo=bool(snap and snap.is_demo),
        ndvi=[(r.date, r.ndvi) for r in ndvi_rows], ndvi_simulated=bool(ndvi_rows and ndvi_rows[-1].is_simulated),
        yields=yields, hour=now.hour,
    )


def get_recommendation(field, refresh=False):
    """Today's recommendation. Regenerated while the farmer has not acted on it; frozen once a decision exists."""
    today = timezone.localdate()
    rec = Recommendation.objects.filter(field=field, date=today).first()
    if rec and (rec.decisions.exists() or (not refresh and timezone.now() - rec.created < timedelta(minutes=20))):
        return rec
    out = recommend(build_input(field))
    out["generated_at"] = timezone.now().isoformat()
    out["field"] = {"id": field.pk, "name": field.name, "crop": field.crop.name}
    rec, _ = Recommendation.objects.update_or_create(
        field=field, date=today,
        defaults=dict(action=out["action"], volume_l=out["volume_l"], depth_mm=out["depth_mm"], confidence=out["confidence"],
                      payload=out, is_demo=field.farm.is_demo),
    )
    return rec


def moisture_series(field, days=30):
    since = timezone.now() - timedelta(days=days)
    return list(field.readings.filter(taken_at__gte=since).order_by("taken_at"))
