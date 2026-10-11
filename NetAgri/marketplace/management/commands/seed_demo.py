"""Fill the database with clearly-labelled demo data.

    python manage.py seed_demo              # create (refuses if demo data exists)
    python manage.py seed_demo --reset      # delete old demo data, then create
    python manage.py seed_demo --password X # choose the password for demo accounts

Everything created here is marked as demo: usernames start with "demo_", emails
use example.com, and storage, transport and tip records say "Demo". Prices,
quantities and contacts are invented. Do not present them as real.
"""
import random
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django.utils.crypto import get_random_string

from marketplace.models import CropListing, Inquiry, Region
from resources.models import FarmingTip, PestReport, StorageFacility, TransportOffer

User = get_user_model()

SOURCE_URL = "https://icar.org.in/"

# username, home region. demo_seller and demo_buyer are the two to log in with.
SELLERS = [
    ("demo_seller", "Jorhat"), ("demo_jorhat2", "Jorhat"), ("demo_tezpur", "Tezpur"),
    ("demo_dibrugarh", "Dibrugarh"), ("demo_guwahati", "Guwahati"), ("demo_silchar", "Silchar"),
    ("demo_shillong", "Shillong"), ("demo_shillong2", "Shillong"), ("demo_aizawl", "Aizawl"),
    ("demo_imphal", "Imphal"), ("demo_gangtok", "Gangtok"), ("demo_dimapur", "Dimapur"),
    ("demo_kohima", "Kohima"), ("demo_lakhimpur", "North Lakhimpur"),
]
BUYERS = ["demo_buyer", "demo_trader", "demo_retailer", "demo_processor"]

# crop, variety options, base price Rs/kg, quantity range kg, [(region, number of listings)]
CROPS = [
    ("Rice", ["Joha", "Boro", "Sali", "Ranjit"], 38, (500, 6000),
     [("Jorhat", 7), ("Tezpur", 5), ("Dibrugarh", 4), ("Silchar", 4), ("Guwahati", 3), ("Imphal", 3)]),
    ("Ginger", ["Local", "Nadia"], 80, (100, 1500),
     [("Shillong", 6), ("Aizawl", 5), ("Gangtok", 4), ("Kohima", 3)]),
    ("Turmeric", ["Lakadong", "Local"], 85, (100, 1200),
     [("Shillong", 5), ("Jorhat", 3), ("Aizawl", 3)]),
    ("King Chilli", ["Bhut Jolokia"], 260, (20, 300),
     [("Dimapur", 4), ("Kohima", 4), ("Jorhat", 3), ("Guwahati", 3)]),
    ("Pineapple", ["Queen", "Kew"], 28, (300, 4000),
     [("Tezpur", 4), ("Guwahati", 3), ("Aizawl", 3)]),
    ("Orange", ["Khasi mandarin"], 60, (200, 3000),
     [("Shillong", 4), ("Gangtok", 3), ("Dimapur", 3)]),
    ("Potato", ["Kufri Jyoti", "Local"], 24, (500, 8000),
     [("Shillong", 5), ("Guwahati", 4), ("Jorhat", 3), ("Tezpur", 3)]),
    ("Maize", ["Hybrid", "Local"], 22, (500, 5000),
     [("Imphal", 4), ("Dimapur", 3), ("Silchar", 3)]),
    ("Mustard", ["Toria", "Yellow sarson"], 64, (200, 2500),
     [("Jorhat", 4), ("Dibrugarh", 3), ("Tezpur", 3)]),
    ("Large Cardamom", ["Sikkim Bold"], 1050, (20, 250),
     [("Gangtok", 4), ("Kohima", 2)]),
    ("Banana", ["Malbhog", "Jahaji"], 30, (200, 3000),
     [("Guwahati", 3), ("Silchar", 3), ("Tezpur", 3)]),
    ("Lemon", ["Assam lemon"], 70, (50, 800),
     [("Guwahati", 4), ("Jorhat", 3), ("North Lakhimpur", 3)]),
    ("Tomato", ["Local"], 36, (100, 1500),
     [("Guwahati", 3), ("Aizawl", 3), ("Imphal", 3)]),
    ("Cabbage", ["Local"], 20, (200, 2500),
     [("Shillong", 3), ("Dimapur", 3), ("Aizawl", 2)]),
    ("Black Rice", ["Chakhao"], 160, (50, 600),
     [("Imphal", 5)]),
    ("Soybean", ["Local"], 52, (200, 2500),
     [("Dimapur", 3), ("Imphal", 2)]),
    ("Passion Fruit", ["Purple"], 110, (50, 700),
     [("Aizawl", 3), ("Kohima", 2)]),
    ("Kiwi", ["Hayward"], 220, (30, 400),
     [("Itanagar", 2), ("Kohima", 2)]),
    ("Areca Nut", ["Local"], 320, (100, 1200),
     [("Guwahati", 3), ("Tezpur", 2)]),
    ("Chayote", ["Local"], 26, (100, 1500),
     [("Gangtok", 3), ("Shillong", 2)]),
]

