from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import CropListingForm, InquiryForm
from .models import CropListing, Inquiry, Region
from .weather import region_alert


def crop_list(request):
    listings = (
        CropListing.objects
        .filter(status="active")
        .select_related("region", "seller")
    )

    selected = request.GET.get("region", "")
    region = None
    if selected.isdigit():
        region = Region.objects.filter(pk=int(selected)).first()
        listings = listings.filter(region_id=int(selected))

    q = request.GET.get("q", "").strip()
    if q:
        listings = listings.filter(crop_name__icontains=q)

    return render(request, "marketplace/crop_list.html", {
        "listings": listings,
        "regions": Region.objects.all(),
        "selected": selected,
        "q": q,
        "region": region,
        "alert": region_alert(region) if region else None,
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


@login_required
def my_listings(request):
    listings = CropListing.objects.filter(seller=request.user).select_related("region")
    return render(request, "marketplace/my_listings.html", {"listings": listings})


@login_required
def edit_listing(request, pk):
    listing = get_object_or_404(CropListing, pk=pk, seller=request.user)
    if request.method == "POST":
        form = CropListingForm(request.POST, instance=listing)
        if form.is_valid():
            form.save()
            return redirect("marketplace:my_listings")
    else:
        form = CropListingForm(instance=listing)
    return render(request, "marketplace/listing_form.html", {"form": form})


@login_required
@require_POST
def mark_sold(request, pk):
    listing = get_object_or_404(CropListing, pk=pk, seller=request.user)
    listing.status = "sold"
    listing.save(update_fields=["status"])
    return redirect("marketplace:my_listings")


@login_required
def create_inquiry(request, pk):
    listing = get_object_or_404(CropListing, pk=pk, status="active")
    if listing.seller_id == request.user.id:
        raise PermissionDenied("You cannot send an inquiry about your own listing.")

    if request.method == "POST":
        form = InquiryForm(request.POST, listing=listing)
        if form.is_valid():
            inquiry = form.save(commit=False)
            inquiry.buyer = request.user
            inquiry.listing = listing
            inquiry.save()
            return redirect("marketplace:inquiry_list")
    else:
        form = InquiryForm(listing=listing)

    return render(request, "marketplace/inquiry_form.html", {"form": form, "listing": listing})


@login_required
def inquiry_list(request):
    sent = Inquiry.objects.filter(buyer=request.user).select_related("listing__region", "listing__seller")
    received = Inquiry.objects.filter(listing__seller=request.user).select_related("listing", "buyer")
    return render(request, "marketplace/inquiry_list.html", {"sent": sent, "received": received})


@login_required
@require_POST
def respond_to_inquiry(request, pk):
    inquiry = get_object_or_404(Inquiry, pk=pk, listing__seller=request.user)
    status = request.POST.get("status")
    if inquiry.status == "pending" and status in ("accepted", "declined"):
        inquiry.status = status
        inquiry.save(update_fields=["status"])
    return redirect("marketplace:inquiry_list")
