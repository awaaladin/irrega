"""Crop-stress (NDVI). SatelliteProvider interface, a real Sentinel Hub provider, and a labelled simulated fallback."""
import logging
import math
import random
from datetime import timedelta

import requests
from django.conf import settings
from django.utils import timezone

from .models import NdviReading

log = logging.getLogger(__name__)


class SatelliteProvider:
    name = "base"
    simulated = False

    def ndvi(self, field, day):  # -> float | None
        raise NotImplementedError


class SimulatedProvider(SatelliteProvider):
    """Plausible seasonal NDVI with gentle noise. Always labelled 'Simulated' in the UI."""

    name = "simulated"
    simulated = True

    def ndvi(self, field, day):
        age = (day - field.planting_date).days
        season = field.crop.season_days
        x = max(0.0, min(age / season, 1.2))
        base = 0.25 + 0.55 * math.sin(math.pi * min(x, 1.0)) ** 0.8
        rng = random.Random(f"{field.pk}-{day.toordinal()}")
        return round(max(0.15, min(0.9, base + rng.uniform(-0.02, 0.02))), 3)


class SentinelHubProvider(SatelliteProvider):
    """Sentinel-2 L2A mean NDVI over a ~100 m box via the Sentinel Hub Statistical API (free trial / quota)."""

    name = "sentinel-2"
    TOKEN_URL = "https://services.sentinel-hub.com/oauth/token"
    STATS_URL = "https://services.sentinel-hub.com/api/v1/statistics"
    EVALSCRIPT = """//VERSION=3
function setup(){return{input:[{bands:["B04","B08","dataMask"]}],output:[{id:"ndvi",bands:1},{id:"dataMask",bands:1}]}}
function evaluatePixel(s){return{ndvi:[(s.B08-s.B04)/(s.B08+s.B04)],dataMask:[s.dataMask]}}"""

    def _token(self):
        r = requests.post(self.TOKEN_URL, data={"grant_type": "client_credentials", "client_id": settings.SENTINELHUB_CLIENT_ID,
                                                 "client_secret": settings.SENTINELHUB_CLIENT_SECRET}, timeout=10)
        r.raise_for_status()
        return r.json()["access_token"]

    def ndvi(self, field, day):
        d = 0.0005
        box = [field.lon - d, field.lat - d, field.lon + d, field.lat + d]
        body = {
            "input": {"bounds": {"bbox": box, "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"}},
                      "data": [{"type": "sentinel-2-l2a", "dataFilter": {"maxCloudCoverage": 40}}]},
            "aggregation": {"timeRange": {"from": f"{(day - timedelta(days=10)).isoformat()}T00:00:00Z", "to": f"{day.isoformat()}T23:59:59Z"},
                            "aggregationInterval": {"of": "P10D"}, "evalscript": self.EVALSCRIPT, "resx": 0.0001, "resy": 0.0001},
        }
        r = requests.post(self.STATS_URL, json=body, headers={"Authorization": f"Bearer {self._token()}"}, timeout=15)
        r.raise_for_status()
        data = r.json()["data"]
        if not data:
            return None
        return round(data[-1]["outputs"]["ndvi"]["bands"]["B0"]["stats"]["mean"], 3)


def get_provider():
    if settings.SATELLITE_PROVIDER == "sentinelhub" and settings.SENTINELHUB_CLIENT_ID:
        return SentinelHubProvider()
    return SimulatedProvider()


def ensure_today(field):
    """Cache one reading per field per day. Real provider first; on any failure fall back to the labelled simulation."""
    today = timezone.localdate()
    if NdviReading.objects.filter(field=field, date=today).exists():
        return
    if field.farm.is_demo:
        provider = SimulatedProvider()
        value = provider.ndvi(field, today)
    else:
        provider = get_provider()
        try:
            value = provider.ndvi(field, today)
        except Exception as exc:
            log.warning("satellite provider %s failed: %s", provider.name, exc)
            provider = SimulatedProvider()
            value = provider.ndvi(field, today)
        if value is None:
            provider = SimulatedProvider()
            value = provider.ndvi(field, today)
    NdviReading.objects.update_or_create(field=field, date=today, defaults=dict(ndvi=value, source=provider.name, is_simulated=provider.simulated))


def series(field, days=60):
    since = timezone.localdate() - timedelta(days=days)
    return list(NdviReading.objects.filter(field=field, date__gte=since).order_by("date"))
