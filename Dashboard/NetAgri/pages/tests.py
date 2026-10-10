from django.test import TestCase
from django.urls import reverse

from .regions import NER_BOUNDS, NER_PLACES


class DashboardTests(TestCase):
    def test_home_renders_dashboard_with_region_data(self):
        r = self.client.get(reverse("home"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, 'id="ner-data"')
        self.assertContains(r, "Jorhat")

    def test_all_places_are_inside_ner_bounds(self):
        b = NER_BOUNDS
        for state, places in NER_PLACES.items():
            for name, lat, lon in places:
                self.assertTrue(b["south"] <= lat <= b["north"] and b["west"] <= lon <= b["east"], f"{name}, {state}")
