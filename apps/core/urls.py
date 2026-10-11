from django.urls import path

from . import views

app_name = "core"
urlpatterns = [
    path("manifest.webmanifest", views.manifest, name="manifest"),
    path("sw.js", views.service_worker, name="sw"),
    path("offline/", views.offline, name="offline"),
    path("healthz", views.health, name="health"),
    path("design/", views.design, name="design"),
    path("account/", views.account, name="account"),
    path("account/keys/new/", views.key_create, name="key_create"),
    path("account/keys/<int:pk>/delete/", views.key_delete, name="key_delete"),
]
