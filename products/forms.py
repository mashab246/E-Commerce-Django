from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "category",
            "brand",
            "name",
            "sku",
            "description",
            "price",
            "stock_quantity",
            "status",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
            "price": forms.NumberInput(attrs={"min": "0.01", "step": "0.01"}),
            "stock_quantity": forms.NumberInput(attrs={"min": 0, "step": 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["category"].queryset = (
            self.fields["category"].queryset.filter(is_active=True)
        )
        self.fields["brand"].queryset = (
            self.fields["brand"].queryset.filter(is_active=True)
        )
        self.fields["brand"].required = False
