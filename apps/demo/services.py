"""Demo mode. Everything created here is flagged is_demo / source='simulated' and labelled 'Demo data' in the UI."""
import random
from datetime import datetime, time, timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone

from apps.billing.services import start_trial
from apps.decisions.models import Decision, Recommendation
from apps.engine.core import DayWeather, EngineInput, recommend
from apps.engine.services import get_recommendation
from apps.farms.crops import growth_stage
from apps.farms.models import METHODS, SOILS, Crop, Farm, Field, MoistureReading, YieldRecord
from apps.notifications.models import Notification
from apps.partners.models import Organization, PilotCode
from apps.providers import satellite, weather
from apps.providers.models import NdviReading, WeatherSnapshot

User = get_user_model()
DEMO_EMAIL = "demo@irrigation.test"
PARTNER_EMAIL = "partner@irrigation.test"
ADMIN_EMAIL = "admin@irrigation.test"
DEMO_PASSWORD = "demo-pass-123"

FIELDS = [
    # name, crop, soil, area_ha, method, days since planting
    ("Cassava, lower plot", "cassava", "laterite", 0.15, "manual", 135),
    ("Tomato bed", "tomato", "loam", 0.04, "drip", 58),
    ("Maize, hill side", "maize", "sandy", 0.10, "manual", 62),
]

# Depletion as a share of the trigger (1.0 = right at the water-now line), by scenario. None = waterlogged.
SCENARIO_MOISTURE = {
    "normal": {"cassava": 0.50, "tomato": 0.92, "maize": 0.45},
    "rainy": {"cassava": 0.15, "tomato": None, "maize": 0.10},
    "dry": {"cassava": 0.95, "tomato": 1.20, "maize": 1.30},
}
SCENARIO_NDVI_DROP = {
    "normal": {},
    "rainy": {"tomato": 0.14},  # falling greenness with wet soil: not a water problem
    "dry": {"maize": 0.13, "tomato": 0.09},
}


def _users():
    org, _ = Organization.objects.get_or_create(name="Cross River Farmers Cooperative", defaults={"kind": "Agricultural organisation"})
    def secure(user):
        # A known password on a public URL would be an open door. Locally you can sign in with it; anywhere else the
        # demo accounts are reachable only through the one-click demo entry.
        if settings.DEBUG:
            user.set_password(DEMO_PASSWORD)
        else:
            user.set_unusable_password()
        user.save()

    farmer, c = User.objects.get_or_create(username=DEMO_EMAIL, defaults=dict(email=DEMO_EMAIL, first_name="Etim", organization=org))
    if c:
        secure(farmer)
        start_trial(farmer, days=45)
    partner, c = User.objects.get_or_create(username=PARTNER_EMAIL, defaults=dict(email=PARTNER_EMAIL, first_name="Ima", role="partner", organization=org))
    if c:
        secure(partner)
        start_trial(partner, days=45, plan_code="partner")
    # The demo "admin" is only for local development: never staff or superuser, so it cannot reach Django admin.
    admin, c = User.objects.get_or_create(username=ADMIN_EMAIL, defaults=dict(email=ADMIN_EMAIL, first_name="Admin", role="admin",
                                                                              is_staff=settings.DEBUG, is_superuser=settings.DEBUG))
    if c:
        secure(admin)
    PilotCode.objects.get_or_create(code="CALABAR2026", defaults=dict(organization=org, trial_days=60))
    return farmer, partner, admin, org


def _history_weather(rng, days):
    """Synthetic rainy-season weather: (rain_mm, et0, tmax)."""
    out = []
    for _ in range(days):
        rainy = rng.random() < 0.42
        out.append((round(rng.uniform(4, 38), 1) if rainy else 0.0, round(rng.uniform(3.2, 5.4), 1), round(rng.uniform(27, 34))))
    return out


def _trigger_pct(field, stage_sensitive):
    soil = SOILS[field.soil]
    return soil["fc"] - field.crop.depletion_fraction * (soil["fc"] - soil["wp"]) * (0.9 if stage_sensitive else 1.0)


