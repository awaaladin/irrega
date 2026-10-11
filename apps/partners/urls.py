from django.urls import path

from . import views

app_name = "partners"
urlpatterns = [
    path("partners/", views.dashboard, name="dashboard"),
    path("feedback/", views.feedback, name="feedback"),
    path("pilot/", views.pilot_results, name="pilot"),
    path("system/", views.system, name="system"),
]
