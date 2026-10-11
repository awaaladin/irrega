from django.conf import settings
from django.db import models


class Plan(models.Model):
    code = models.SlugField(unique=True)
    name = models.CharField(max_length=40)
    price_ngn = models.PositiveIntegerField(help_text="Per month, Naira")
    max_fields = models.PositiveIntegerField()
    max_hectares = models.FloatField()
    blurb = models.CharField(max_length=160, blank=True)
    features = models.JSONField(default=list)
    sort = models.PositiveSmallIntegerField(default=0)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["sort"]

    def __str__(self):
        return self.name


class Subscription(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="subscription")
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    status = models.CharField(max_length=10, default="trial")  # trial | active | cancelled
    trial_ends = models.DateField(null=True, blank=True)
    started = models.DateTimeField(auto_now_add=True)


class Invoice(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="invoices")
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    amount_ngn = models.PositiveIntegerField()
    reference = models.CharField(max_length=40, unique=True)
    status = models.CharField(max_length=12, default="paid (test)")
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]
