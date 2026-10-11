from django.conf import settings
from django.db import models


class Recommendation(models.Model):
    field = models.ForeignKey("farms.Field", on_delete=models.CASCADE, related_name="recommendations")
    date = models.DateField()
    action = models.CharField(max_length=24)
    volume_l = models.FloatField(default=0)
    depth_mm = models.FloatField(default=0)
    confidence = models.CharField(max_length=6)
    payload = models.JSONField()  # full engine output + signals snapshot
    is_demo = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-id"]
        unique_together = [("field", "date")]


class Decision(models.Model):
    """Immutable log of what the farmer did with a recommendation."""

    KINDS = [("accept", "Accepted"), ("override", "Overrode"), ("snooze", "Snoozed")]
    recommendation = models.ForeignKey(Recommendation, on_delete=models.CASCADE, related_name="decisions")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    kind = models.CharField(max_length=10, choices=KINDS)
    farmer_action = models.CharField(max_length=24, blank=True)  # IRRIGATE / SKIP / LATER
    litres = models.FloatField(null=True, blank=True)
    reason = models.CharField(max_length=40, blank=True)
    note = models.CharField(max_length=300, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]

    def save(self, *args, **kwargs):
        if self.pk:
            raise PermissionError("Decision history is immutable.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionError("Decision history is immutable.")
