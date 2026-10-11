from django.contrib import admin

from .models import FarmingTip, StorageFacility, TransportOffer

admin.site.register(StorageFacility)
admin.site.register(TransportOffer)
admin.site.register(FarmingTip)
