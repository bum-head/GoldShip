from django.urls import path

from . import views

app_name = "marketplace"

urlpatterns = [
    path("", views.crop_list, name="crop_list"),
    path("add/", views.create_listing, name="create_listing"),
    path("mine/", views.my_listings, name="my_listings"),
    path("listing/<int:pk>/edit/", views.edit_listing, name="edit_listing"),
    path("listing/<int:pk>/sold/", views.mark_sold, name="mark_sold"),
    path("listing/<int:pk>/inquire/", views.create_inquiry, name="create_inquiry"),
    path("inquiries/", views.inquiry_list, name="inquiry_list"),
    path("inquiries/<int:pk>/respond/", views.respond_to_inquiry, name="respond_to_inquiry"),
]
