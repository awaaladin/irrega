from django.db import models


class WeatherSnapshot(models.Model):
    farm = models.ForeignKey("farms.Farm", on_delete=models.CASCADE, related_name="weather")
    fetched_at = models.DateTimeField(auto_now_add=True)
    source = models.CharField(max_length=30)  # open-meteo | demo
    is_demo = models.BooleanField(default=False)
    days = models.JSONField()  # [{date, rain_mm, rain_prob, et0, tmax, tmin, humidity, wind, solar}]

    class Meta:
        ordering = ["-fetched_at"]


class NdviReading(models.Model):
    field = models.ForeignKey("farms.Field", on_delete=models.CASCADE, related_name="ndvi")
    date = models.DateField()
    ndvi = models.FloatField()
    source = models.CharField(max_length=30)
    is_simulated = models.BooleanField(default=False)

    class Meta:
        ordering = ["date"]
        unique_together = [("field", "date")]
