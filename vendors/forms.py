from django import forms
from .models import Vendor


class VendorRegistrationForm(forms.ModelForm):

    class Meta:
        model = Vendor

        fields = [
            "store_name",
            "description",
            "phone_number",
            "business_address",
        ]

        widgets = {
            "store_name": forms.TextInput(
                attrs={
                    "placeholder": "Enter your store name",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "placeholder": "Tell customers about your store",
                    "rows": 4,
                }
            ),
            "phone_number": forms.TextInput(
                attrs={
                    "placeholder": "+256 7XX XXX XXX",
                }
            ),
            "business_address": forms.Textarea(
                attrs={
                    "placeholder": "Enter your business location",
                    "rows": 3,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.widget.attrs["class"] = "form-control"

        self.fields["description"].required = False
        self.fields["phone_number"].required = False
        self.fields["business_address"].required = False
