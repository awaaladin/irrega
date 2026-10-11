from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from apps.farms.models import Farm

from . import services

BACKEND = "apps.accounts.backends.EmailOrPhoneBackend"


def enter(request, who="farmer"):
    if not settings.DEMO_MODE:
        raise Http404
    farmer, partner, admin = services.ensure_demo()
    user = {"farmer": farmer, "partner": partner, "admin": admin}.get(who, farmer)
    login(request, user, backend=BACKEND)
    nxt = request.GET.get("next", "")
    if nxt.startswith("/") and not nxt.startswith("//"):
        return redirect(nxt)
    return redirect("/partners/" if who == "partner" else "/system/" if who == "admin" else "/")


@login_required
@require_POST
def scenario(request):
    if not settings.DEMO_MODE:
        raise Http404
    which = request.POST.get("scenario")
    farm = Farm.objects.filter(owner=request.user, is_demo=True).first()
    if which not in ("normal", "rainy", "dry") or not farm:
        return JsonResponse({"error": "Unknown scenario."}, status=400)
    services.apply_scenario(farm, which)
    return redirect(request.META.get("HTTP_REFERER") or "/")


@login_required
@require_POST
def sensor(request):
    if not settings.DEMO_MODE:
        raise Http404
    farm = Farm.objects.filter(owner=request.user, is_demo=True).first()
    if farm:
        services.simulate_sensor(farm)
    return redirect(request.META.get("HTTP_REFERER") or "/")


@login_required
@require_POST
def reset(request):
    if not settings.DEMO_MODE:
        raise Http404
    services.seed_farm(request.user)
    return redirect("/")
