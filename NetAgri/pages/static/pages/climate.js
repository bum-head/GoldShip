/*
 * NetAgri climate logic: weather lookup + rain / flood alert evaluation.
 *
 * No DOM access in here, so it can be unit-tested in Node
 * (see pages/static/pages/climate.test.js).
 *
 * Data: Open-Meteo (https://open-meteo.com) - free for NON-COMMERCIAL use, no API key.
 *   forecast : https://api.open-meteo.com/v1/forecast
 *   flood    : https://flood-api.open-meteo.com/v1/flood   (GloFAS river discharge)
 * Switch to a commercial plan / another provider before this is used commercially.
 */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.NetAgriClimate = factory();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  /* ---------------------------------------------------------------- *
   * Thresholds. Rainfall classes follow the IMD 24-hour categories:
   *   heavy 64.5-115.5 mm, very heavy 115.6-204.4 mm, extremely heavy >= 204.5 mm
   * Everything else is a heuristic and should be tuned with local data.
   * ---------------------------------------------------------------- */
  const T = {
    heavy24: 64.5,
    veryHeavy24: 115.6,
    extremeHeavy24: 204.5,
    intenseHour: 20, // mm in one hour
    rainLikelyProb: 60, // %
    rainLikelyMm48: 10, // mm over 48 h
    floodRain72Extreme: 250, // mm over 72 h - flood warning on rainfall alone
    floodRain72High: 150, // mm over 72 h
    floodRain72Mid: 100,
    saturatedSoil: 0.35, // m3/m3 (top 1 cm) - ground can't absorb more
    riverRiseHigh: 2.0, // forecast peak / today's discharge
    riverRiseMid: 1.4,
    minRiverDischarge: 5, // m3/s; below this the 5 km model grid is not a real river
  };

  /* WMO weather codes -> [label, icon] */
  const WMO = {
    0: ["Clear sky", "☀️"], 1: ["Mainly clear", "🌤️"], 2: ["Partly cloudy", "⛅"], 3: ["Overcast", "☁️"],
    45: ["Fog", "🌫️"], 48: ["Rime fog", "🌫️"],
    51: ["Light drizzle", "🌦️"], 53: ["Drizzle", "🌦️"], 55: ["Dense drizzle", "🌦️"],
    56: ["Freezing drizzle", "🌧️"], 57: ["Freezing drizzle", "🌧️"],
    61: ["Light rain", "🌦️"], 63: ["Rain", "🌧️"], 65: ["Heavy rain", "🌧️"],
    66: ["Freezing rain", "🌧️"], 67: ["Freezing rain", "🌧️"],
    71: ["Light snow", "🌨️"], 73: ["Snow", "🌨️"], 75: ["Heavy snow", "❄️"], 77: ["Snow grains", "🌨️"],
    80: ["Light showers", "🌦️"], 81: ["Showers", "🌧️"], 82: ["Violent showers", "⛈️"],
    85: ["Snow showers", "🌨️"], 86: ["Heavy snow showers", "❄️"],
    95: ["Thunderstorm", "⛈️"], 96: ["Thunderstorm, hail", "⛈️"], 99: ["Severe thunderstorm, hail", "⛈️"],
  };

  function describe(code) {
    const e = WMO[code];
    return e ? { label: e[0], icon: e[1] } : { label: "Unknown", icon: "❔" };
  }

  /* ------------------------------ geography ------------------------------ */

  function haversineKm(lat1, lon1, lat2, lon2) {
    const R = 6371, rad = Math.PI / 180;
    const dLat = (lat2 - lat1) * rad, dLon = (lon2 - lon1) * rad;
    const a = Math.sin(dLat / 2) ** 2 +
      Math.cos(lat1 * rad) * Math.cos(lat2 * rad) * Math.sin(dLon / 2) ** 2;
    return 2 * R * Math.asin(Math.sqrt(a));
  }

  function inBounds(lat, lon, b) {
    return lat >= b.south && lat <= b.north && lon >= b.west && lon <= b.east;
  }

  /** Nearest known NER place to a coordinate: {name, state, km} or null. */
  function nearestPlace(lat, lon, states) {
    let best = null;
    for (const s of states) {
      for (const p of s.places) {
        const km = haversineKm(lat, lon, p.lat, p.lon);
        if (!best || km < best.km) best = { name: p.name, state: s.name, km };
      }
    }
    return best;
  }

  /* -------------------------------- fetching ------------------------------ */

  const FORECAST_URL = "https://api.open-meteo.com/v1/forecast";
  const FLOOD_URL = "https://flood-api.open-meteo.com/v1/flood";

  function qs(params) {
    return Object.entries(params).map(([k, v]) => `${k}=${encodeURIComponent(v)}`).join("&");
  }

  async function getJson(url, timeoutMs, fetchImpl) {
    const ctl = typeof AbortController !== "undefined" ? new AbortController() : null;
    const timer = ctl ? setTimeout(() => ctl.abort(), timeoutMs) : null;
    try {
      const res = await fetchImpl(url, ctl ? { signal: ctl.signal } : undefined);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } finally {
      if (timer) clearTimeout(timer);
    }
  }

  /**
   * Fetch forecast (required) and river-flood data (optional) for a point.
   * Resolves { forecast, flood|null }. Rejects only if the forecast fails.
   */
  async function fetchWeather(lat, lon, fetchImpl) {
    fetchImpl = fetchImpl || (typeof fetch !== "undefined" ? fetch.bind(globalThis) : null);
    const fUrl = FORECAST_URL + "?" + qs({
      latitude: lat.toFixed(4),
      longitude: lon.toFixed(4),
      current: "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m,wind_gusts_10m",
      hourly: "precipitation,precipitation_probability,soil_moisture_0_to_1cm",
      daily: "weather_code,temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max",
      timezone: "auto",
      forecast_days: 7,
    });
    const rUrl = FLOOD_URL + "?" + qs({
      latitude: lat.toFixed(4),
      longitude: lon.toFixed(4),
      daily: "river_discharge,river_discharge_max",
      forecast_days: 7,
    });
    const [forecast, flood] = await Promise.all([
      getJson(fUrl, 12000, fetchImpl),
      getJson(rUrl, 12000, fetchImpl).catch(() => null), // flood data is a bonus, never fatal
    ]);
    return { forecast, flood };
  }

  /* ------------------------------- evaluation ----------------------------- */

  const sum = (arr) => arr.reduce((a, v) => a + (v || 0), 0);
  const max = (arr) => arr.reduce((a, v) => (v != null && v > a ? v : a), 0);
  const round1 = (n) => Math.round(n * 10) / 10;

  /** Index in hourly.time of the current hour (times are local ISO strings). */
  function currentHourIndex(hourly, currentTime) {
    const hour = (currentTime || "").slice(0, 13); // "2026-10-10T18"
    const i = hourly.time.findIndex((t) => t.slice(0, 13) >= hour);
    return i === -1 ? 0 : i;
  }

  /** Rolling summary used by both the alerts and the dashboard widgets. */
  function summarise(forecast) {
    const h = forecast.hourly;
    const i = currentHourIndex(h, forecast.current && forecast.current.time);
    const win = (arr, n) => arr.slice(i, i + n);

    const p24 = win(h.precipitation, 24), p48 = win(h.precipitation, 48), p72 = win(h.precipitation, 72);
    const prob24 = win(h.precipitation_probability || [], 24);
    const prob48 = win(h.precipitation_probability || [], 48);

    let peakIdx = i, peakVal = -1;
    p48.forEach((v, k) => { if ((v || 0) > peakVal) { peakVal = v || 0; peakIdx = i + k; } });

    const soil = (h.soil_moisture_0_to_1cm || [])[i];
    let firstRain = null; // first hour with >= 0.5 mm
    for (let k = 0; k < p72.length; k++) {
      if ((p72[k] || 0) >= 0.5) { firstRain = h.time[i + k]; break; }
    }

    return {
      startIndex: i,
      rain24: round1(sum(p24)),
      rain48: round1(sum(p48)),
      rain72: round1(sum(p72)),
      probMax24: max(prob24),
      probMax48: max(prob48),
      peakHourMm: round1(Math.max(peakVal, 0)),
      peakHourTime: peakVal > 0 ? h.time[peakIdx] : null,
      firstRain,
      soilMoisture: soil == null ? null : soil,
    };
  }

  /** River status from flood API data: {todayQ, peakQ, peakDate, ratio} or null. */
  function riverStatus(flood) {
    if (!flood || !flood.daily || !flood.daily.river_discharge) return null;
    const q = flood.daily.river_discharge, t = flood.daily.time;
    const valid = q.map((v, k) => [v, k]).filter(([v]) => v != null);
    if (valid.length < 2) return null;
    const todayQ = valid[0][0];
    let peakQ = todayQ, peakK = valid[0][1];
    for (const [v, k] of valid) if (v > peakQ) { peakQ = v; peakK = k; }
    if (todayQ < T.minRiverDischarge && peakQ < T.minRiverDischarge) return null;
    return {
      todayQ: round1(todayQ),
      peakQ: round1(peakQ),
      peakDate: t[peakK],
      ratio: todayQ > 0 ? round1(peakQ / todayQ) : null,
    };
  }

  const LEVELS = { advisory: 1, watch: 2, warning: 3 };

  const ACTIONS = {
    rain: [
      "Harvest mature crops before the rain and move produce under cover.",
      "Clear field drains and channels so water can leave the plot.",
      "Hold off fertiliser and pesticide spraying - rain will wash it away.",
      "Secure livestock, tools and covered storage.",
    ],
    heavy: [
      "Bring harvested produce, seed and fertiliser into dry, raised storage.",
      "Open drainage channels and check bunds on low-lying fields.",
      "Check road and bridge status before sending produce to market.",
      "Keep phones charged and a battery torch ready.",
    ],
    flood: [
      "Move stored grain, seed and inputs above ground level.",
      "Identify the nearest higher ground or relief shelter and a route to it.",
      "Move livestock and equipment to safe ground early.",
      "Delay dispatching produce along low-lying roads and river crossings.",
      "Follow official warnings: IMD, Central Water Commission, state disaster authority.",
    ],
  };

  /**
   * Turn a forecast (+ optional flood data) into alerts.
   * Returns { summary, river, alerts[], topLevel } where each alert is
   * { id, kind, level, title, detail, actions[] } and topLevel is
   * "none" | "advisory" | "watch" | "warning".
   */
  function evaluate(forecast, flood) {
    const s = summarise(forecast);
    const river = riverStatus(flood);
    const alerts = [];

    /* ---- rain ---- */
    let rainLevel = null, rainTitle = "";
    if (s.rain24 >= T.extremeHeavy24) { rainLevel = "warning"; rainTitle = "Extremely heavy rain expected"; }
    else if (s.rain24 >= T.veryHeavy24) { rainLevel = "warning"; rainTitle = "Very heavy rain expected"; }
    else if (s.rain24 >= T.heavy24) { rainLevel = "watch"; rainTitle = "Heavy rain expected"; }
    else if (s.peakHourMm >= T.intenseHour) { rainLevel = "watch"; rainTitle = "Intense downpour possible"; }
    else if (s.probMax48 >= T.rainLikelyProb && s.rain48 >= T.rainLikelyMm48) { rainLevel = "advisory"; rainTitle = "Rain likely"; }

    if (rainLevel) {
      const bits = [`${s.rain24} mm in the next 24 h`, `${s.rain72} mm over 72 h`];
      if (s.peakHourMm >= 5) bits.push(`peak about ${s.peakHourMm} mm/h`);
      alerts.push({
        id: "rain-" + rainLevel,
        kind: "rain",
        level: rainLevel,
        title: rainTitle,
        detail: bits.join(" · ") + (s.firstRain ? `. Rain starts around ${s.firstRain.slice(11, 16)} (${s.firstRain.slice(0, 10)}).` : "."),
        actions: rainLevel === "advisory" ? ACTIONS.rain : ACTIONS.heavy,
      });
    }

    /* ---- flood (score from independent signals) ---- */
    let score = 0;
    const why = [];
    if (s.rain72 >= T.floodRain72Extreme) { score += 4; why.push(`${s.rain72} mm of rain forecast over 72 h`); }
    else if (s.rain72 >= T.floodRain72High) { score += 2; why.push(`${s.rain72} mm of rain forecast over 72 h`); }
    else if (s.rain72 >= T.floodRain72Mid) { score += 1; why.push(`${s.rain72} mm of rain forecast over 72 h`); }

    if (s.soilMoisture != null && s.soilMoisture >= T.saturatedSoil && s.rain72 >= 60) {
      score += 1; why.push("soil is already saturated");
    }
    if (river && river.ratio != null) {
      if (river.ratio >= T.riverRiseHigh) { score += 2; why.push(`nearby river flow forecast to rise ${river.ratio}× (${river.todayQ} → ${river.peakQ} m³/s)`); }
      else if (river.ratio >= T.riverRiseMid) { score += 1; why.push(`nearby river flow forecast to rise ${river.ratio}×`); }
    }
    if (score >= 2) {
      const level = score >= 4 ? "warning" : score === 3 ? "watch" : "advisory";
      alerts.push({
        id: "flood-" + level,
        kind: "flood",
        level,
        title: level === "warning" ? "High flood risk" : level === "watch" ? "Elevated flood risk" : "Possible flooding - stay alert",
        detail: why.join("; ") + ". Model-based estimate, not an official warning.",
        actions: ACTIONS.flood,
      });
    }

    alerts.sort((a, b) => LEVELS[b.level] - LEVELS[a.level]);
    const topLevel = alerts.length ? alerts[0].level : "none";
    return { summary: s, river, alerts, topLevel, floodScore: score };
  }

  return { T, WMO, describe, haversineKm, inBounds, nearestPlace, fetchWeather, summarise, riverStatus, evaluate };
});
