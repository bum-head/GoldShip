// Run with:  node pages/static/pages/climate.test.js   (from the NetAgri folder)
const assert = require("node:assert/strict");
const C = require("./climate.js");

/** Build a fake Open-Meteo forecast: 168 hourly values from 2026-10-10T00:00. */
function fake({ rain = () => 0, prob = () => 0, soil = 0.2, nowHour = 18 } = {}) {
  const time = [];
  for (let d = 0; d < 7; d++) for (let h = 0; h < 24; h++) {
    time.push(`2026-10-${String(10 + d).padStart(2, "0")}T${String(h).padStart(2, "0")}:00`);
  }
  return {
    current: { time: `2026-10-10T${String(nowHour).padStart(2, "0")}:15` },
    hourly: {
      time,
      precipitation: time.map((_, i) => rain(i - nowHour)),
      precipitation_probability: time.map((_, i) => prob(i - nowHour)),
      soil_moisture_0_to_1cm: time.map(() => soil),
    },
  };
}
const flood = (q) => ({ daily: { time: q.map((_, i) => `2026-10-${10 + i}`), river_discharge: q } });
let n = 0;
const t = (name, fn) => { fn(); n++; console.log("ok -", name); };

t("dry day: no alerts", () => {
  const r = C.evaluate(fake());
  assert.equal(r.topLevel, "none");
  assert.equal(r.alerts.length, 0);
});

t("window starts at the current hour, not midnight", () => {
  // 100 mm fell earlier today (hours 0-5) - must NOT count towards the forecast
  const r = C.evaluate(fake({ rain: (rel) => (rel < -10 ? 20 : 0) }));
  assert.equal(r.summary.rain24, 0);
  assert.equal(r.topLevel, "none");
});

t("rain likely -> advisory", () => {
  const r = C.evaluate(fake({ rain: (rel) => (rel >= 0 && rel < 6 ? 2 : 0), prob: () => 80 }));
  assert.equal(r.topLevel, "advisory");
  assert.equal(r.alerts[0].kind, "rain");
});

t("high probability but trivial rain -> no alert", () => {
  const r = C.evaluate(fake({ rain: () => 0.1, prob: () => 90 }));
  assert.equal(r.alerts.length, 0);
});

t("heavy rain (>=64.5 mm/24h) -> watch", () => {
  const r = C.evaluate(fake({ rain: (rel) => (rel >= 0 && rel < 12 ? 6 : 0) })); // 72 mm
  assert.equal(r.alerts[0].level, "watch");
  assert.match(r.alerts[0].title, /Heavy rain/);
});

t("very heavy rain (>=115.6 mm/24h) -> warning", () => {
  const r = C.evaluate(fake({ rain: (rel) => (rel >= 0 && rel < 12 ? 10 : 0) })); // 120 mm
  assert.equal(r.alerts[0].level, "warning");
});

t("intense single hour -> watch", () => {
  const r = C.evaluate(fake({ rain: (rel) => (rel === 3 ? 25 : 0) }));
  assert.equal(r.alerts[0].level, "watch");
  assert.match(r.alerts[0].title, /downpour/i);
});

t("flood: big 72h rain + saturated soil -> flood alert, sorted by severity", () => {
  const r = C.evaluate(fake({ rain: (rel) => (rel >= 0 && rel < 36 ? 5 : 0), soil: 0.42 })); // 180 mm
  const f = r.alerts.find((a) => a.kind === "flood");
  assert.ok(f, "flood alert present");
  assert.equal(f.level, "watch"); // 180 mm + saturated soil = score 3
  assert.ok(f.detail.includes("not an official warning"));
  assert.ok(f.actions.length > 0);
  const order = r.alerts.map((a) => ["advisory", "watch", "warning"].indexOf(a.level));
  assert.deepEqual(order, [...order].sort((a, b) => b - a));
});

t("flood: extreme 72h rainfall alone -> flood warning", () => {
  const r = C.evaluate(fake({ rain: (rel) => (rel >= 0 && rel < 36 ? 7.5 : 0) })); // 270 mm
  assert.equal(r.alerts.find((a) => a.kind === "flood").level, "warning");
  assert.equal(r.topLevel, "warning");
});

t("flood: river surge alone (no local rain) still alerts - upstream flooding", () => {
  const r = C.evaluate(fake(), flood([1000, 1400, 2300, 3000, 2800, 2500, 2000]));
  assert.equal(r.river.ratio, 3);
  const f = r.alerts.find((a) => a.kind === "flood");
  assert.ok(f);
  assert.equal(f.level, "advisory"); // river signal alone = score 2
});

t("flood: tiny stream (below model resolution) is ignored", () => {
  const r = C.evaluate(fake(), flood([0.5, 1, 3, 4, 2, 1, 1]));
  assert.equal(r.river, null);
  assert.equal(r.alerts.length, 0);
});

t("flood: stable river + light rain -> nothing", () => {
  const r = C.evaluate(fake({ rain: () => 0.2 }), flood([800, 810, 820, 800, 790, 780, 770]));
  assert.equal(r.alerts.length, 0);
});

t("missing flood data / missing optional hourly fields don't crash", () => {
  const fc = fake();
  delete fc.hourly.precipitation_probability;
  delete fc.hourly.soil_moisture_0_to_1cm;
  assert.doesNotThrow(() => C.evaluate(fc, null));
  assert.doesNotThrow(() => C.evaluate(fc, { daily: {} }));
});

t("null values in arrays are tolerated", () => {
  const fc = fake({ rain: () => 1 });
  fc.hourly.precipitation[20] = null;
  assert.doesNotThrow(() => C.evaluate(fc, flood([null, null, 5, 9, null, 8, 8])));
});

t("nearestPlace / inBounds", () => {
  const states = [{ name: "Assam", places: [{ name: "Jorhat", lat: 26.7509, lon: 94.2037 }, { name: "Guwahati", lat: 26.1445, lon: 91.7362 }] }];
  const p = C.nearestPlace(26.76, 94.21, states);
  assert.equal(p.name, "Jorhat");
  assert.ok(p.km < 3);
  const b = { south: 21.9, north: 29.5, west: 87.9, east: 97.5 };
  assert.equal(C.inBounds(26.1, 91.7, b), true);
  assert.equal(C.inBounds(28.6, 77.2, b), false); // Delhi
});

t("describe() handles known and unknown codes", () => {
  assert.equal(C.describe(65).label, "Heavy rain");
  assert.equal(C.describe(12345).label, "Unknown");
});

t("fetchWeather: flood API failure is non-fatal, forecast failure is fatal", async () => {});
(async () => {
  const ok = { ok: true, json: async () => ({ hello: 1 }) };
  const r = await C.fetchWeather(26.14, 91.74, async (u) => {
    if (u.includes("flood-api")) throw new Error("down");
    assert.ok(u.includes("latitude=26.1400") && u.includes("timezone=auto"));
    return ok;
  });
  assert.equal(r.flood, null);
  assert.deepEqual(r.forecast, { hello: 1 });
  await assert.rejects(C.fetchWeather(1, 2, async () => ({ ok: false, status: 500 })), /HTTP 500/);
  console.log("ok - fetchWeather error handling");
  console.log(`\n${n + 1} tests passed`);
})();
