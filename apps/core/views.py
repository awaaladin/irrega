import json
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from apps.accounts.models import ApiKey


def manifest(request):
    icons = [
        {"src": "/static/img/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
        {"src": "/static/img/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
        {"src": "/static/img/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        {"src": "/static/img/icon.svg", "sizes": "any", "type": "image/svg+xml", "purpose": "any"},
    ]
    data = {
        "name": "Routine Irrigation Technology", "short_name": "Irrigation", "description": "Clear daily irrigation advice. You stay in control.",
        "start_url": "/", "scope": "/", "display": "standalone", "orientation": "portrait", "background_color": "#0B1A19", "theme_color": "#0B1A19",
        "icons": icons,
        "shortcuts": [{"name": "Today", "url": "/"}, {"name": "Alerts", "url": "/notifications/"}],
    }
    return HttpResponse(json.dumps(data), content_type="application/manifest+json")


def service_worker(request):
    js = (Path(settings.BASE_DIR) / "static" / "js" / "sw.js").read_text(encoding="utf-8")
    resp = HttpResponse(js, content_type="application/javascript")
    resp["Service-Worker-Allowed"] = "/"
    resp["Cache-Control"] = "no-cache"
    return resp


def offline(request):
    return render(request, "offline.html")


def health(request):
    return JsonResponse({"ok": True})


def design(request):
    from datetime import timedelta

    from django.utils import timezone

    swatches = [
        ("bg-base", "bg-base"), ("bg-raised", "bg-raised"), ("bg-sunken", "bg-sunken"), ("border-subtle", "bg-line"),
        ("text-primary", "bg-ink"), ("text-secondary", "bg-mute"), ("accent-water", "bg-water"), ("accent-laterite", "bg-laterite"),
        ("accent-leaf", "bg-leaf"), ("signal-skip", "bg-skip"), ("signal-watch", "bg-watch"), ("signal-stress", "bg-stress"),
    ]
    signals = [
        {"label": "Soil moisture", "display": "19% (measured)", "status": "stress", "share": 0.46, "direction": "irrigate"},
        {"label": "Rain forecast", "display": "3 mm expected", "status": "watch", "share": 0.2, "direction": "skip"},
        {"label": "Crop water use", "display": "5.4 mm/day (mid, Kc 1.20)", "status": "watch", "share": 0.2, "direction": "irrigate"},
        {"label": "Growth stage", "display": "Mid stage", "status": "info", "share": 0.14, "direction": "neutral"},
    ]
    return render(request, "design/gallery.html", {
        "active": "", "swatches": swatches, "signals": signals, "dials": [0, 25, 60, 90],
        "actions": ["IRRIGATE_NOW", "IRRIGATE_LATER_TODAY", "SKIP_TODAY", "WATCH"],
        "now": timezone.now(), "old": timezone.now() - timedelta(hours=9),
        "motion_options": [("system", "Follow my device", "Uses your phone's setting"), ("reduce", "Reduce motion", "Fades instead of movement"), ("full", "Full animation", "Springs and count-ups")],
    })


@login_required
def account(request):
    links = [
        ("/guide/", "Guide: how to use this app", "info"),
        ("/billing/", "Plans and billing", "card"),
        ("/pilot/", "Pilot results", "chart"),
        ("/notifications/settings/", "Alert settings", "bell"),
        ("/notifications/sent/", "Sent messages (SMS and WhatsApp log)", "message"),
        ("/farms/onboarding/", "Add another farm", "map-pin"),
        ("/design/", "Design gallery", "layers"),
    ]
    if request.user.is_partner:
        links.insert(0, ("/partners/", "Partner dashboard", "users"))
    motion_options = [
        ("system", "Follow my device", "Uses your phone's setting"),
        ("reduce", "Reduce motion", "Fades instead of movement"),
        ("full", "Full animation", "Springs and count-ups"),
    ]
    return render(request, "account.html", {"active": "Account", "keys": request.user.api_keys.all(), "links": links, "motion_options": motion_options})


@login_required
@require_POST
def key_create(request):
    ApiKey.objects.create(user=request.user, label=(request.POST.get("label") or "Sensor")[:60])
    messages.success(request, "API key created. Copy it now and keep it private.")
    return redirect("core:account")


@login_required
@require_POST
def key_delete(request, pk):
    request.user.api_keys.filter(pk=pk).delete()
    return redirect("core:account")
