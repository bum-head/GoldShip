from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Region(models.Model):
    name = models.CharField(max_length=100)
    district = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, default="Assam")
    latitude = models.DecimalField(max_digits=8, decimal_places=5, null=True, blank=True)
    longitude = models.DecimalField(max_digits=8, decimal_places=5, null=True, blank=True)

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