@transaction.atomic
def seed_farm(owner):
    Farm.objects.filter(owner=owner, is_demo=True).delete()
    rng = random.Random(42)
    today = timezone.localdate()
    farm = Farm.objects.create(owner=owner, organization=owner.organization, name="Etim's farm (Demo), Calabar South", latitude=4.9517, longitude=8.3220, is_demo=True)
    hist = _history_weather(rng, 92)
    for name, crop_key, soil, area, method, age in FIELDS:
        crop = Crop.objects.get(key=crop_key)
        f = Field.objects.create(farm=farm, name=name, crop=crop, soil=soil, area_ha=area, method=method, planting_date=today - timedelta(days=age),
                                 latitude=farm.latitude + rng.uniform(-0.0008, 0.0008), longitude=farm.longitude + rng.uniform(-0.0008, 0.0008))
        s = SOILS[soil]
        # earlier seasons for yield history; maize lost yield to a dry spell
        base = {"cassava": 2800, "tomato": 950, "maize": 1500}[crop_key]
        YieldRecord.objects.create(field=f, season="2024 rainy season", amount_kg=base, dry_spell=False)
        YieldRecord.objects.create(field=f, season="2025 rainy season", amount_kg=base * (0.7 if crop_key == "maize" else 1.04), dry_spell=crop_key == "maize")

        theta = s["fc"] - 0.4 * (s["fc"] - s["wp"])
        root = crop.root_depth_mm
        for i in range(90, 0, -1):
            d = today - timedelta(days=i)
            rain, et0, tmax = hist[90 - i]
            _, kc, *_ = growth_stage(crop.stages, (d - f.planting_date).days)
            stage = growth_stage(crop.stages, (d - f.planting_date).days)
            if (d - f.planting_date).days < 0:
                continue
            theta += rain * 0.7 / root * 100 - et0 * kc / root * 100
            theta = max(s["wp"] + 1, min(theta, s["sat"] + 1))
            fc_prob = [DayWeather(d, rain, 40 if rain else 15, et0, tmax, 23), DayWeather(d + timedelta(1), hist[min(91 - i, 91)][0], 35, et0, tmax, 23)]
            ndvi_series = []
            when = timezone.make_aware(datetime.combine(d, time(6, 30)))
            if rng.random() < 0.85:
                MoistureReading.objects.create(field=f, value=round(theta + rng.uniform(-0.6, 0.6), 1), taken_at=when, source="simulated")
            # NDVI every day, from the labelled simulated provider
            NdviReading.objects.update_or_create(field=f, date=d, defaults=dict(ndvi=satellite.SimulatedProvider().ndvi(f, d), source="simulated", is_simulated=True))
            if i <= 30:
                ndvi = [(r.date, r.ndvi) for r in NdviReading.objects.filter(field=f, date__lte=d).order_by("date")[:60]][-6:]
                out = recommend(EngineInput(
                    today=d, planting_date=f.planting_date, stages=crop.stages, root_depth_mm=root, p=crop.depletion_fraction, sensitive_stage=crop.sensitive_stage,
                    soil=s, area_m2=f.area_m2, efficiency=METHODS[method]["eff"], method=method, moisture=theta, moisture_age_h=2, moisture_simulated=True,
                    forecast=fc_prob, weather_age_h=1, weather_demo=True, ndvi=ndvi, ndvi_simulated=True, hour=6))
                out["field"] = {"id": f.pk, "name": f.name, "crop": crop.name}
                rec = Recommendation.objects.create(field=f, date=d, action=out["action"], volume_l=out["volume_l"], depth_mm=out["depth_mm"],
                                                    confidence=out["confidence"], payload=out, is_demo=True)
                Recommendation.objects.filter(pk=rec.pk).update(created=when)
                roll = rng.random()
                if out["action"].startswith("IRRIGATE"):
                    if roll < 0.78:
                        dec = Decision(recommendation=rec, user=owner, kind="accept", litres=out["volume_l"])
                        theta = min(s["fc"], theta + out["depth_mm"] * 0.9 / root * 100)
                    else:
                        dec = Decision(recommendation=rec, user=owner, kind="override", farmer_action="SKIP", reason=rng.choice(["rain_started", "no_water", "already_watered"]))
                else:
                    if roll < 0.2:
                        dec = Decision(recommendation=rec, user=owner, kind="override", farmer_action="IRRIGATE", litres=round(out["balance"]["taw_mm"] * 0.1 * f.area_m2 / METHODS[method]["eff"]),
                                       reason=rng.choice(["crop_looks_thirsty", "know_my_soil"]))
                        theta = min(s["fc"], theta + 3)
                    elif roll < 0.85:
                        dec = Decision(recommendation=rec, user=owner, kind="accept")
                    else:
                        dec = None
                if dec:
                    dec.save()
                    Decision.objects.filter(pk=dec.pk).update(created=when + timedelta(minutes=rng.randint(10, 180)))
    apply_scenario(farm, "normal")
    Notification.objects.create(user=owner, kind="digest", title="Welcome to the demo", body="Everything on this farm is demo data. Try the Rainy day and Dry spell switches in the demo bar.")
    return farm


