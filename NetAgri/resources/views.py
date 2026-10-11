from django.db.models import Q
from django.shortcuts import render

from marketplace.models import Region
from .models import FarmingTip, StorageFacility, TransportOffer


def _selected(request):
    s = request.GET.get("region", "")
    return int(s) if s.isdigit() else None


def _render(request, title, intro, items, selected, q=None):
    return render(request, "resources/directory.html", {
        "title": title, "intro": intro, "items": items,
        "regions": Region.objects.all(), "selected": selected, "q": q,
    })


def storage(request):
    rid = _selected(request)
    qs = StorageFacility.objects.select_related("region")
    if rid:
        qs = qs.filter(region_id=rid)
    items = [{
        "title": f.name,
        "lines": [
            f"{f.get_storage_type_display()} · {f.region}",
            f"Capacity: {f.capacity_kg} kg" if f.capacity_kg else "",
            f"Contact: {f.contact}",
            f.notes,
        ],
    } for f in qs]
    return _render(request, "Storage facilities",
                   "Warehouses and cold storage near you, to reduce losses after harvest.", items, rid)


def transport(request):
    rid = _selected(request)
    qs = TransportOffer.objects.select_related("origin", "destination")
    if rid:
        qs = qs.filter(Q(origin_id=rid) | Q(destination_id=rid))
    items = [{
        "title": f"{t.origin} → {t.destination}",
        "lines": [
            f"{t.provider} · {t.vehicle_type}",
            f"Capacity: {t.capacity_kg} kg" if t.capacity_kg else "",
            f"Available from: {t.available_from}" if t.available_from else "",
            f"Contact: {t.contact}",
            t.notes,
        ],
    } for t in qs]
    return _render(request, "Transport offers",
                   "Vehicles and routes for moving crops. Filter by origin or destination.", items, rid)


def tips(request):
    rid = _selected(request)
    q = request.GET.get("q", "").strip()
    qs = FarmingTip.objects.select_related("region")
    if rid:
        qs = qs.filter(Q(region_id=rid) | Q(region__isnull=True))
    if q:
        qs = qs.filter(crop_name__icontains=q)
    items = [{
        "title": f"{t.crop_name}" + (f" ({t.season})" if t.season else ""),
        "lines": [t.content, f"Source: {t.source_url}"],
    } for t in qs]
    return _render(request, "Farming tips",
                   "Practices from agricultural sources, by crop and region.", items, rid, q)
