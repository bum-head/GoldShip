"""Climate service: port of backend/modules/climate (service.js + rating.js)."""
import json
import math
import os
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

API_URL = os.environ.get("WEATHER_API_URL", "https://api.open-meteo.com/v1/forecast")
TIMEOUT_S = 8
DEFAULT_LAT = 26.73  # Assam
DEFAULT_LON = 93.15


class ApiError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


def _read(raw, fallback):
    if raw is None or str(raw).strip() == "":
        return fallback
    try:
        return float(raw)
    except ValueError:
        return math.nan


def parse_coords(query):
    lat = _read(query.get("lat"), DEFAULT_LAT)
    lon = _read(query.get("lon"), DEFAULT_LON)
    if not math.isfinite(lat) or lat < -90 or lat > 90:
        raise ApiError(400, "lat must be a number between -90 and 90")
    if not math.isfinite(lon) or lon < -180 or lon > 180:
        raise ApiError(400, "lon must be a number between -180 and 180")
    return {"lat": lat, "lon": lon}


def fetch_raw_weather(lat, lon):
    params = urlencode({
        "latitude": lat,
        "longitude": lon,
        "current_weather": "true",
        "current": "relative_humidity_2m,precipitation",
        "timezone": "auto",
    })
    try:
        with urlopen(f"{API_URL}?{params}", timeout=TIMEOUT_S) as resp:
            return json.load(resp)
    except HTTPError as e:  # must come before URLError (it is a subclass)
        raise ApiError(502, f"Weather service returned {e.code}")
    except (URLError, TimeoutError, ValueError) as e:
        raise ApiError(502, f"Weather service unreachable: {e}")


def normalize_weather(raw):
    cw = raw.get("current_weather")
    if not cw:
        raise ApiError(502, "Weather service returned no current weather")
    cur = raw.get("current") or {}
    precip = cur.get("precipitation")
    return {
        "temperature": cw.get("temperature"),
        "windspeed": cw.get("windspeed"),
        "weathercode": cw.get("weathercode"),
        "humidity": cur.get("relative_humidity_2m"),
        "precipitation": 0 if precip is None else precip,
        "time": cw.get("time"),
    }


# ---------------------------------------------------------------- rating
def _clamp(n, lo, hi):
    return min(hi, max(lo, n))


def _js_round(x):  # JavaScript's Math.round: halves round up
    return math.floor(x + 0.5)


def _n(x):  # print 33.0 as "33", like JavaScript does
    return int(x) if isinstance(x, float) and x.is_integer() else x


def _is_num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


CONDITIONS = {
    0: (0, "Clear sky"), 1: (0, "Mainly clear"), 2: (0, "Partly cloudy"), 3: (3, "Overcast"),
    45: (10, "Fog"), 48: (10, "Freezing fog"),
    51: (10, "Light drizzle"), 53: (10, "Drizzle"), 55: (12, "Heavy drizzle"),
    56: (15, "Freezing drizzle"), 57: (18, "Heavy freezing drizzle"),
    61: (15, "Light rain"), 63: (20, "Rain"), 65: (30, "Heavy rain"),
    66: (25, "Freezing rain"), 67: (30, "Heavy freezing rain"),
    71: (20, "Light snow"), 73: (25, "Snow"), 75: (30, "Heavy snow"), 77: (20, "Snow grains"),
    80: (12, "Light rain showers"), 81: (18, "Rain showers"), 82: (30, "Violent rain showers"),
    85: (25, "Snow showers"), 86: (30, "Heavy snow showers"),
    95: (35, "Thunderstorm"), 96: (45, "Thunderstorm with hail"), 99: (45, "Severe thunderstorm with hail"),
}

LEVELS = [
    {"min": 80, "label": "Good", "level": "good"},
    {"min": 60, "label": "Fair", "level": "fair"},
    {"min": 40, "label": "Poor", "level": "poor"},
    {"min": 0, "label": "Bad", "level": "bad"},
]


def rate_weather(w):
    factors = []

    def add(name, penalty, note):
        factors.append({"name": name, "penalty": _js_round(penalty), "note": note})

    t = w.get("temperature")
    if _is_num(t):
        if t < 15:
            add("Temperature", _clamp((15 - t) * 3, 0, 40), f"{_n(t)} °C is cold")
        elif t > 30:
            add("Temperature", _clamp((t - 30) * 4, 0, 40), f"{_n(t)} °C is hot")
        else:
            add("Temperature", 0, f"{_n(t)} °C is comfortable")

    wind = w.get("windspeed")
    if _is_num(wind):
        if wind > 15:
            add("Wind", _clamp((wind - 15) * 1.5, 0, 30), f"{_n(wind)} km/h is strong")
        else:
            add("Wind", 0, f"{_n(wind)} km/h is calm")

    rain = w.get("precipitation")
    if _is_num(rain):
        if rain > 0:
            add("Precipitation", _clamp(rain * 10, 0, 30), f"{_n(rain)} mm falling")
        else:
            add("Precipitation", 0, "No precipitation")

    h = w.get("humidity")
    if _is_num(h):
        if h > 85:
            add("Humidity", _clamp(h - 85, 0, 15), f"{_n(h)}% is very humid")
        elif h < 30:
            add("Humidity", _clamp((30 - h) * 0.5, 0, 10), f"{_n(h)}% is very dry")
        else:
            add("Humidity", 0, f"{_n(h)}% is comfortable")

    penalty, condition = CONDITIONS.get(w.get("weathercode"), (0, "Unknown conditions"))
    add("Conditions", penalty, condition)

    score = _clamp(_js_round(100 - sum(f["penalty"] for f in factors)), 0, 100)
    lvl = next(l for l in LEVELS if score >= l["min"])
    return {"score": score, "label": lvl["label"], "level": lvl["level"],
            "condition": condition, "factors": factors}
