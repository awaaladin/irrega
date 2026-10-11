"""Weather: Open-Meteo (free, no key). Cached per farm; demo farms use a labelled scenario forecast."""
import logging
from datetime import timedelta

import requests
from django.utils import timezone

from .models import WeatherSnapshot

log = logging.getLogger(__name__)
CACHE_MINUTES = 90
DAILY = "precipitation_sum,precipitation_probability_max,temperature_2m_max,temperature_2m_min,et0_fao_evapotranspiration,wind_speed_10m_max,shortwave_radiation_sum,relative_humidity_2m_mean"

SCENARIOS = {
    # rain_mm, rain_prob, et0, tmax, tmin per day
    "normal": dict(mm=[2, 4, 1, 6, 3, 2], prob=[30, 40, 25, 50, 35, 30], et0=4.4, tmax=30, tmin=23),
    "rainy": dict(mm=[28, 18, 10, 6, 3, 2], prob=[90, 85, 70, 60, 40, 30], et0=3.0, tmax=26, tmin=22),
    "dry": dict(mm=[0, 0, 1, 0, 0, 0], prob=[5, 5, 10, 5, 5, 5], et0=6.4, tmax=35, tmin=25),
}


def demo_days(scenario, start=None):
    start = start or timezone.localdate()
    s = SCENARIOS.get(scenario, SCENARIOS["normal"])
    return [
        {"date": (start + timedelta(days=i)).isoformat(), "rain_mm": s["mm"][i], "rain_prob": s["prob"][i], "et0": round(s["et0"] + (0.2 if i % 2 else -0.1), 1),
         "tmax": s["tmax"] + (i % 2), "tmin": s["tmin"], "humidity": 85 if scenario == "rainy" else 55 if scenario == "dry" else 72, "wind": 9, "solar": 18}
        for i in range(6)
    ]


def _fetch_open_meteo(lat, lon):
    r = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={"latitude": lat, "longitude": lon, "daily": DAILY, "timezone": "Africa/Lagos", "forecast_days": 6},
        timeout=8,
    )
    r.raise_for_status()
    d = r.json()["daily"]
    days = []
    for i, day in enumerate(d["time"]):
        days.append({
            "date": day, "rain_mm": d["precipitation_sum"][i] or 0, "rain_prob": d["precipitation_probability_max"][i] or 0,
            "et0": d["et0_fao_evapotranspiration"][i] or 4.5, "tmax": d["temperature_2m_max"][i], "tmin": d["temperature_2m_min"][i],
            "humidity": (d.get("relative_humidity_2m_mean") or [None] * 7)[i], "wind": d["wind_speed_10m_max"][i], "solar": d["shortwave_radiation_sum"][i],
        })
    return days


def latest(farm):
    return WeatherSnapshot.objects.filter(farm=farm).first()


def refresh(farm, force=False):
    """Return the freshest snapshot we can get. Never raises: falls back to the last one (which will read as stale)."""
    snap = latest(farm)
    if farm.is_demo:
        today = timezone.localdate().isoformat()
        want = demo_days(farm.scenario)
        if snap is None or force or not snap.is_demo or snap.days[0]["date"] != today or snap.days != want:
            snap = WeatherSnapshot.objects.create(farm=farm, source="demo", is_demo=True, days=want)
        return snap
    if snap and not force and timezone.now() - snap.fetched_at < timedelta(minutes=CACHE_MINUTES):
        return snap
    try:
        days = _fetch_open_meteo(farm.latitude, farm.longitude)
        return WeatherSnapshot.objects.create(farm=farm, source="open-meteo", days=days)
    except Exception as exc:  # network down, API change: keep serving the last known forecast
        log.warning("weather fetch failed for farm %s: %s", farm.pk, exc)
        return snap


def age_hours(snap):
    return None if snap is None else (timezone.now() - snap.fetched_at).total_seconds() / 3600
