from django.contrib import admin
from django.urls import include, path

from apps.farms import views as farm_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", farm_views.home, name="today"),
    path("about/", farm_views.landing, name="about"),
    path("guide/", farm_views.guide, name="guide"),
    path("", include("apps.core.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("farms/", include("apps.farms.urls")),
    path("", include("apps.decisions.urls")),
    path("", include("apps.assistant.urls")),
    path("notifications/", include("apps.notifications.urls")),
    path("billing/", include("apps.billing.urls")),
    path("", include("apps.partners.urls")),
    path("demo/", include("apps.demo.urls")),
    path("api/readings/", farm_views.api_readings, name="api_readings"),
    path("api/fields/<int:pk>/moisture/", farm_views.api_moisture, name="api_moisture"),
]
