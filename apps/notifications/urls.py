from django.urls import path

from . import views

app_name = "notifications"
urlpatterns = [
    path("", views.center, name="center"),
    path("read/", views.mark_read, name="read"),
    path("digest/", views.send_digest, name="digest"),
    path("settings/", views.settings_view, name="settings"),
    path("sent/", views.sent, name="sent"),
]
