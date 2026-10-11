from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models


class Role(models.TextChoices):
    FARMER = "farmer", "Farmer"
    PARTNER = "partner", "Partner"
    ADMIN = "admin", "Admin"


class User(AbstractUser):
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.FARMER)
    language = models.CharField(max_length=5, default="en", choices=[("en", "English"), ("pcm", "Pidgin")])
    organization = models.ForeignKey("partners.Organization", null=True, blank=True, on_delete=models.SET_NULL, related_name="members")
    objects = UserManager()

    @property
    def is_partner(self):
        return self.role in (Role.PARTNER, Role.ADMIN)

    @property
    def display_name(self):
        return self.first_name or self.email or self.phone or self.username


def _new_key():
    import secrets

    return "rit_" + secrets.token_urlsafe(32)


class ApiKey(models.Model):
    """Bearer key for POST /api/readings/ (a future soil sensor or gateway)."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="api_keys")
    label = models.CharField(max_length=60, default="Sensor")
    key = models.CharField(max_length=80, unique=True, default=_new_key)
    created = models.DateTimeField(auto_now_add=True)
