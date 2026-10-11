"""Plans are data (see ensure_plans). Payments go through a PaymentAdapter; only a mock in test mode ships here."""
import uuid
from datetime import timedelta

from django.utils import timezone

from .models import Invoice, Plan, Subscription

DEFAULT_PLANS = [
    dict(code="starter", name="Starter", price_ngn=2500, max_fields=2, max_hectares=1.0, sort=1,
         blurb="One small garden or two plots.", features=["Daily watering advice", "Why-this explanations", "Ask questions", "In-app alerts"]),
    dict(code="farm", name="Farm", price_ngn=7500, max_fields=8, max_hectares=10.0, sort=2,
         blurb="A working farm with several fields.", features=["Everything in Starter", "Crop-stress (NDVI) tracking", "SMS and WhatsApp morning digest", "Pidgin explanations", "Yield history"]),
    dict(code="partner", name="Partner", price_ngn=45000, max_fields=200, max_hectares=500.0, sort=3,
         blurb="For agricultural organisations and irrigation providers.", features=["Everything in Farm", "Partner dashboard", "Pilot codes and results", "Data-quality flags", "Priority support"]),
]


def ensure_plans(**kwargs):
    for p in DEFAULT_PLANS:
        Plan.objects.get_or_create(code=p["code"], defaults=p)


class PaymentAdapter:
    def charge(self, user, plan):  # -> (ok, reference)
        raise NotImplementedError


class MockPaystack(PaymentAdapter):
    """Test mode only. No money moves and no card details are collected."""

    def charge(self, user, plan):
        return True, f"TEST-{uuid.uuid4().hex[:12].upper()}"


def start_trial(user, days=30, plan_code="farm"):
    plan = Plan.objects.filter(code=plan_code).first() or Plan.objects.first()
    if plan is None:
        ensure_plans()
        plan = Plan.objects.get(code=plan_code)
    sub, _ = Subscription.objects.get_or_create(
        user=user, defaults=dict(plan=plan, status="trial", trial_ends=timezone.localdate() + timedelta(days=days))
    )
    return sub


def trial_days_left(sub):
    if sub is None or sub.status != "trial" or not sub.trial_ends:
        return None
    return max((sub.trial_ends - timezone.localdate()).days, 0)


def change_plan(user, plan, adapter=None):
    ok, ref = (adapter or MockPaystack()).charge(user, plan)
    if not ok:
        return None
    sub = start_trial(user)
    sub.plan, sub.status, sub.trial_ends = plan, "active", None
    sub.save()
    return Invoice.objects.create(user=user, plan=plan, amount_ngn=plan.price_ngn, reference=ref)


def within_plan(user):
    """Return (ok, message) for adding another field."""
    from apps.farms.models import Field

    sub = getattr(user, "subscription", None)
    if sub is None:
        return True, ""
    n = Field.objects.filter(farm__owner=user).count()
    if n >= sub.plan.max_fields:
        return False, f"Your {sub.plan.name} plan covers {sub.plan.max_fields} fields. Choose a bigger plan to add more."
    return True, ""
