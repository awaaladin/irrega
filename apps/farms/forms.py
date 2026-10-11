from django import forms

from .models import Farm, Field, YieldRecord

BASE = {"class": "input"}


class FarmForm(forms.ModelForm):
    class Meta:
        model = Farm
        fields = ["name", "latitude", "longitude"]
        widgets = {
            "name": forms.TextInput(attrs={**BASE, "placeholder": "e.g. Etim's farm, Calabar South"}),
            "latitude": forms.NumberInput(attrs={**BASE, "step": "any", "inputmode": "decimal"}),
            "longitude": forms.NumberInput(attrs={**BASE, "step": "any", "inputmode": "decimal"}),
        }

    def clean_latitude(self):
        v = self.cleaned_data["latitude"]
        if not -90 <= v <= 90:
            raise forms.ValidationError("Latitude must be between -90 and 90.")
        return v

    def clean_longitude(self):
        v = self.cleaned_data["longitude"]
        if not -180 <= v <= 180:
            raise forms.ValidationError("Longitude must be between -180 and 180.")
        return v


class FieldForm(forms.ModelForm):
    class Meta:
        model = Field
        fields = ["name", "crop", "area_ha", "soil", "planting_date", "method"]
        widgets = {
            "name": forms.TextInput(attrs={**BASE, "placeholder": "e.g. Cassava, lower plot"}),
            "crop": forms.RadioSelect,
            "area_ha": forms.NumberInput(attrs={**BASE, "step": "0.001", "min": "0.001", "inputmode": "decimal"}),
            "soil": forms.Select(attrs={"class": "select"}),
            "planting_date": forms.DateInput(attrs={**BASE, "type": "date"}),
            "method": forms.Select(attrs={"class": "select"}),
        }
        labels = {"area_ha": "Size (hectares)", "method": "How do you water?", "soil": "Soil type"}
        help_texts = {"area_ha": "1 hectare = 10,000 m². A plot of 50 x 100 ft is about 0.046 ha."}

    def clean_area_ha(self):
        v = self.cleaned_data["area_ha"]
        if v <= 0 or v > 1000:
            raise forms.ValidationError("Enter a size between 0.001 and 1000 hectares.")
        return v

    def clean_planting_date(self):
        from datetime import date, timedelta

        d = self.cleaned_data["planting_date"]
        if d > date.today() + timedelta(days=60):
            raise forms.ValidationError("That planting date is too far in the future.")
        return d


class YieldForm(forms.ModelForm):
    class Meta:
        model = YieldRecord
        fields = ["season", "amount_kg", "dry_spell"]
        widgets = {
            "season": forms.TextInput(attrs={**BASE, "placeholder": "e.g. 2025 rainy season"}),
            "amount_kg": forms.NumberInput(attrs={**BASE, "step": "any", "min": "0"}),
            "dry_spell": forms.CheckboxInput(attrs={"class": "h-5 w-5 rounded border-line bg-sunken text-water"}),
        }
        labels = {"amount_kg": "Harvest (kg)", "dry_spell": "A long dry spell hurt this harvest"}
