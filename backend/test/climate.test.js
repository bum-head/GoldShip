const test = require("node:test");
const assert = require("node:assert/strict");

const {
  parseCoords,
  normalizeWeather,
  DEFAULT_LAT,
  DEFAULT_LON,
} = require("../modules/climate/service");

const { rateWeather } = require("../modules/climate/rating");


test("coordinates default when omitted", () => {
  assert.deepEqual(parseCoords({}), {
    lat: DEFAULT_LAT,
    lon: DEFAULT_LON,
  });
});


test("valid coordinates are accepted", () => {
  assert.deepEqual(
    parseCoords({ lat: "26.73", lon: "93.15" }),
    { lat: 26.73, lon: 93.15 }
  );
});


test("invalid latitude is rejected", () => {
  assert.throws(
    () => parseCoords({ lat: "999", lon: "93" }),
    (error) => error.status === 400
  );
});


test("invalid longitude is rejected", () => {
  assert.throws(
    () => parseCoords({ lat: "26", lon: "181" }),
    (error) => error.status === 400
  );
});


test("weather data is normalized correctly", () => {
  const result = normalizeWeather({
    current_weather: {
      temperature: 22,
      windspeed: 5,
      weathercode: 0,
      time: "2026-10-10T12:00",
    },
    current: {
      relative_humidity_2m: 60,
      precipitation: 0,
    },
  });

  assert.equal(result.temperature, 22);
  assert.equal(result.windspeed, 5);
  assert.equal(result.humidity, 60);
  assert.equal(result.precipitation, 0);
});


test("missing current weather is rejected", () => {
  assert.throws(
    () => normalizeWeather({}),
    (error) => error.status === 502
  );
});


test("clear, comfortable weather receives a Good rating", () => {
  const result = rateWeather({
    temperature: 22,
    windspeed: 5,
    precipitation: 0,
    humidity: 60,
    weathercode: 0,
  });

  assert.equal(result.score, 100);
  assert.equal(result.label, "Good");
});


test("severe weather penalties produce a Bad rating", () => {
  const result = rateWeather({
    temperature: 100,
    windspeed: 100,
    precipitation: 10,
    humidity: 100,
    weathercode: 99,
  });

  assert.equal(result.score, 0);
  assert.equal(result.label, "Bad");
});
