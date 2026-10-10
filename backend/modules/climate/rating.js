// Turns weather readings into a Good → Bad rating for outdoor/farm work.
// Pure function (no network), easy to tune.  Score starts at 100 and loses points:
//   80-100 Good | 60-79 Fair | 40-59 Poor | 0-39 Bad

const clamp = (n, lo, hi) => Math.min(hi, Math.max(lo, n));

// WMO weather codes -> [penalty, description]
const CONDITIONS = {
  0: [0, "Clear sky"], 1: [0, "Mainly clear"], 2: [0, "Partly cloudy"], 3: [3, "Overcast"],
  45: [10, "Fog"], 48: [10, "Freezing fog"],
  51: [10, "Light drizzle"], 53: [10, "Drizzle"], 55: [12, "Heavy drizzle"],
  56: [15, "Freezing drizzle"], 57: [18, "Heavy freezing drizzle"],
  61: [15, "Light rain"], 63: [20, "Rain"], 65: [30, "Heavy rain"],
  66: [25, "Freezing rain"], 67: [30, "Heavy freezing rain"],
  71: [20, "Light snow"], 73: [25, "Snow"], 75: [30, "Heavy snow"], 77: [20, "Snow grains"],
  80: [12, "Light rain showers"], 81: [18, "Rain showers"], 82: [30, "Violent rain showers"],
  85: [25, "Snow showers"], 86: [30, "Heavy snow showers"],
  95: [35, "Thunderstorm"], 96: [45, "Thunderstorm with hail"], 99: [45, "Severe thunderstorm with hail"],
};

const LEVELS = [
  { min: 80, label: "Good", level: "good" },
  { min: 60, label: "Fair", level: "fair" },
  { min: 40, label: "Poor", level: "poor" },
  { min: 0,  label: "Bad",  level: "bad" },
];

function rateWeather(w) {
  const factors = [];
  const add = (name, penalty, note) => factors.push({ name, penalty: Math.round(penalty), note });

  const t = w.temperature; // comfortable: 15-30 °C
  if (typeof t === "number") {
    if (t < 15) add("Temperature", clamp((15 - t) * 3, 0, 40), `${t} °C is cold`);
    else if (t > 30) add("Temperature", clamp((t - 30) * 4, 0, 40), `${t} °C is hot`);
    else add("Temperature", 0, `${t} °C is comfortable`);
  }

  const wind = w.windspeed; // fine up to 15 km/h
  if (typeof wind === "number") {
    if (wind > 15) add("Wind", clamp((wind - 15) * 1.5, 0, 30), `${wind} km/h is strong`);
    else add("Wind", 0, `${wind} km/h is calm`);
  }

  const rain = w.precipitation;
  if (typeof rain === "number") {
    if (rain > 0) add("Precipitation", clamp(rain * 10, 0, 30), `${rain} mm falling`);
    else add("Precipitation", 0, "No precipitation");
  }

  const h = w.humidity; // fine at 30-85 %
  if (typeof h === "number") {
    if (h > 85) add("Humidity", clamp(h - 85, 0, 15), `${h}% is very humid`);
    else if (h < 30) add("Humidity", clamp((30 - h) * 0.5, 0, 10), `${h}% is very dry`);
    else add("Humidity", 0, `${h}% is comfortable`);
  }

  const [codePenalty, condition] = CONDITIONS[w.weathercode] || [0, "Unknown conditions"];
  add("Conditions", codePenalty, condition);

  const score = clamp(Math.round(100 - factors.reduce((s, f) => s + f.penalty, 0)), 0, 100);
  const { label, level } = LEVELS.find((l) => score >= l.min);
  return { score, label, level, condition, factors };
}

module.exports = { rateWeather };