def apply_scenario(farm, scenario):
    """Switch the live scenario: new forecast, fresh simulated sensor readings and NDVI trend. Frozen (decided) recommendations are kept."""
    farm.scenario = scenario
    farm.save(update_fields=["scenario"])
    today = timezone.localdate()
    now = timezone.now()
    weather.refresh(farm, force=True)
    for f in farm.fields.select_related("crop"):
        s = SOILS[f.soil]
        stage = growth_stage(f.crop.stages, (today - f.planting_date).days)
        sensitive = stage[0] == f.crop.sensitive_stage
        factor = SCENARIO_MOISTURE[scenario].get(f.crop.key, 0.5)
        if factor is None:
            theta = s["sat"] + 1.5
        else:
            trig_depl = f.crop.depletion_fraction * (s["fc"] - s["wp"]) * (0.9 if sensitive else 1.0)
            theta = max(s["wp"] + 0.5, s["fc"] - factor * trig_depl)
        MoistureReading.objects.filter(field=f, source="simulated", taken_at__gte=now - timedelta(hours=1)).delete()
        MoistureReading.objects.create(field=f, value=round(theta, 1), taken_at=now, source="simulated")
        drop = SCENARIO_NDVI_DROP[scenario].get(f.crop.key, 0)
        base = satellite.SimulatedProvider().ndvi(f, today - timedelta(days=8))
        for k in range(7, -1, -1):
            d = today - timedelta(days=k)
            frac = (7 - k) / 7
            v = satellite.SimulatedProvider().ndvi(f, d) if not drop else round(base - drop * frac, 3)
            NdviReading.objects.update_or_create(field=f, date=d, defaults=dict(ndvi=v, source="simulated", is_simulated=True))
        Recommendation.objects.filter(field=f, date=today, decisions__isnull=True).delete()
        get_recommendation(f, refresh=True)


def simulate_sensor(farm):
    """Labelled simulated sensor stream: moisture drifts down with crop demand, up with rain."""
    snap = weather.latest(farm)
    rain = (snap.days[0]["rain_mm"] * snap.days[0]["rain_prob"] / 100) if snap else 0
    for f in farm.fields.select_related("crop"):
        last = f.readings.first()
        s = SOILS[f.soil]
        cur = last.value if last else s["fc"] - 3
        cur += rain * 0.25 - 0.6
        cur = max(s["wp"] + 0.5, min(cur, s["sat"] + 2))
        MoistureReading.objects.create(field=f, value=round(cur, 1), taken_at=timezone.now(), source="simulated")
        Recommendation.objects.filter(field=f, date=timezone.localdate(), decisions__isnull=True).delete()
        get_recommendation(f, refresh=True)


def ensure_demo():
    farmer, partner, admin, org = _users()
    if not Farm.objects.filter(owner=farmer, is_demo=True).exists():
        seed_farm(farmer)
    return farmer, partner, admin
