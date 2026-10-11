from django.conf import settings
from django.db import models


class Organization(models.Model):
    name = models.CharField(max_length=120)
    kind = models.CharField(max_length=30, default="Agricultural organization")

    def __str__(self):
        return self.name


class PilotCode(models.Model):
    code = models.CharField(max_length=20, unique=True)
    organization = models.ForeignKey(Organization, null=True, blank=True, on_delete=models.SET_NULL)
    trial_days = models.PositiveIntegerField(default=60)
    max_uses = models.PositiveIntegerField(default=50)
    uses = models.PositiveIntegerField(default=0)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.code


class PilotFeedback(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField()
    text = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)
