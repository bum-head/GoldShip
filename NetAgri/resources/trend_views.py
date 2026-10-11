from django.core.cache import cache
from django.shortcuts import render

from marketplace.models import Region

from .trends import fetch_daily, monthly_summary
from .views import _selected


def trends(request):
    rid = _selected(request)
    region = Region.objects.filter(pk=rid).first() if rid else None
    rows = annual = error = None
    if region:
        if region.latitude is None or region.longitude is None:
            error = "This region has no coordinates yet."
        else:
            key = f"trends:{region.pk}"
            data = cache.get(key)
            if data is None:
                try:
                    data = monthly_summary(fetch_daily(float(region.latitude), float(region.longitude)))
                    cache.set(key, data, 86400)
                except (OSError, ValueError, KeyError):
                    error = "Historical data is unavailable right now."
            if data:
                rows, annual = data
    return render(request, "resources/trends.html", {
        "regions": Region.objects.all(), "selected": rid, "region": region,
        "rows": rows, "annual": annual, "error": error,
    })
