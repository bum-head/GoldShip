from django.shortcuts import render

from .models import CropListing


def crop_list(request):
    listings = (
        CropListing.objects
        .filter(status="active")
        .select_related("region", "seller")
    )

    return render(
        request,
        "marketplace/crop_list.html",
        {"listings": listings},
    )
