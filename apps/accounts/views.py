from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import RegisterForm


def login_view(request):
    error = None
    if request.method == "POST":
        user = authenticate(request, username=request.POST.get("identifier"), password=request.POST.get("password"))
        if user:
            login(request, user)
            return redirect(request.GET.get("next") or "/")
        error = "We could not find an account with those details. Check them and try again."
    return render(request, "registration/login.html", {"error": error})


def register_view(request):
    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        from apps.billing.services import start_trial
        from apps.partners.services import apply_pilot_code

        start_trial(user)
        apply_pilot_code(user, form.cleaned_data.get("pilot_code"))
        login(request, user, backend="apps.accounts.backends.EmailOrPhoneBackend")
        return redirect("farms:onboarding")
    return render(request, "registration/register.html", {"form": form})


@require_POST
def logout_view(request):
    logout(request)
    return redirect("accounts:login")


@require_POST
def set_language(request):
    if request.user.is_authenticated and request.POST.get("lang") in ("en", "pcm"):
        request.user.language = request.POST["lang"]
        request.user.save(update_fields=["language"])
    return redirect(request.META.get("HTTP_REFERER", "/"))
