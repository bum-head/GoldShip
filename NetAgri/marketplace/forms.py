from django import forms
from .models import CropListing, Inquiry


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

class InquiryForm(forms.ModelForm):
    class Meta:
        model = Inquiry
        fields = ["quantity_kg", "message"]

    def __init__(self, *args, listing=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.listing = listing

    def clean_quantity_kg(self):
        qty = self.cleaned_data["quantity_kg"]
        if self.listing and qty > self.listing.quantity_kg:
            raise forms.ValidationError(f"Only {self.listing.quantity_kg} kg is available.")
        return qty
