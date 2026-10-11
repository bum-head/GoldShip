from django import forms
from django.utils import timezone

from .models import PestReport


class PestReportForm(forms.ModelForm):
    class Meta:
        model = PestReport
        fields = ["crop_name", "region", "observed_on", "symptoms"]
        widgets = {"observed_on": forms.DateInput(attrs={"type": "date"})}

    def clean_crop_name(self):
        return self.cleaned_data["crop_name"].strip().title()

    def clean_observed_on(self):
        day = self.cleaned_data["observed_on"]
        if day > timezone.localdate():
            raise forms.ValidationError("The date cannot be in the future.")
        return day
