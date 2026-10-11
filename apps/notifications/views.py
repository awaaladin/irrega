import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .models import Notification, OutboundMessage
from .services import morning_digest, prefs_for, scan_alerts


@login_required
def center(request):
    scan_alerts(request.user)
    items = list(Notification.objects.filter(user=request.user)[:60])
    unread = sum(1 for n in items if not n.read)
    resp = render(request, "notifications/center.html", {"active": "Alerts", "items": items, "unread": unread})
    return resp


@login_required
@require_POST
def mark_read(request):
    Notification.objects.filter(user=request.user, read=False).update(read=True)
    return redirect("notifications:center")


@login_required
@require_POST
def send_digest(request):
    lines = morning_digest(request.user)
    messages.success(request, "Morning plan sent to your alerts." if lines else "Add a field first, then we can write your morning plan.")
    return redirect("notifications:center")


@login_required
def settings_view(request):
    prefs = prefs_for(request.user)
    if request.method == "POST":
        prefs.in_app = "in_app" in request.POST
        prefs.sms = "sms" in request.POST
        prefs.whatsapp = "whatsapp" in request.POST
        try:
            prefs.quiet_start = datetime.time.fromisoformat(request.POST.get("quiet_start") or "21:00")
            prefs.quiet_end = datetime.time.fromisoformat(request.POST.get("quiet_end") or "05:30")
        except ValueError:
            messages.error(request, "Enter quiet hours as times, like 21:00.")
            return redirect("notifications:settings")
        prefs.save()
        messages.success(request, "Alert settings saved.")
        return redirect("notifications:settings")
    channels = [
        ("in_app", "In the app", prefs.in_app, "The alert list and the bell."),
        ("sms", "SMS", prefs.sms, "A short text message. Demo mode logs it instead."),
        ("whatsapp", "WhatsApp", prefs.whatsapp, "A WhatsApp message. Demo mode logs it instead."),
    ]
    return render(request, "notifications/settings.html", {"active": "Alerts", "prefs": prefs, "channels": channels})


@login_required
def sent(request):
    return render(request, "notifications/sent.html", {"active": "Alerts", "items": OutboundMessage.objects.filter(user=request.user)[:50]})
