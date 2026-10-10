/*
 * NetAgri dashboard: location detection, weather widgets, minimap, alerts.
 * Depends on climate.js (NetAgriClimate) and, optionally, Leaflet (window.L).
 */
(function () {
  "use strict";
  const C = window.NetAgriClimate;
  const $ = (id) => document.getElementById(id);

  const NER = JSON.parse($("ner-data").textContent);
  const LS = { loc: "netagri.location", map: "netagri.mapOpen", notified: "netagri.notified", cache: "netagri.cache." };
  const REFRESH_MS = 30 * 60 * 1000;
  const NEAR_KM = 60; // within this of a known town -> "Near <town>"

  /* ------------------------- tiny safe storage helpers ------------------------- */
  const store = {
    get(k) { try { return JSON.parse(localStorage.getItem(k)); } catch (e) { return null; } },
    set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* private mode / full */ } },
    del(k) { try { localStorage.removeItem(k); } catch (e) { /* ignore */ } },
  };

  /* safe DOM builder (no innerHTML with data) */
  function el(tag, props, kids) {
    const n = document.createElement(tag);
    for (const [k, v] of Object.entries(props || {})) {
      if (k === "class") n.className = v;
      else if (k === "text") n.textContent = v;
      else n.setAttribute(k, v);
    }
    for (const kid of [].concat(kids || [])) if (kid != null) n.append(kid);
    return n;
  }
  const num = (v, d = 0) => (v == null || Number.isNaN(v) ? "--" : Number(v).toFixed(d));

  /* ================================================================== *
   *  LOCATION
   * ================================================================== */
  let loc = null;       // {lat, lon, label, source, accuracy?}
  let lastData = null;  // {forecast, flood, fetchedAt, offline}
  let refreshTimer = null;

  function labelFor(lat, lon) {
    const near = C.nearestPlace(lat, lon, NER.states);
    const inside = C.inBounds(lat, lon, NER.bounds);
    if (near && near.km <= NEAR_KM) {
      return { label: `Near ${near.name}, ${near.state}`, inside, nearKm: near.km };
    }
    const coords = `${lat.toFixed(3)}°N, ${lon.toFixed(3)}°E`;
    return { label: inside ? `${coords} (NER)` : coords, inside, nearKm: near ? near.km : null };
  }

  function setMsg(text, isError) {
    const m = $("loc-msg");
    m.textContent = text || "";
    m.classList.toggle("error", !!isError);
  }

  function showSetup(show) { $("loc-setup").hidden = !show; }

  function saveLoc() { store.set(LS.loc, loc); }

  function applyLocation(newLoc, opts) {
    opts = opts || {};
    loc = newLoc;
    saveLoc();
    $("dash").dataset.state = "ready";
    showSetup(false);
    setMsg("");

    $("loc-label").textContent = loc.label;
    const meta = [];
    if (loc.source === "gps") meta.push(loc.accuracy ? `GPS ±${formatAcc(loc.accuracy)}` : "GPS");
    else if (loc.source === "map") meta.push("set on map");
    else meta.push("chosen manually");
    if (loc.outside) meta.push("outside NER");
    $("loc-meta").textContent = meta.join(" · ");
    $("loc-chip").hidden = false;
    $("dash-body").hidden = false;
    showNotice(loc.outside
      ? "This location is outside the North Eastern Region. NetAgri is built for NER, but the weather and alerts still work here."
      : "");

    initMap();
    updateMap(opts.fromMap);
    loadWeather();
  }

  function formatAcc(m) { return m >= 1000 ? `${(m / 1000).toFixed(1)} km` : `${Math.round(m)} m`; }

  /* ---------- GPS ---------- */
  function detectGPS(silent) {
    if (!("geolocation" in navigator)) {
      setMsg("This browser can't detect location. Please choose your town below.", true);
      return;
    }
    if (window.isSecureContext === false) {
      setMsg("Location detection needs a secure (https) connection. Please choose your town below.", true);
      return;
    }
    const btn = $("btn-gps");
    btn.disabled = true;
    if (!silent) setMsg("Finding your location…");

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        btn.disabled = false;
        const { latitude: lat, longitude: lon, accuracy } = pos.coords;
        const info = labelFor(lat, lon);
        applyLocation({ lat, lon, accuracy, source: "gps", label: info.label, outside: !info.inside });
      },
      (err) => {
        btn.disabled = false;
        const reasons = {
          1: "Location access was blocked. You can allow it in your browser's site settings, or choose your town below.",
          2: "Your device couldn't work out where you are (no GPS or network signal). Please choose your town below.",
          3: "Finding your location took too long. Try again, or choose your town below.",
        };
        showSetup(true);
        setMsg(reasons[err.code] || "Couldn't detect your location. Please choose your town below.", true);
      },
      { enableHighAccuracy: false, timeout: 12000, maximumAge: 10 * 60 * 1000 }
    );
  }

  function showNotice(text) {
    const box = $("notices");
    box.replaceChildren();
    if (text) box.append(el("div", { class: "alert level-info" }, [el("p", { text })]));
  }

  /* ---------- manual picker ---------- */
  function initPicker() {
    const sState = $("sel-state"), sPlace = $("sel-place"), go = $("btn-pick");
    NER.states.forEach((s, i) => sState.append(el("option", { value: i, text: s.name })));

    sState.addEventListener("change", () => {
      sPlace.replaceChildren(el("option", { value: "", text: "District…" }));
      go.disabled = true;
      if (sState.value === "") { sPlace.disabled = true; return; }
      NER.states[+sState.value].places.forEach((p, i) => sPlace.append(el("option", { value: i, text: p.name })));
      sPlace.disabled = false;
      sPlace.value = "0"; // capital by default
      go.disabled = false;
    });
    sPlace.addEventListener("change", () => { go.disabled = sPlace.value === ""; });

    go.addEventListener("click", () => {
      const s = NER.states[+sState.value], p = s && s.places[+sPlace.value];
      if (!p) return;
      applyLocation({ lat: p.lat, lon: p.lon, source: "manual", label: `${p.name}, ${s.name}` });
    });
  }

  /* ================================================================== *
   *  WEATHER
   * ================================================================== */
  function cacheKey(l) { return LS.cache + l.lat.toFixed(2) + "," + l.lon.toFixed(2); }

  async function loadWeather() {
    clearTimeout(refreshTimer);
    $("btn-refresh").disabled = true;
    const here = loc;
    try {
      const { forecast, flood } = await C.fetchWeather(here.lat, here.lon);
      if (loc !== here) return; // user moved on while we were fetching
      lastData = { forecast, flood, fetchedAt: Date.now(), offline: false };
      store.set(cacheKey(here), { t: lastData.fetchedAt, forecast, flood });
      render();
    } catch (e) {
      if (loc !== here) return;
      const cached = store.get(cacheKey(here));
      if (cached && Date.now() - cached.t < 24 * 3600 * 1000) {
        lastData = { forecast: cached.forecast, flood: cached.flood, fetchedAt: cached.t, offline: true };
        render();
      } else {
        showError();
      }
    } finally {
      $("btn-refresh").disabled = false;
      refreshTimer = setTimeout(loadWeather, REFRESH_MS);
    }
  }

  function showError() {
    $("alerts").replaceChildren(el("div", { class: "alert level-error", role: "alert" }, [
      el("p", { class: "alert-title", text: "Couldn't load the forecast" }),
      el("p", { text: "Check your internet connection and press Refresh. If you've loaded this place before, a saved copy will be shown when you're offline." }),
    ]));
    $("updated").textContent = "";
  }

  /* ---------- render everything from lastData ---------- */
  function render() {
    const { forecast: f, flood, fetchedAt, offline } = lastData;
    const cur = f.current, day = f.daily;
    const w = C.describe(cur.weather_code);
    const result = C.evaluate(f, flood);

    // current
    $("now-icon").textContent = w.icon;
    $("now-temp").textContent = num(cur.temperature_2m);
    $("now-desc").textContent = w.label;
    $("now-feels").textContent = num(cur.apparent_temperature);
    $("st-temp").textContent = num(cur.temperature_2m, 1);
    $("st-lo").textContent = num(day.temperature_2m_min[0]);
    $("st-hi").textContent = num(day.temperature_2m_max[0]);
    $("st-hum").textContent = num(cur.relative_humidity_2m);
    $("st-hum-bar").style.width = Math.max(0, Math.min(100, cur.relative_humidity_2m || 0)) + "%";
    $("st-rain").textContent = num(cur.precipitation, 1);
    $("st-wind").textContent = num(cur.wind_speed_10m);
    $("st-gust").textContent = num(cur.wind_gusts_10m);

    // risk card
    const s = result.summary;
    $("r-24").textContent = num(s.rain24, 0);
    $("r-72").textContent = num(s.rain72, 0);
    $("r-prob").textContent = num(s.probMax48, 0);
    renderOutlook(result);
    $("river-line").textContent = result.river
      ? `River flow nearby: ${result.river.todayQ} m³/s today, peaking at ${result.river.peakQ} m³/s on ${result.river.peakDate}.`
      : "No river-flow data for this spot (small streams aren't covered).";

    renderHourly(f, s);
    renderDays(day);
    renderAlerts(result);
    maybeNotify(result);

    const when = new Date(fetchedAt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    $("updated").textContent = offline
      ? `⚠ Offline - showing saved forecast from ${when}`
      : `Updated ${when}`;
    $("updated").classList.toggle("warn", offline);
  }

  function renderOutlook(result) {
    const rain = result.alerts.find((a) => a.kind === "rain");
    const flood = result.alerts.find((a) => a.kind === "flood");
    const pill = (label, alert, none) =>
      el("div", { class: "pill-row" }, [
        el("span", { class: "pill-label", text: label }),
        el("span", { class: "pill level-" + (alert ? alert.level : "ok"), text: alert ? alert.title : none }),
      ]);
    $("outlook").replaceChildren(
      pill("Rain", rain, "No significant rain expected"),
      pill("Flood", flood, "Low risk")
    );
  }

  /* ---------- 48 h rainfall bars (inline SVG) ---------- */
  function renderHourly(f, s) {
    const h = f.hourly, i = s.startIndex, N = 48;
    const vals = h.precipitation.slice(i, i + N).map((v) => v || 0);
    const times = h.time.slice(i, i + N);
    const probs = (h.precipitation_probability || []).slice(i, i + N);
    const yMax = Math.max(5, Math.ceil(Math.max(...vals) / 5) * 5);
    const W = 480, H = 130, padL = 26, padB = 20, padT = 6;
    const bw = (W - padL) / N, ph = H - padB - padT;
    const NS = "http://www.w3.org/2000/svg";
    const svgEl = (tag, attrs) => { const n = document.createElementNS(NS, tag); for (const [k, v] of Object.entries(attrs || {})) n.setAttribute(k, v); return n; };

    const svg = svgEl("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", class: "chart",
      "aria-label": `Hourly rainfall for the next 48 hours. Total ${s.rain48} millimetres, peak ${s.peakHourMm} millimetres in one hour.` });

    [0, yMax / 2, yMax].forEach((g) => {
      const y = padT + ph - (g / yMax) * ph;
      svg.append(svgEl("line", { x1: padL, x2: W, y1: y, y2: y, class: "gridline" }));
      const t = svgEl("text", { x: padL - 4, y: y + 3, class: "axis", "text-anchor": "end" });
      t.textContent = g % 1 ? g.toFixed(1) : g;
      svg.append(t);
    });
    vals.forEach((v, k) => {
      const bh = (v / yMax) * ph;
      const r = svgEl("rect", { x: padL + k * bw + 0.6, width: Math.max(bw - 1.2, 1), y: padT + ph - bh, height: Math.max(bh, v > 0 ? 1 : 0), class: "bar" + (v >= C.T.intenseHour ? " bar-hot" : "") , rx: 1 });
      const tip = svgEl("title");
      tip.textContent = `${times[k].slice(5, 10)} ${times[k].slice(11, 16)}  ·  ${v.toFixed(1)} mm` + (probs[k] != null ? `  ·  ${probs[k]}% chance` : "");
      r.append(tip);
      svg.append(r);
    });
    times.forEach((t, k) => {
      const hr = +t.slice(11, 13);
      if (k === 0 || hr % 6 === 0) {
        const tx = svgEl("text", { x: padL + k * bw + bw / 2, y: H - 5, class: "axis", "text-anchor": k === 0 ? "start" : "middle" });
        tx.textContent = k === 0 ? "now" : hr === 0 ? t.slice(8, 10) + "/" + t.slice(5, 7) : String(hr).padStart(2, "0") + "h";
        svg.append(tx);
      }
    });
    $("hourly-chart").replaceChildren(svg);
    $("hourly-peak").textContent = s.peakHourMm > 0 ? `Peak ${s.peakHourMm} mm/h around ${s.peakHourTime.slice(11, 16)}` : "No rain expected";
  }

  /* ---------- 7 day ---------- */
  function renderDays(d) {
    const rows = d.time.map((t, k) => {
      const dt = new Date(t + "T00:00:00");
      const name = k === 0 ? "Today" : dt.toLocaleDateString([], { weekday: "short" });
      const w = C.describe(d.weather_code[k]);
      const prob = d.precipitation_probability_max ? d.precipitation_probability_max[k] : null;
      return el("li", { class: "day" }, [
        el("span", { class: "day-name", text: name }),
        el("span", { class: "day-icon", title: w.label, text: w.icon, "aria-label": w.label }),
        el("span", { class: "day-temp" }, [el("strong", { text: num(d.temperature_2m_max[k]) + "°" }), " ", el("span", { class: "muted", text: num(d.temperature_2m_min[k]) + "°" })]),
        el("span", { class: "day-rain" + ((d.precipitation_sum[k] || 0) >= C.T.heavy24 ? " heavy" : ""), text: `${num(d.precipitation_sum[k], 1)} mm` + (prob != null ? ` · ${prob}%` : "") }),
      ]);
    });
    $("days").replaceChildren(...rows);
  }

  /* ---------- alerts ---------- */
  const LEVEL_NAME = { advisory: "Advisory", watch: "Watch", warning: "Warning" };

  function renderAlerts(result) {
    const box = $("alerts");
    box.replaceChildren();
    if (!result.alerts.length) {
      box.append(el("div", { class: "alert level-ok", role: "status" }, [
        el("p", { class: "alert-title", text: "No rain or flood alerts for the next 72 hours" }),
      ]));
      return;
    }
    result.alerts.forEach((a, idx) => {
      const details = el("details", { class: "prep" }, [
        el("summary", { text: "What to prepare" }),
        el("ul", {}, a.actions.map((t) => el("li", { text: t }))),
      ]);
      if (a.level === "warning" || idx === 0) details.open = true;
      box.append(el("div", { class: "alert level-" + a.level, role: a.level === "warning" ? "alert" : "status" }, [
        el("p", { class: "alert-title" }, [
          el("span", { class: "alert-level", text: LEVEL_NAME[a.level] }),
          " " + a.title,
        ]),
        el("p", { class: "alert-detail", text: a.detail }),
        details,
      ]));
    });
  }

  /* ---------- browser notifications (only fire while the page is open) ---------- */
  function notifySupported() { return "Notification" in window; }

  function initNotifyButton() {
    const b = $("btn-notify");
    if (!notifySupported() || Notification.permission !== "default") return;
    b.hidden = false;
    b.addEventListener("click", async () => {
      const p = await Notification.requestPermission();
      b.hidden = true;
      if (p === "granted" && lastData) maybeNotify(C.evaluate(lastData.forecast, lastData.flood));
    });
  }

  function maybeNotify(result) {
    if (!notifySupported() || Notification.permission !== "granted") return;
    const today = new Date().toISOString().slice(0, 10);
    const seen = store.get(LS.notified) || {};
    for (const k of Object.keys(seen)) if (!k.endsWith(today)) delete seen[k]; // drop old days
    for (const a of result.alerts) {
      if (a.level === "advisory") continue; // only interrupt people for watch/warning
      const key = `${loc.label}|${a.id}|${today}`;
      if (seen[key]) continue;
      seen[key] = 1;
      try { new Notification(`NetAgri · ${LEVEL_NAME[a.level]}: ${a.title}`, { body: `${loc.label}. ${a.detail}`, tag: key }); } catch (e) { /* some mobile browsers need a service worker */ }
    }
    store.set(LS.notified, seen);
  }

  /* ================================================================== *
   *  MINIMAP
   * ================================================================== */
  let map = null, marker = null, accCircle = null;

  function initMap() {
    if (map) return;
    const box = $("map");
    if (!window.L) {
      box.replaceChildren(el("p", { class: "muted small pad", text: "The map couldn't load (it needs an internet connection). The weather below still works." }));
      return;
    }
    map = L.map(box, { zoomControl: true, scrollWheelZoom: false, attributionControl: true }).setView([loc.lat, loc.lon], 9);
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 18,
      // OSM blocks tile requests that arrive without a Referer header (HTTP 403).
      referrerPolicy: "strict-origin-when-cross-origin",
      attribution: "&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors",
    }).addTo(map);
    marker = L.marker([loc.lat, loc.lon], { draggable: true, title: "Your location" }).addTo(map);
    marker.on("dragend", () => {
      const p = marker.getLatLng();
      const info = labelFor(p.lat, p.lng);
      applyLocation({ lat: p.lat, lon: p.lng, source: "map", label: info.label, outside: !info.inside }, { fromMap: true });
    });
  }

  function updateMap(fromMap) {
    if (!map) return;
    marker.setLatLng([loc.lat, loc.lon]);
    if (accCircle) { accCircle.remove(); accCircle = null; }
    if (loc.source === "gps" && loc.accuracy && loc.accuracy < 20000) {
      accCircle = L.circle([loc.lat, loc.lon], { radius: loc.accuracy, weight: 1, color: "#267447", fillOpacity: 0.1 }).addTo(map);
    }
    if (!fromMap) map.setView([loc.lat, loc.lon], 9);
    setTimeout(() => map.invalidateSize(), 50);
  }

  function setMapOpen(open, persist) {
    $("map-wrap").hidden = !open;
    const t = $("map-toggle");
    t.setAttribute("aria-expanded", String(open));
    t.textContent = open ? "Hide map ▴" : "Show map ▾";
    if (persist) store.set(LS.map, open);
    if (open && map) setTimeout(() => map.invalidateSize(), 50);
  }

  function initMapToggle() {
    const saved = store.get(LS.map);
    const open = saved == null ? window.matchMedia("(min-width: 760px)").matches : !!saved;
    setMapOpen(open, false);
    $("map-toggle").addEventListener("click", () => setMapOpen($("map-wrap").hidden, true));
  }

  /* ================================================================== *
   *  BOOT
   * ================================================================== */
  function boot() {
    initPicker();
    initMapToggle();
    initNotifyButton();

    $("btn-gps").addEventListener("click", () => detectGPS(false));
    $("btn-refresh").addEventListener("click", loadWeather);
    $("loc-change").addEventListener("click", () => { showSetup(true); $("loc-setup").scrollIntoView({ behavior: "smooth", block: "nearest" }); });
    document.addEventListener("visibilitychange", () => {
      if (!document.hidden && loc && lastData && Date.now() - lastData.fetchedAt > REFRESH_MS) loadWeather();
    });

    const saved = store.get(LS.loc);
    if (saved && Number.isFinite(saved.lat) && Number.isFinite(saved.lon)) {
      applyLocation(saved);
      return;
    }
    showSetup(true);
    // If the user already allowed location for this site, don't make them click.
    if (navigator.permissions && navigator.permissions.query) {
      navigator.permissions.query({ name: "geolocation" }).then((p) => {
        if (p.state === "granted") detectGPS(true);
      }).catch(() => {});
    }
  }

  boot();
})();
