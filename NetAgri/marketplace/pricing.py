from statistics import median

from .models import CropListing

MIN_COMPARABLES = 3
IN_LINE_PCT = 10


def price_context(listing):
    """Compare a listing's asking price with other listings of the same crop.

    Uses the listing's own region when it has enough comparables, otherwise all
    regions. Returns None when there is not enough data to say anything useful.
    """
    others = CropListing.objects.filter(
        crop_name__iexact=listing.crop_name.strip()
    ).exclude(pk=listing.pk)

    sample = list(others.filter(region=listing.region).values_list("price_per_kg", flat=True))
    scope = listing.region.name
    if len(sample) < MIN_COMPARABLES:
        sample = list(others.values_list("price_per_kg", flat=True))
        scope = "all regions"
    if len(sample) < MIN_COMPARABLES:
        return None

    mid = median(sample)
    if not mid:
        return None

    pct = round((listing.price_per_kg - mid) / mid * 100)
    if abs(pct) < IN_LINE_PCT:
        verdict = "in line with"
    elif pct > 0:
        verdict = f"{pct}% above"
    else:
        verdict = f"{abs(pct)}% below"

    return {"median": mid, "n": len(sample), "scope": scope, "verdict": verdict}
