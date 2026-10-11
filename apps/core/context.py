from django.conf import settings


def shell(request):
    ctx = {"DEMO_MODE": settings.DEMO_MODE}
    u = getattr(request, "user", None)
    if u is not None and u.is_authenticated:
        from apps.billing.services import trial_days_left
        from apps.farms.models import Farm

        farms = list(Farm.objects.filter(owner=u).only("id", "name", "is_demo", "scenario"))
        ctx.update(
            unread_count=u.notifications.filter(read=False).count(),
            trial_days=trial_days_left(getattr(u, "subscription", None)),
            has_demo_farm=any(f.is_demo for f in farms),
            demo_farm=next((f for f in farms if f.is_demo), None),
            lang=u.language,
            demo_scenarios=[("normal", "Normal day", "cloud-sun"), ("rainy", "Rainy day", "cloud-rain"), ("dry", "Dry spell", "sun")],
            nav_items=[
                {"label": "Today", "href": "/", "icon": "today"},
                {"label": "Fields", "href": "/farms/", "icon": "sprout"},
                {"label": "Insights", "href": "/insights/", "icon": "chart"},
                {"label": "Alerts", "href": "/notifications/", "icon": "bell"},
                {"label": "Account", "href": "/account/", "icon": "user"},
            ],
        )
    return ctx
