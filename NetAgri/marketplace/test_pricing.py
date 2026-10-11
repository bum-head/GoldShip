from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import CropListing, Inquiry, Region
from .pricing import price_context


class PricingTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user("price1", password="pw")
        self.buyer = User.objects.create_user("price2", password="pw")
        self.jorhat = Region.objects.create(name="Jorhat", state="Assam")
        self.tezpur = Region.objects.create(name="Tezpur", state="Assam")

    def listing(self, price, region=None, crop="Rice", qty=10, status="active"):
        return CropListing.objects.create(
            seller=self.user, region=region or self.jorhat, crop_name=crop,
            quantity_kg=Decimal(qty), price_per_kg=Decimal(price), status=status,
        )

    def test_none_without_enough_comparables(self):
        target = self.listing("20")
        self.listing("10")
        self.listing("12")
        self.assertIsNone(price_context(target))

    def test_local_median_and_verdict(self):
        target = self.listing("30")
        for p in ("10", "20", "30"):
            self.listing(p)
        ctx = price_context(target)
        self.assertEqual(ctx["scope"], "Jorhat")
        self.assertEqual(ctx["median"], Decimal("20"))
        self.assertEqual(ctx["verdict"], "50% above")

    def test_below_median(self):
        target = self.listing("10")
        for p in ("20", "20", "20"):
            self.listing(p)
        self.assertEqual(price_context(target)["verdict"], "50% below")

    def test_within_ten_percent_is_in_line(self):
        target = self.listing("21")
        for p in ("20", "20", "20"):
            self.listing(p)
        self.assertEqual(price_context(target)["verdict"], "in line with")

    def test_falls_back_to_all_regions(self):
        target = self.listing("20")
        for p in ("10", "20", "30"):
            self.listing(p, region=self.tezpur)
        ctx = price_context(target)
        self.assertEqual(ctx["scope"], "all regions")
        self.assertEqual(ctx["n"], 3)

    def test_crop_name_match_ignores_case(self):
        target = self.listing("20", crop="Rice")
        for p in ("20", "20", "20"):
            self.listing(p, crop="rice")
        self.assertIsNotNone(price_context(target))

    def test_other_crops_are_ignored(self):
        target = self.listing("20", crop="Rice")
        for p in ("20", "20", "20"):
            self.listing(p, crop="Tea")
        self.assertIsNone(price_context(target))

    def test_inquiry_total_value(self):
        listing = self.listing("5")
        inquiry = Inquiry.objects.create(buyer=self.buyer, listing=listing, quantity_kg=Decimal("4"))
        self.assertEqual(inquiry.total_value, Decimal("20"))

    def test_my_listings_totals(self):
        active = self.listing("5", qty="10")        # 50
        self.listing("5", qty="10", status="sold")  # ignored
        Inquiry.objects.create(buyer=self.buyer, listing=active, quantity_kg=Decimal("4"), status="accepted")  # 20
        Inquiry.objects.create(buyer=self.buyer, listing=active, quantity_kg=Decimal("2"))                      # pending, ignored
        self.client.login(username="price1", password="pw")
        r = self.client.get(reverse("marketplace:my_listings"))
        self.assertEqual(r.context["active_value"], Decimal("50"))
        self.assertEqual(r.context["accepted_value"], Decimal("20"))

    def test_listing_page_shows_price_check(self):
        target = self.listing("30")
        for p in ("10", "20", "30"):
            self.listing(p)
        r = self.client.get(reverse("marketplace:listing_detail", args=[target.pk]))
        self.assertContains(r, "50% above")
