from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q


class Cart(models.Model):

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        CONVERTED = "CONVERTED", "Converted to order"
        ABANDONED = "ABANDONED", "Abandoned"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="carts",
    )

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(status="ACTIVE"),
                name="unique_active_cart_per_user",
            ),
        ]

    def __str__(self):
        return f"Cart #{self.pk} - {self.user}"


class CartItem(models.Model):
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items",
    )

    product = models.ForeignKey(
        "products.Product",
        on_delete=models.PROTECT,
        related_name="cart_items",
    )

    variant = models.ForeignKey(
        "products.ProductVariant",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="cart_items",
    )

    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
    )

    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["added_at"]
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gte=1),
                name="cart_item_quantity_at_least_one",
            ),
            models.UniqueConstraint(
                fields=["cart", "product"],
                condition=Q(variant__isnull=True),
                name="unique_simple_product_per_cart",
            ),
            models.UniqueConstraint(
                fields=["cart", "variant"],
                condition=Q(variant__isnull=False),
                name="unique_variant_per_cart",
            ),
        ]

    def clean(self):
        super().clean()

        if self.variant_id and self.product_id:
            if self.variant.product_id != self.product_id:
                raise ValidationError({
                    "variant": (
                        "The selected variant must belong "
                        "to the selected product."
                    )
                })

    def __str__(self):
        item_name = (
            self.variant.name
            if self.variant_id
            else self.product.name
        )
        return f"{item_name} x {self.quantity}"
