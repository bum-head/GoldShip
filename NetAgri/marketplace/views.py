from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import CropListingForm
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


@login_required
def create_listing(request):
    if request.method == "POST":
        form = CropListingForm(request.POST)

        if form.is_valid():
            listing = form.save(commit=False)
            listing.seller = request.user
            listing.save()

            return redirect("marketplace:crop_list")
    else:
        form = CropListingForm()

    return render(
        request,
        "marketplace/listing_form.html",
        {"form": form},
    )
