import datetime

from django.conf import settings
from django.db import models


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    kind = models.CharField(max_length=20, default="info")  # digest | stress | stale | rain | info
    title = models.CharField(max_length=120)
    body = models.TextField(blank=True)
    read = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]


class OutboundMessage(models.Model):
    """Demo-mode log of SMS / WhatsApp messages that would have been sent."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    channel = models.CharField(max_length=10)
    to = models.CharField(max_length=40, blank=True)
    body = models.TextField()
    status = models.CharField(max_length=20, default="logged (demo)")
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]


class NotificationPrefs(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_prefs")
    in_app = models.BooleanField(default=True)
    sms = models.BooleanField(default=False)
    whatsapp = models.BooleanField(default=False)
    quiet_start = models.TimeField(default=datetime.time(21, 0))
    quiet_end = models.TimeField(default=datetime.time(5, 30))
