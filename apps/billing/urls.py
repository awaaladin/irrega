from django.urls import path

from . import views

app_name = "billing"
urlpatterns = [
    path("", views.plans, name="plans"),
    path("subscribe/", views.subscribe, name="subscribe"),
]
