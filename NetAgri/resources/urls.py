from django.urls import path

from . import advisor_views, pest_views, trend_views, views

app_name = "resources"

urlpatterns = [
    path("storage/", views.storage, name="storage"),
    path("transport/", views.transport, name="transport"),
    path("tips/", views.tips, name="tips"),
    path("pests/", pest_views.pests, name="pests"),
    path("pests/report/", pest_views.report_pest, name="report_pest"),
    path("trends/", trend_views.trends, name="trends"),
    path("advisor/", advisor_views.advisor, name="advisor"),
]
