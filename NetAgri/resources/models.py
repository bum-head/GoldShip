from django.db import models

from marketplace.models import Region


class StorageFacility(models.Model):
    TYPE_CHOICES = [("warehouse", "Warehouse"), ("cold", "Cold storage"), ("other", "Other")]

    name = models.CharField(max_length=150)
    storage_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="warehouse")
    region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name="storage_facilities")
    capacity_kg = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    contact = models.CharField(max_length=100)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "storage facilities"
        ordering = ["region", "name"]

    def __str__(self):
        return f"{self.name} ({self.region})"


class TransportOffer(models.Model):
    provider = models.CharField(max_length=150)
    origin = models.ForeignKey(Region, on_delete=models.PROTECT, related_name="transport_from")
    destination = models.ForeignKey(Region, on_delete=models.PROTECT, related_name="transport_to")
    vehicle_type = models.CharField(max_length=100)
    capacity_kg = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    available_from = models.DateField(null=True, blank=True)
    contact = models.CharField(max_length=100)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["origin", "destination"]

    def __str__(self):
        return f"{self.provider}: {self.origin} → {self.destination}"


class FarmingTip(models.Model):
    crop_name = models.CharField(max_length=100)
    region = models.ForeignKey(
        Region, on_delete=models.PROTECT, null=True, blank=True,
        help_text="Leave empty if the tip applies to every region.",
    )
    season = models.CharField(max_length=50, blank=True)
    content = models.TextField()
    source_url = models.URLField(help_text="Required: link to the ICAR, KVK or other source.")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["crop_name"]

    def __str__(self):
        return self.crop_name
