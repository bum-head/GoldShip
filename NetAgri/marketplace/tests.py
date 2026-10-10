from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import CropListing, Region


class RegionFilterTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user("farmer", password="pw")
        self.jorhat = Region.objects.create(name="Jorhat", state="Assam")
        self.tezpur = Region.objects.create(name="Tezpur", state="Assam")
        for crop, region in [("Tea", self.jorhat), ("Rice", self.tezpur)]:
            CropListing.objects.create(
                seller=user, region=region, crop_name=crop,
                quantity_kg=10, price_per_kg=5,
            )

    def test_filter_by_region(self):
        r = self.client.get(reverse("marketplace:crop_list"), {"region": self.jorhat.pk})
        self.assertEqual([l.crop_name for l in r.context["listings"]], ["Tea"])

    def test_bad_region_value_is_ignored(self):
        r = self.client.get(reverse("marketplace:crop_list"), {"region": "abc"})
        self.assertEqual(len(r.context["listings"]), 2)
