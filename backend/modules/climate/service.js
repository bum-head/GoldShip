const { HttpError } = require("../../core/errors");

const API_URL = process.env.WEATHER_API_URL || "https://api.open-meteo.com/v1/forecast";
const TIMEOUT_MS = 8000;
const DEFAULT_LAT = 26.73; // Assam
const DEFAULT_LON = 93.15;

// Reads and validates lat/lon from the query (falls back to the defaults).
function parseCoords(query) {
  const read = (raw, fallback) => (raw === undefined || String(raw).trim() === "" ? fallback : Number(raw));
  const lat = read(query.lat, DEFAULT_LAT);
  const lon = read(query.lon, DEFAULT_LON);
  if (!Number.isFinite(lat) || lat < -90 || lat > 90) throw new HttpError(400, "lat must be a number between -90 and 90");
  if (!Number.isFinite(lon) || lon < -180 || lon > 180) throw new HttpError(400, "lon must be a number between -180 and 180");
  return { lat, lon };
}

// Raw Open-Meteo JSON (current_weather block + humidity/precipitation).
async function fetchRawWeather({ lat, lon }) {
  const url = new URL(API_URL);
  url.searchParams.set("latitude", lat);
  url.searchParams.set("longitude", lon);
  url.searchParams.set("current_weather", "true");
  url.searchParams.set("current", "relative_humidity_2m,precipitation");
  url.searchParams.set("timezone", "auto");

  let res;
  try {
    res = await fetch(url, { signal: AbortSignal.timeout(TIMEOUT_MS) });
  } catch (e) {
    throw new HttpError(502, `Weather service unreachable: ${e.message}`);
  }
  if (!res.ok) throw new HttpError(502, `Weather service returned ${res.status}`);
  return res.json();
}

// Flattens the raw response into the fields the rating uses.
function normalizeWeather(raw) {
  const cw = raw.current_weather;
  if (!cw) throw new HttpError(502, "Weather service returned no current weather");
  const cur = raw.current || {};
  return {
    temperature: cw.temperature,                 // °C
    windspeed: cw.windspeed,                     // km/h
    weathercode: cw.weathercode,                 // WMO code
    humidity: cur.relative_humidity_2m ?? null,  // %
    precipitation: cur.precipitation ?? 0,       // mm
    time: cw.time,
  };
}

module.exports = { parseCoords, fetchRawWeather, normalizeWeather, DEFAULT_LAT, DEFAULT_LON };
