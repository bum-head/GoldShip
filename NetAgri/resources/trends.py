import calendar
import json
from collections import defaultdict
from datetime import date
from statistics import mean
from urllib.parse import urlencode
from urllib.request import urlopen

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
YEARS = 5


def fetch_daily(lat, lon):
    this_year = date.today().year
    params = urlencode({
        "latitude": lat, "longitude": lon,
        "start_date": f"{this_year - YEARS}-01-01", "end_date": f"{this_year - 1}-12-31",
        "daily": "temperature_2m_mean,precipitation_sum", "timezone": "auto",
    })
    with urlopen(f"{ARCHIVE_URL}?{params}", timeout=20) as r:
        return json.load(r)["daily"]


def monthly_summary(daily):
    temps, rain = defaultdict(list), defaultdict(float)
    for day, t, p in zip(daily["time"], daily["temperature_2m_mean"], daily["precipitation_sum"]):
        y, m = int(day[:4]), int(day[5:7])
        if t is not None:
            temps[m].append(t)
        if p is not None:
            rain[(y, m)] += p
    years = sorted({y for y, _ in rain})
    rows = []
    for m in range(1, 13):
        totals = [rain[(y, m)] for y in years if (y, m) in rain]
        rows.append({
            "month": calendar.month_abbr[m],
            "temp": round(mean(temps[m]), 1) if temps[m] else None,
            "rain": round(mean(totals)) if totals else None,
        })
    top = max((r["rain"] or 0 for r in rows), default=0) or 1
    for r in rows:
        r["pct"] = round((r["rain"] or 0) / top * 100)
    annual = [{"year": y, "rain": round(sum(v for (yy, _), v in rain.items() if yy == y))} for y in years]
    return rows, annual
