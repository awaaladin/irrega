"""Notifications: in-app is real; SMS / WhatsApp adapters only log to the 'Sent messages' screen in this build."""
from django.utils import timezone

from .models import Notification, NotificationPrefs, OutboundMessage


class ChannelAdapter:
    channel = ""

    def send(self, user, body):
        raise NotImplementedError


class LoggingAdapter(ChannelAdapter):
    """Termii-style interface; swap in a real HTTP client later. Demo mode logs instead of sending."""

    def __init__(self, channel):
        self.channel = channel

    def send(self, user, body):
        OutboundMessage.objects.create(user=user, channel=self.channel, to=user.phone or user.email or "", body=body)


def prefs_for(user):
    return NotificationPrefs.objects.get_or_create(user=user)[0]


def in_quiet_hours(prefs, now=None):
    t = (now or timezone.localtime()).time()
    s, e = prefs.quiet_start, prefs.quiet_end
    return (s <= t or t < e) if s > e else (s <= t < e)


def notify(user, kind, title, body="", urgent=False, now=None):
    prefs = prefs_for(user)
    quiet = in_quiet_hours(prefs, now) and not urgent
    if prefs.in_app:
        Notification.objects.create(user=user, kind=kind, title=title, body=body)
    if not quiet:
        for ch, on in (("sms", prefs.sms), ("whatsapp", prefs.whatsapp)):
            if on:
                LoggingAdapter(ch).send(user, f"{title}. {body}".strip())


def morning_digest(user):
    from apps.engine import explain
    from apps.engine.services import get_recommendation
    from apps.farms.models import Field

    lines = []
    for f in Field.objects.filter(farm__owner=user).select_related("crop", "farm"):
        r = get_recommendation(f).payload
        if r["action"].startswith("IRRIGATE"):
            lines.append(f"{f.name}: water {r['window'] or 'today'}, {r['depth_mm']} mm.")
        elif r["action"] == "WATCH":
            lines.append(f"{f.name}: watch closely, do not add water yet.")
        else:
            why = "rain likely" if any(x["code"] in ("RAIN_COVERS", "HEAVY_RAIN_SKIP") for x in r["reasons"]) else "soil has enough"
            lines.append(f"{f.name}: skip, {why}.")
    if lines:
        notify(user, "digest", "Morning plan", " ".join(lines))
    return lines


def scan_alerts(user):
    """Alerts on stress spikes, stale data and heavy rain. De-duplicated per day."""
    from apps.decisions.models import Recommendation

    today = timezone.localdate()
    seen = set(Notification.objects.filter(user=user, created__date=today).values_list("title", flat=True))
    for r in Recommendation.objects.filter(field__farm__owner=user, date=today).select_related("field"):
        p = r.payload
        codes = {x["code"] for x in p["reasons"]}
        alerts = []
        if "NDVI_FALL_DRY" in codes or "NDVI_FALL_WET" in codes:
            alerts.append(("stress", f"Crop stress on {r.field.name}", "Satellite greenness is falling. Open the field to see why."))
        if "STALE_WEATHER" in codes or "STALE_MOISTURE" in codes:
            alerts.append(("stale", f"Out-of-date data on {r.field.name}", "Add a fresh soil reading or refresh the forecast."))
        if p["balance"]["rain_today_mm"] + p["balance"]["rain_tomorrow_mm"] >= 15:
            alerts.append(("rain", f"Heavy rain expected near {r.field.name}", "Skip watering and check drainage."))
        for kind, title, body in alerts:
            if title not in seen:
                notify(user, kind, title, body, urgent=(kind == "stress"))
                seen.add(title)