ROAD = {
    "Guwahati": "good", "Jorhat": "good", "Dibrugarh": "good", "Tezpur": "good", "Dimapur": "good",
    "Silchar": "fair", "Imphal": "fair", "Shillong": "fair", "Aizawl": "fair", "Kohima": "fair",
    "North Lakhimpur": "fair", "Gangtok": "poor", "Itanagar": "fair", "Tawang": "poor", "Ziro": "poor",
}
TERRAIN = {
    "Gangtok": "Mountain roads; landslides can close routes in the monsoon.",
    "Shillong": "Hill roads; fog and heavy rain slow transport in summer.",
    "Aizawl": "Hill roads with few alternative routes.",
    "Kohima": "Hill roads; seasonal landslides on the highway.",
    "Tawang": "High-altitude road; snow can close it in winter.",
    "Ziro": "Remote hill road, long travel times.",
}

STORAGE = [
    ("Demo Cold Storage, Guwahati", "cold", "Guwahati", 250000),
    ("Demo Warehouse, Jorhat", "warehouse", "Jorhat", 120000),
    ("Demo Warehouse, Tezpur", "warehouse", "Tezpur", 90000),
    ("Demo Cold Storage, Dibrugarh", "cold", "Dibrugarh", 80000),
    ("Demo Warehouse, Silchar", "warehouse", "Silchar", 100000),
    ("Demo Cold Storage, Shillong", "cold", "Shillong", 60000),
    ("Demo Warehouse, Imphal", "warehouse", "Imphal", 110000),
    ("Demo Warehouse, Dimapur", "warehouse", "Dimapur", 150000),
    ("Demo Cold Storage, Gangtok", "cold", "Gangtok", 30000),
    ("Demo Storage Shed, Aizawl", "other", "Aizawl", 25000),
    ("Demo Warehouse, Kohima", "warehouse", "Kohima", 45000),
    ("Demo Storage Shed, North Lakhimpur", "other", "North Lakhimpur", 35000),
]

TRANSPORT = [
    ("Jorhat", "Guwahati", "Truck, 9 tonne", 9000), ("Tezpur", "Guwahati", "Pickup, 1.5 tonne", 1500),
    ("Dibrugarh", "Guwahati", "Truck, 9 tonne", 9000), ("Silchar", "Guwahati", "Truck, 6 tonne", 6000),
    ("Shillong", "Guwahati", "Mini truck, 3 tonne", 3000), ("Imphal", "Dimapur", "Truck, 9 tonne", 9000),
    ("Dimapur", "Guwahati", "Truck, 12 tonne", 12000), ("Kohima", "Dimapur", "Pickup, 1.5 tonne", 1500),
    ("Aizawl", "Silchar", "Mini truck, 3 tonne", 3000), ("Gangtok", "Guwahati", "Mini truck, 3 tonne", 3000),
    ("North Lakhimpur", "Jorhat", "Pickup, 1.5 tonne", 1500), ("Jorhat", "Dibrugarh", "Truck, 6 tonne", 6000),
    ("Guwahati", "Shillong", "Mini truck, 3 tonne", 3000), ("Tezpur", "Jorhat", "Pickup, 1.5 tonne", 1500),
]

