from django.urls import path

from . import views

app_name = "resources"

urlpatterns = [
    path("storage/", views.storage, name="storage"),
    path("transport/", views.transport, name="transport"),
    path("tips/", views.tips, name="tips"),
]
