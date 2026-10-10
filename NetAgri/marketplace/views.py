from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import CropListingForm
from .models import CropListing, Region


def crop_list(request):
    listings = (
        CropListing.objects
        .filter(status="active")
        .select_related("region", "seller")
    )

    selected = request.GET.get("region", "")
    if selected.isdigit():
        listings = listings.filter(region_id=int(selected))

    q = request.GET.get("q", "").strip()
    if q:
        listings = listings.filter(crop_name__icontains=q)

    return render(request, "marketplace/crop_list.html", {
        "listings": listings,
        "regions": Region.objects.all(),
        "selected": selected,
        "q": q,
    })


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

    return render(request, "marketplace/listing_form.html", {"form": form})
