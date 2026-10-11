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

from .models import Inquiry


class InquiryTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.seller = User.objects.create_user("seller", password="pw")
        self.buyer = User.objects.create_user("buyer", password="pw")
        region = Region.objects.create(name="Jorhat", state="Assam")
        self.listing = CropListing.objects.create(
            seller=self.seller, region=region, crop_name="Tea",
            quantity_kg=10, price_per_kg=5,
        )
        self.url = reverse("marketplace:create_inquiry", args=[self.listing.pk])

    def test_buyer_can_send_inquiry(self):
        self.client.login(username="buyer", password="pw")
        r = self.client.post(self.url, {"quantity_kg": "4", "message": "hi"})
        self.assertRedirects(r, reverse("marketplace:inquiry_list"), fetch_redirect_response=False)
        self.assertEqual(Inquiry.objects.count(), 1)

    def test_cannot_ask_for_more_than_available(self):
        self.client.login(username="buyer", password="pw")
        self.client.post(self.url, {"quantity_kg": "50", "message": ""})
        self.assertEqual(Inquiry.objects.count(), 0)

    def test_seller_cannot_inquire_on_own_listing(self):
        self.client.login(username="seller", password="pw")
        self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_only_the_seller_can_respond(self):
        inq = Inquiry.objects.create(buyer=self.buyer, listing=self.listing, quantity_kg=4)
        respond = reverse("marketplace:respond_to_inquiry", args=[inq.pk])

        self.client.login(username="buyer", password="pw")
        self.assertEqual(self.client.post(respond, {"status": "accepted"}).status_code, 404)
        inq.refresh_from_db()
        self.assertEqual(inq.status, "pending")

        self.client.login(username="seller", password="pw")
        self.client.post(respond, {"status": "accepted"})
        inq.refresh_from_db()
        self.assertEqual(inq.status, "accepted")


class SellerManagementTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.seller = User.objects.create_user("seller2", password="pw")
        self.other = User.objects.create_user("other2", password="pw")
        region = Region.objects.create(name="Tezpur", state="Assam")
        self.listing = CropListing.objects.create(
            seller=self.seller, region=region, crop_name="Rice",
            quantity_kg=10, price_per_kg=5,
        )
        self.sold_url = reverse("marketplace:mark_sold", args=[self.listing.pk])

    def test_other_user_cannot_mark_sold(self):
        self.client.login(username="other2", password="pw")
        self.assertEqual(self.client.post(self.sold_url).status_code, 404)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.status, "active")

    def test_seller_can_mark_sold_and_it_leaves_the_marketplace(self):
        self.client.login(username="seller2", password="pw")
        self.client.post(self.sold_url)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.status, "sold")
        r = self.client.get(reverse("marketplace:crop_list"))
        self.assertEqual(len(r.context["listings"]), 0)

    def test_mark_sold_rejects_get(self):
        self.client.login(username="seller2", password="pw")
        self.assertEqual(self.client.get(self.sold_url).status_code, 405)


from resources.models import StorageFacility

from .geo import haversine_km


class LogisticsTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.seller = User.objects.create_user("seller3", password="pw")
        self.jorhat = Region.objects.create(name="Jorhat", state="Assam", latitude=26.7509, longitude=94.2037)
        self.majuli = Region.objects.create(name="Majuli", state="Assam", latitude=26.95, longitude=94.1667)
        self.aizawl = Region.objects.create(name="Aizawl", state="Mizoram", latitude=23.7271, longitude=92.7176)
        self.listing = CropListing.objects.create(
            seller=self.seller, region=self.jorhat, crop_name="Tea", quantity_kg=10, price_per_kg=5)
        for name, region in [("Far store", self.aizawl), ("Near store", self.majuli), ("Local store", self.jorhat)]:
            StorageFacility.objects.create(name=name, region=region, contact="123")

    def test_distance_is_sensible(self):
        d = haversine_km(26.1445, 91.7362, 26.7509, 94.2037)  # Guwahati to Jorhat
        self.assertTrue(240 < d < 270)

    def test_storage_sorted_by_distance_and_far_ones_hidden(self):
        r = self.client.get(reverse("marketplace:listing_detail", args=[self.listing.pk]))
        self.assertEqual([row["item"].name for row in r.context["storage"]], ["Local store", "Near store"])

    def test_sold_listing_hidden_from_others_but_not_owner(self):
        self.listing.status = "sold"
        self.listing.save()
        url = reverse("marketplace:listing_detail", args=[self.listing.pk])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.client.login(username="seller3", password="pw")
        self.assertEqual(self.client.get(url).status_code, 200)
