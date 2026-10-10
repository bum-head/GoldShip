from django.test import SimpleTestCase
from pages.climate_service import rate_weather


class RatingTests(SimpleTestCase):
    def test_calm_weather_is_good(self):
        r = rate_weather({"temperature": 22, "windspeed": 5, "precipitation": 0,
                          "humidity": 50, "weathercode": 0})
        self.assertEqual((r["score"], r["label"]), (100, "Good"))

    def test_halves_round_up_like_javascript(self):
        r = rate_weather({"temperature": 33, "windspeed": 18, "precipitation": 0.25,
                          "humidity": 90, "weathercode": 61})
        self.assertEqual((r["score"], r["label"]), (60, "Fair"))
