from django.conf import settings
from django.db import models
from django.utils import timezone

SOILS = {
    # field capacity %, wilting point %, saturation % (volumetric water content)
    "sandy": {"label": "Sandy", "fc": 15, "wp": 6, "sat": 22},
    "loam": {"label": "Loam", "fc": 30, "wp": 12, "sat": 38},
    "clay": {"label": "Clay", "fc": 38, "wp": 20, "sat": 46},
    "laterite": {"label": "Laterite (red clay soil)", "fc": 24, "wp": 10, "sat": 32},
}
# application efficiency: share of applied water that reaches the root zone
METHODS = {
    "drip": {"label": "Drip", "eff": 0.90},
    "sprinkler": {"label": "Sprinkler", "eff": 0.75},
    "manual": {"label": "Watering can / hose", "eff": 0.70},
    "flood": {"label": "Flood", "eff": 0.60},
}
WATERING_CAN_LITRES = 15


class Crop(models.Model):
    """FAO-56 style crop. stages = [[name, days, kc], ...] in order initial, development, mid, late."""

    key = models.SlugField(unique=True)
    name = models.CharField(max_length=60)
    stages = models.JSONField()
    root_depth_mm = models.PositiveIntegerField(default=500)
    depletion_fraction = models.FloatField(default=0.5, help_text="p: share of available water the crop can use before stress")
    sensitive_stage = models.CharField(max_length=20, default="mid")
    glyph = models.CharField(max_length=20, default="leaf")

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def season_days(self):
        return sum(s[1] for s in self.stages)


class Farm(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="farms")
    organization = models.ForeignKey("partners.Organization", null=True, blank=True, on_delete=models.SET_NULL, related_name="farms")
    name = models.CharField(max_length=80)
    latitude = models.FloatField(default=4.9517)  # Calabar South
    longitude = models.FloatField(default=8.3220)
    is_demo = models.BooleanField(default=False)
    scenario = models.CharField(max_length=10, default="normal", choices=[("normal", "Normal"), ("rainy", "Rainy day"), ("dry", "Dry spell")])
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Field(models.Model):
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name="fields")
    name = models.CharField(max_length=80)
    area_ha = models.FloatField(default=0.25)
    crop = models.ForeignKey(Crop, on_delete=models.PROTECT)
    soil = models.CharField(max_length=10, choices=[(k, v["label"]) for k, v in SOILS.items()], default="loam")
    planting_date = models.DateField()
    method = models.CharField(max_length=10, choices=[(k, v["label"]) for k, v in METHODS.items()], default="manual")
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    polygon = models.JSONField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.crop.name})"

    @property
    def lat(self):
        return self.latitude if self.latitude is not None else self.farm.latitude

    @property
    def lon(self):
        return self.longitude if self.longitude is not None else self.farm.longitude

    @property
    def area_m2(self):
        return self.area_ha * 10000


class MoistureReading(models.Model):
    SOURCES = [("manual", "Manual"), ("csv", "CSV import"), ("sensor", "Sensor"), ("simulated", "Simulated")]
    field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name="readings")
    value = models.FloatField(help_text="Volumetric soil moisture, %")
    taken_at = models.DateTimeField(default=timezone.now)
    source = models.CharField(max_length=10, choices=SOURCES, default="manual")

    class Meta:
        ordering = ["-taken_at"]
        indexes = [models.Index(fields=["field", "-taken_at"])]

    @property
    def is_simulated(self):
        return self.source == "simulated"


class YieldRecord(models.Model):
    field = models.ForeignKey(Field, on_delete=models.CASCADE, related_name="yields")
    season = models.CharField(max_length=20)
    amount_kg = models.FloatField()
    dry_spell = models.BooleanField(default=False, help_text="A long dry spell hurt this season")
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-id"]
