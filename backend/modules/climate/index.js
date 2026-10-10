// Climate module: weather data + Good→Bad rating.   Routes: /api/climate/...
const { parseCoords, fetchRawWeather, normalizeWeather, DEFAULT_LAT, DEFAULT_LON } = require("./service");
const { rateWeather } = require("./rating");

module.exports = {
  name: "climate",
  description: "Current weather (Open-Meteo) and a Good→Bad farming rating",
  version: "1.0.0",

  routes: [
    {
      method: "GET",
      path: "/weather",
      description: "Raw Open-Meteo JSON. Optional ?lat=&lon=",
      handler: async ({ query }) => fetchRawWeather(parseCoords(query)),
    },
    {
      method: "GET",
      path: "/rating",
      description: "Readings + rating. Optional ?lat=&lon=",
      handler: async ({ query }) => {
        const location = parseCoords(query);
        const weather = normalizeWeather(await fetchRawWeather(location));
        return { location, weather, rating: rateWeather(weather) };
      },
    },
  ],

  // Used by the dashboard: can we reach the weather API right now?
  health: async () => {
    const w = normalizeWeather(await fetchRawWeather({ lat: DEFAULT_LAT, lon: DEFAULT_LON }));
    return { ok: true, detail: `Weather API reachable (${w.temperature} °C at default location)` };
  },
};
