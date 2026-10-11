from django.contrib import admin

from .models import FarmingTip, PestReport, StorageFacility, TransportOffer

admin.site.register(StorageFacility)
admin.site.register(TransportOffer)
admin.site.register(FarmingTip)


@admin.register(PestReport)
class PestReportAdmin(admin.ModelAdmin):
    list_display = ("crop_name", "region", "observed_on", "status", "reporter")
    list_filter = ("status", "region__state", "crop_name")
    search_fields = ("crop_name", "symptoms")
