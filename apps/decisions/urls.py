from django.urls import path

from . import views

app_name = "decisions"
urlpatterns = [
    path("api/decisions/", views.api_decide, name="decide"),
    path("insights/", views.insights, name="insights"),
]
