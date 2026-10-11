from django.urls import path

from . import views

app_name = "farms"
urlpatterns = [
    path("", views.field_list, name="list"),
    path("onboarding/", views.onboarding, name="onboarding"),
    path("<int:farm_id>/fields/new/", views.field_new, name="field_new"),
    path("fields/<int:pk>/", views.field_detail, name="field_detail"),
    path("fields/<int:pk>/edit/", views.field_edit, name="field_edit"),
    path("fields/<int:pk>/delete/", views.field_delete, name="field_delete"),
    path("fields/<int:pk>/yield/", views.yield_add, name="yield_add"),
    path("fields/<int:pk>/csv/", views.csv_import, name="csv_import"),
]
