from django.urls import path

from . import views

app_name = "marketplace"

urlpatterns = [
    path("", views.crop_list, name="crop_list"),
    path("add/", views.create_listing, name="create_listing"),
]
