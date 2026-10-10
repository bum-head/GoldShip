from django import forms
from .models import CropListing


class CropListingForm(forms.ModelForm):
    class Meta:
        model = CropListing

        fields = [
            "crop_name",
            "variety",
            "region",
            "quantity_kg",
            "price_per_kg",
        ]
