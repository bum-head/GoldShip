from django.urls import path

from . import pest_views, views

app_name = "resources"

urlpatterns = [
    path("storage/", views.storage, name="storage"),
    path("transport/", views.transport, name="transport"),
    path("tips/", views.tips, name="tips"),
    path("pests/", pest_views.pests, name="pests"),
    path("pests/report/", pest_views.report_pest, name="report_pest"),
]
