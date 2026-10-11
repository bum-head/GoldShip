import json
import os
from statistics import median
from urllib.error import URLError
from urllib.request import Request, urlopen

from django.core.cache import cache

from marketplace.models import CropListing

from .trends import fetch_daily, monthly_summary

API_URL = "https://api.openai.com/v1/chat/completions"
MODEL = os.environ.get("ADVISOR_MODEL", "gpt-4o-mini")

SYSTEM = (
    "You are a farming advisor for smallholder farmers in India. Answer in simple, "
    "short language. Use ONLY the data provided below for numbers about climate and "
    "prices; if the data is missing, say so instead of guessing. Climate data is "
    "modelled history, not a forecast. Prices are asking prices, not market rates. "
    "For pest or disease problems, suggest contacting the local agriculture office."
)


class AdvisorError(Exception):
    pass


def build_context(region, crop):
    lines = [f"Region: {region}"]
    key = f"trends:{region.pk}"
    data = cache.get(key)
    if data is None and region.latitude is not None and region.longitude is not None:
        try:
            data = monthly_summary(fetch_daily(float(region.latitude), float(region.longitude)))
            cache.set(key, data, 86400)
        except (OSError, ValueError, KeyError):
            data = None
    if data:
        rows, _ = data
        lines.append("Typical month averages (temp C, rainfall mm, last 5 years):")
        lines += [f"{r['month']}: {r['temp']} C, {r['rain']} mm" for r in rows]
    else:
        lines.append("Climate data: not available.")
    if crop:
        prices = list(CropListing.objects.filter(
            crop_name__iexact=crop.strip(), region=region
        ).values_list("price_per_kg", flat=True))
        if prices:
            lines.append(f"Asking prices for {crop} in this region: {len(prices)} listings, "
                         f"median Rs {median(prices)}/kg.")
        else:
            lines.append(f"Asking prices for {crop} in this region: no listings.")
    return "\n".join(lines)


def ask(question, context):
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise AdvisorError("The advisor is not configured yet.")
    body = json.dumps({
        "model": MODEL,
        "max_completion_tokens": 600,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"DATA:\n{context}\n\nQUESTION: {question}"},
        ],
    }).encode()
    req = Request(API_URL, data=body, headers={
        "content-type": "application/json",
        "authorization": f"Bearer {key}",
    })
    try:
        with urlopen(req, timeout=30) as r:
            payload = json.load(r)
        return payload["choices"][0]["message"]["content"].strip()
    except (OSError, URLError, ValueError, KeyError, IndexError):
        raise AdvisorError("The advisor is unavailable right now. Please try again.")


def local_summary(region, crop):
    """Free fallback: summarise climate and prices without calling any AI."""
    key = f"trends:{region.pk}"
    data = cache.get(key)
    if data is None and region.latitude is not None and region.longitude is not None:
        try:
            data = monthly_summary(fetch_daily(float(region.latitude), float(region.longitude)))
            cache.set(key, data, 86400)
        except (OSError, ValueError, KeyError):
            data = None
    lines = []
    if data:
        rows = [r for r in data[0] if r["rain"] is not None and r["temp"] is not None]
        if rows:
            wet = sorted(rows, key=lambda r: -r["rain"])[:3]
            dry = sorted(rows, key=lambda r: r["rain"])[:3]
            hot = max(rows, key=lambda r: r["temp"])
            cool = min(rows, key=lambda r: r["temp"])
            lines.append("Wettest months: " + ", ".join(f"{r['month']} ({r['rain']} mm)" for r in wet) + ".")
            lines.append("Driest months: " + ", ".join(f"{r['month']} ({r['rain']} mm)" for r in dry) + ".")
            lines.append(f"Warmest month: {hot['month']} ({hot['temp']} C). Coolest: {cool['month']} ({cool['temp']} C).")
            lines.append("Tip: plan sowing around the wet months and keep harvest and transport in the drier ones.")
    else:
        lines.append("Climate data is not available for this region right now.")
    if crop:
        prices = list(CropListing.objects.filter(
            crop_name__iexact=crop.strip(), region=region
        ).values_list("price_per_kg", flat=True))
        if prices:
            lines.append(f"Local asking prices for {crop}: {len(prices)} listings, median Rs {median(prices)}/kg (asking prices, not market rates).")
        else:
            lines.append(f"No local listings for {crop} yet.")
    lines.append("This is a summary of historical data, not a forecast.")
    return "\n".join(lines)