TIPS = [
    ("Rice", "Kharif", "Use certified seed of a variety recommended for your district. Ask your Krishi Vigyan Kendra (KVK) for the sowing window that suits your area."),
    ("Ginger", "Pre-monsoon", "Choose healthy, disease-free seed rhizomes and avoid plots where water stands. Ask your KVK how to treat seed rhizomes before planting."),
    ("Turmeric", "Pre-monsoon", "Plant in well-drained soil and do not replant on the same plot year after year. Check with your KVK for varieties suited to your region."),
    ("Potato", "Rabi", "Buy certified seed tubers and keep the harvest dry and shaded before storage. Your KVK can advise on local storage practices."),
    ("Orange", "Year-round", "Check trees regularly for pests and unusual leaf colour and report sightings on the Pest watch page. Confirm any treatment with your KVK first."),
    ("Maize", "Kharif", "Prepare drainage before the rains, because waterlogged fields hurt young plants. Ask your KVK for hybrids that suit your altitude."),
    ("Mustard", "Rabi", "Sow when soil moisture is adequate and keep records of the date and variety so you can compare seasons. Your KVK can confirm the best window."),
    ("Large Cardamom", "Year-round", "Shade trees and good drainage matter for large cardamom. Follow guidance from the Spices Board or your local horticulture office."),
    ("Pineapple", "Year-round", "Plant on sloping or well-drained land and use healthy planting material. Ask your horticulture office about recommended varieties."),
    ("Tomato", "Year-round", "Handle fruit gently and move it to market quickly, since damage during transport causes most losses. Ask your KVK about local crates and packing."),
]

PEST_SYMPTOMS = [
    ("Rice", "Jorhat", "Brown spots with grey centres on leaves, spreading after two days of rain. About a third of the field is affected."),
    ("Rice", "Jorhat", "Leaf tips turning yellow and drying, mostly near the field edge. Roughly 20 plants in one corner."),
    ("Rice", "Tezpur", "Many small insects on the lower stems and the plants look weak. Seen in two nearby fields."),
    ("Rice", "Dibrugarh", "White patches on leaves and the tillers are fewer than last season."),
    ("Ginger", "Shillong", "Lower leaves yellowing and the base of the stem is soft. Spreading along one row."),
    ("Ginger", "Aizawl", "Leaves rolling and drying from the edges. About 10 percent of plants."),
    ("Potato", "Shillong", "Dark water-soaked patches on leaves after fog and rain, a few stems collapsing."),
    ("Potato", "Guwahati", "Holes in leaves and small green caterpillars underneath. Found on most plants in one plot."),
    ("Orange", "Shillong", "Leaves curling with sticky residue on them and ants on the branches."),
    ("Orange", "Gangtok", "Fruit dropping early with small dark marks on the rind."),
    ("Tomato", "Guwahati", "Wilting of whole plants in the afternoon that does not recover by morning."),
    ("Maize", "Imphal", "Ragged holes in young leaves and sawdust-like droppings in the whorl."),
    ("King Chilli", "Dimapur", "Leaves curling upward and small white insects underneath. Fruit set looks poor."),
    ("Large Cardamom", "Gangtok", "Streaks on the leaves and stunted clumps. Several clumps affected in one garden."),
    ("Banana", "Silchar", "Yellowing of older leaves that then hang down around the stem. A few plants affected."),
    ("Mustard", "Jorhat", "Clusters of small insects on the flower stalks and the pods look shrivelled."),
]

MESSAGES = [
    "Is the quantity still available this week? I can arrange pickup.",
    "Can we agree on a price for the full quantity? Please let me know.",
    "I would like to buy a smaller lot first to check quality.",
    "Do you deliver, or should I send my own vehicle?",
    "We buy regularly. Can you supply every fortnight?",
    "Can you share when it was harvested?",
    "",
]


