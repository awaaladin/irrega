from django.urls import path

from . import views

app_name = "demo"
urlpatterns = [
    path("enter/", views.enter, name="enter"),
    path("enter/<str:who>/", views.enter, name="enter_as"),
    path("scenario/", views.scenario, name="scenario"),
    path("sensor/", views.sensor, name="sensor"),
    path("reset/", views.reset, name="reset"),
]
