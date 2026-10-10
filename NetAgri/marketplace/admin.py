from django.contrib import admin
from .models import Region, CropListing


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ("name", "district", "state")


@admin.register(CropListing)
class CropListingAdmin(admin.ModelAdmin):
    list_display = (
        "crop_name",
        "quantity_kg",
        "price_per_kg",
        "region",
        "seller",
        "status",
    )

    list_filter = ("status", "region")
    search_fields = ("crop_name", "variety")
