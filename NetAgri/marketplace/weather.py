from django.core.cache import cache

from pages import climate_service as cs

ADVICE = {
    "good": "Good conditions for harvesting and transport.",
    "fair": "Fair conditions. Check the forecast before harvesting.",
    "poor": "Poor conditions. Consider delaying harvest and transport.",
    "bad": "Bad conditions. Delay harvest and transport if you can.",
}


def region_alert(region):
    """Current-weather alert for a region, cached for 10 minutes. None if unavailable."""
    if region.latitude is None or region.longitude is None:
        return None
    key = f"region-alert:{region.pk}"
    data = cache.get(key)
    if data is None:
        try:
            weather = cs.normalize_weather(
                cs.fetch_raw_weather(float(region.latitude), float(region.longitude))
            )
        except cs.ApiError:
            return None
        rating = cs.rate_weather(weather)
        data = {
            "label": rating["label"],
            "level": rating["level"],
            "condition": rating["condition"],
            "temperature": weather["temperature"],
            "advice": ADVICE[rating["level"]],
        }
        cache.set(key, data, 600)
    return data
