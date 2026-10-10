from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("register/", views.register, name="register"),
    path("api/climate/weather", views.climate_weather, name="climate_weather"),
    path("api/climate/rating", views.climate_rating, name="climate_rating"),
    path("dashboard/", views.dashboard, name="dashboard"),
]
