from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Region(models.Model):
    name = models.CharField(max_length=100)
    district = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, default="Assam")
    latitude = models.DecimalField(max_digits=8, decimal_places=5, null=True, blank=True)
    longitude = models.DecimalField(max_digits=8, decimal_places=5, null=True, blank=True)

    ROAD_CHOICES = [
        ("unknown", "Not assessed"),
        ("good", "Good road access"),
        ("fair", "Fair, some seasonal disruption"),
        ("poor", "Poor or remote"),
    ]
    road_access = models.CharField(max_length=10, choices=ROAD_CHOICES, default="unknown")
    terrain_note = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["state", "name"]

    def __str__(self):
        place = self.district or self.state
        return f"{self.name}, {place}"

class CropListing(models.Model):
    STATUS_CHOICES = [
        ("active", "Available"),
        ("sold", "Sold"),
    ]

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="crop_listings",
    )

    region = models.ForeignKey(
        Region,
        on_delete=models.PROTECT,
        related_name="crop_listings",
    )

    crop_name = models.CharField(max_length=100)
    variety = models.CharField(max_length=100, blank=True)

    quantity_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )

    price_per_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="active",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.crop_name} - {self.region}"

    @property
    def stock_value(self):
        return self.quantity_kg * self.price_per_kg

class Inquiry(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("declined", "Declined"),
    ]

    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_inquiries",
    )
    listing = models.ForeignKey(
        CropListing,
        on_delete=models.CASCADE,
        related_name="inquiries",
    )
    quantity_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
    )
    message = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.buyer} → {self.listing.crop_name} ({self.status})"

    @property
    def total_value(self):
        return self.quantity_kg * self.listing.price_per_kg
