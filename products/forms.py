from django import forms
from .models import Product, Category


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        if not data:
            return []

        if isinstance(data, (list, tuple)):
            return [
                super(MultipleFileField, self).clean(file, initial)
                for file in data
            ]

        return [super().clean(data, initial)]


class ProductForm(forms.ModelForm):
    images = MultipleFileField(
        required=False,
        widget=MultipleFileInput(attrs={
            "accept": "image/*",
        }),
        help_text="You can select multiple product images.",
    )

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


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = [
            "name",
            "description",
            "parent",
        ]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "placeholder": "Enter category name",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Describe this category (optional)",
                }
            ),
            "parent": forms.Select(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["parent"].required = False
        self.fields["parent"].empty_label = "Main category (no parent)"

    def clean_parent(self):
        parent = self.cleaned_data.get("parent")

        if not parent:
            return parent

        if self.instance.pk:
            if parent.pk == self.instance.pk:
                raise forms.ValidationError(
                    "A category cannot be its own parent."
                )

            descendant_ids = set()
            pending = [self.instance]

            while pending:
                current = pending.pop()

                children = Category.objects.filter(parent=current)

                for child in children:
                    if child.pk not in descendant_ids:
                        descendant_ids.add(child.pk)
                        pending.append(child)

            if parent.pk in descendant_ids:
                raise forms.ValidationError(
                    "A category cannot have one of its descendants as its parent."
                )

        return parent

