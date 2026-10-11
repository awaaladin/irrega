from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.farms.models import Field

from .models import Plan
from .services import change_plan, start_trial, trial_days_left


@login_required
def plans(request):
    sub = start_trial(request.user)
    used = Field.objects.filter(farm__owner=request.user).count()
    hectares = round(sum(f.area_ha for f in Field.objects.filter(farm__owner=request.user)), 2)
    return render(request, "billing/plans.html", {
        "active": "Account", "plans": Plan.objects.filter(active=True), "sub": sub, "days_left": trial_days_left(sub),
        "fields_used": used, "hectares": hectares, "invoices": request.user.invoices.select_related("plan")[:20],
    })


@login_required
@require_POST
def subscribe(request):
    plan = get_object_or_404(Plan, code=request.POST.get("plan"), active=True)
    inv = change_plan(request.user, plan)
    if inv:
        messages.success(request, f"You are on the {plan.name} plan. Test mode: no money was taken. Reference {inv.reference}.")
    else:
        messages.error(request, "The payment did not go through. Nothing was charged. Please try again.")
    return redirect("billing:plans")
