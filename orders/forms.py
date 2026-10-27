from django import forms
from .models import Order

class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            "shipping_full_name",
            "shipping_phone",
            "shipping_address",
            "shipping_city",
            "shipping_region",
            "shipping_postal_code",
            "shipping_country",
            "payment_method",
            "customer_note",
        ]

        widgets = {
            "shipping_full_name": forms.TextInput(
                attrs={
                    "placeholder": "Full name",
                    "autocomplete": "name",
                }
            ),
            "shipping_phone": forms.TextInput(
                attrs={
                    "placeholder": "e.g. +256 7XX XXX XXX",
                    "autocomplete": "tel",
                }
            ),
            "shipping_address": forms.Textarea(
                attrs={
                    "placeholder": "Street, building, village or detailed delivery location",
                    "rows": 3,
                    "autocomplete": "street-address",
                }
            ),
            "shipping_city": forms.TextInput(
                attrs={
                    "placeholder": "Town or city",
                    "autocomplete": "address-level2",
                }
            ),
            "shipping_region": forms.TextInput(
                attrs={
                    "placeholder": "District or region",
                    "autocomplete": "address-level1",
                }
            ),
            "shipping_postal_code": forms.TextInput(
                attrs={
                    "placeholder": "Postal code (if applicable)",
                    "autocomplete": "postal-code",
                }
            ),
            "shipping_country": forms.TextInput(
                attrs={
                    "autocomplete": "country-name",
                }
            ),
            "payment_method": forms.Select(),
            "customer_note": forms.Textarea(
                attrs={
                    "placeholder": "Optional delivery instructions",
                    "rows": 3,
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["shipping_country"].initial = "Uganda"

        self.fields["shipping_region"].required = False
        self.fields["shipping_postal_code"].required = False
        self.fields["customer_note"].required = False

        self.fields["payment_method"].choices = [
            choice
            for choice in Order.PaymentMethod.choices
            if choice[0] in {
                Order.PaymentMethod.CASH_ON_DELIVERY,
                Order.PaymentMethod.MOBILE_MONEY,
            }
        ]

        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")