class Command(BaseCommand):
    help = "Create a large demo dataset (users, listings, inquiries, storage, transport, tips, pest reports)."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Delete existing demo data first.")
        parser.add_argument("--demo-site", action="store_true",
                            help="Allow running with DEBUG off. Only for a separate demo deployment.")
        parser.add_argument("--password", help="Password for all demo accounts (default: random, printed at the end).")

    def handle(self, *args, **opts):
        if not settings.DEBUG and not opts["demo_site"]:
            raise CommandError(
                "Refusing to create demo data while DEBUG is off, because this looks like a real "
                "deployment. On a separate demo site, add --demo-site.")
        demo_exists = User.objects.filter(username__startswith="demo_").exists()
        if demo_exists and not opts["reset"]:
            raise CommandError("Demo data already exists. Run with --reset to replace it.")

        call_command("seed_regions", verbosity=0)
        password = opts["password"] or get_random_string(10)
        rng = random.Random(2026)  # fixed seed: the same data every run

        with transaction.atomic():
            if opts["reset"]:
                self.wipe()
            self.set_road_info()
            sellers, buyers = self.make_users(password)
            listings = self.make_listings(rng, sellers)
            self.make_inquiries(rng, listings, sellers, buyers)
            self.make_resources()
            self.make_pests(rng, [u for u, _ in sellers] + buyers)

        self.stdout.write(self.style.SUCCESS("Demo data created."))
        self.stdout.write(f"  Users: {User.objects.filter(username__startswith='demo_').count()}")
        self.stdout.write(f"  Listings: {CropListing.objects.filter(seller__username__startswith='demo_').count()}")
        self.stdout.write(f"  Inquiries: {Inquiry.objects.filter(buyer__username__startswith='demo_').count()}")
        self.stdout.write(f"  Storage: {StorageFacility.objects.filter(name__startswith='Demo ').count()}, "
                          f"transport: {TransportOffer.objects.filter(provider__startswith='Demo ').count()}, "
                          f"tips: {FarmingTip.objects.filter(content__startswith='[Demo]').count()}, "
                          f"pest reports: {PestReport.objects.filter(reporter__username__startswith='demo_').count()}")
        self.stdout.write("")
        self.stdout.write("Log in as demo_seller or demo_buyer (all demo accounts share one password):")
        self.stdout.write(self.style.WARNING(f"  password: {password}"))
        self.stdout.write("Do not use this on a public server.")

    # ----- helpers -----

    def wipe(self):
        # Deleting the users also deletes their listings, inquiries and pest reports.
        User.objects.filter(username__startswith="demo_").delete()
        StorageFacility.objects.filter(name__startswith="Demo ").delete()
        TransportOffer.objects.filter(provider__startswith="Demo ").delete()
        FarmingTip.objects.filter(content__startswith="[Demo]").delete()

    def region(self, name):
        r = Region.objects.filter(name=name).first()
        if r is None:
            raise CommandError(f"Region {name!r} not found. Did seed_regions run?")
        return r

    def set_road_info(self):
        for name, road in ROAD.items():
            Region.objects.filter(name=name, road_access="unknown").update(
                road_access=road, terrain_note=TERRAIN.get(name, ""))

    def make_users(self, password):
        def make(username):
            user, _ = User.objects.get_or_create(username=username, defaults={"email": f"{username}@example.com"})
            user.set_password(password)
            user.email = f"{username}@example.com"
            user.save()
            return user
        sellers = [(make(u), self.region(r)) for u, r in SELLERS]
        buyers = [make(u) for u in BUYERS]
        return sellers, buyers

    def make_listings(self, rng, sellers):
        by_region = {}
        for user, region in sellers:
            by_region.setdefault(region.name, []).append(user)
        listings = []
        for crop, varieties, base, (qmin, qmax), spots in CROPS:
            for region_name, count in spots:
                region = self.region(region_name)
                owners = by_region.get(region_name) or [u for u, _ in sellers]
                for i in range(count):
                    # Spread prices around the base so some listings are above, some below the median.
                    factor = rng.choice([0.75, 0.85, 0.92, 1.0, 1.0, 1.05, 1.12, 1.25, 1.4])
                    price = Decimal(str(round(base * factor, 2))).quantize(Decimal("0.01"))
                    qty = Decimal(rng.randrange(qmin, qmax + 1, 10)).quantize(Decimal("0.01"))
                    owner = owners[0] if (region_name == "Jorhat" and i % 2 == 0) else rng.choice(owners)
                    listings.append(CropListing.objects.create(
                        seller=owner, region=region, crop_name=crop,
                        variety=rng.choice(varieties), quantity_kg=qty, price_per_kg=price,
                        status="sold" if rng.random() < 0.10 else "active",
                    ))
        # Spread the creation times over the last three weeks so the list looks lived in.
        now = timezone.now()
        for listing in listings:
            CropListing.objects.filter(pk=listing.pk).update(
                created_at=now - timedelta(hours=rng.randrange(1, 24 * 21)))
        return listings

    def make_inquiries(self, rng, listings, sellers, buyers):
        demo_seller = next(u for u, _ in sellers if u.username == "demo_seller")
        demo_buyer = next(b for b in buyers if b.username == "demo_buyer")
        active = [l for l in listings if l.status == "active"]

        def add(buyer, listing, status, qty_share=None):
            if listing.seller_id == buyer.id:
                return
            share = qty_share or rng.choice([0.1, 0.2, 0.3, 0.5])
            qty = max(Decimal("1"), (listing.quantity_kg * Decimal(str(share))).quantize(Decimal("1")))
            inquiry = Inquiry.objects.create(
                buyer=buyer, listing=listing, quantity_kg=qty,
                message=rng.choice(MESSAGES), status=status)
            Inquiry.objects.filter(pk=inquiry.pk).update(
                created_at=timezone.now() - timedelta(hours=rng.randrange(1, 24 * 10)))

        # A guaranteed story for the live demo: demo_buyer writes to demo_seller.
        mine = [l for l in active if l.seller_id == demo_seller.id]
        for listing, status in zip(mine, ["accepted", "accepted", "pending", "pending", "declined"]):
            add(demo_buyer, listing, status)
        # demo_seller also buys from someone else, so Inquiries shows both directions.
        others = [l for l in active if l.seller_id != demo_seller.id]
        for listing, status in zip(rng.sample(others, 3), ["accepted", "pending", "pending"]):
            add(demo_seller, listing, status)
        # Plenty of background activity.
        for _ in range(35):
            add(rng.choice(buyers), rng.choice(active),
                rng.choice(["pending", "pending", "accepted", "declined"]))

    def make_resources(self):
        for name, kind, region_name, cap in STORAGE:
            StorageFacility.objects.create(
                name=name, storage_type=kind, region=self.region(region_name),
                capacity_kg=Decimal(cap), contact="demo-contact@example.com",
                notes="Demo record. Not a real facility.")
        for i, (origin, dest, vehicle, cap) in enumerate(TRANSPORT):
            TransportOffer.objects.create(
                provider=f"Demo Transporter {i + 1}", origin=self.region(origin),
                destination=self.region(dest), vehicle_type=vehicle, capacity_kg=Decimal(cap),
                available_from=timezone.localdate() + timedelta(days=(i % 6) + 1),
                contact="demo-contact@example.com", notes="Demo record. Not a real offer.")
        for crop, season, text in TIPS:
            FarmingTip.objects.create(
                crop_name=crop, season=season, source_url=SOURCE_URL,
                content=f"[Demo] {text}")

    def make_pests(self, rng, users):
        today = timezone.localdate()
        for i, (crop, region_name, symptoms) in enumerate(PEST_SYMPTOMS):
            reviewed = i % 3 != 0  # about two thirds reviewed, the rest pending
            report = PestReport(
                reporter=rng.choice(users), region=self.region(region_name), crop_name=crop,
                observed_on=today - timedelta(days=rng.randrange(0, 27)), symptoms=symptoms,
                status="reviewed" if reviewed else "pending")
            if reviewed:
                report.advisory = ("[Demo] Have the pest or disease identified by your local KVK or "
                                   "agriculture office before using any treatment. Remove badly "
                                   "affected plants and keep tools clean to limit spread.")
                report.source_url = SOURCE_URL
            report.save()
