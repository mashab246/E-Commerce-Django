from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Cart, CartItem


def get_or_create_active_cart(user):
    if not user.is_authenticated:
        raise ValidationError("You must log in to use a cart.")

    cart, _ = Cart.objects.get_or_create(
        user=user,
        status=Cart.Status.ACTIVE,
    )
    return cart


def validate_sellable_product(product, variant=None):
    if product.status != "PUBLISHED":
        raise ValidationError("This product is not available for purchase.")

    if product.vendor.status != "APPROVED":
        raise ValidationError("This seller is not approved.")

    if variant is not None:
        if variant.product_id != product.pk:
            raise ValidationError(
                "The selected variant does not belong to this product."
            )

        if not variant.is_active:
            raise ValidationError("This product variant is unavailable.")

        available_stock = variant.stock_quantity
    else:
        available_stock = product.stock_quantity

    if available_stock < 1:
        raise ValidationError("This product is out of stock.")

    return available_stock


@transaction.atomic
def add_to_cart(user, product, quantity=1, variant=None):
    if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 1:
        raise ValidationError("Quantity must be a positive whole number.")

    available_stock = validate_sellable_product(product, variant)

    cart = get_or_create_active_cart(user)

    # Lock the cart row while updating its items.
    cart = Cart.objects.select_for_update().get(pk=cart.pk)

    item_filter = {
        "cart": cart,
        "product": product,
        "variant": variant,
    }

    item = CartItem.objects.filter(**item_filter).first()

    if item is not None:
        new_quantity = item.quantity + quantity

        if new_quantity > available_stock:
            raise ValidationError(
                f"Only {available_stock} unit(s) are currently available."
            )

        item.quantity = new_quantity
        item.full_clean()
        item.save(update_fields=["quantity", "updated_at"])

    else:
        if quantity > available_stock:
            raise ValidationError(
                f"Only {available_stock} unit(s) are currently available."
            )

        item = CartItem(
            **item_filter,
            quantity=quantity,
        )
        item.full_clean()
        item.save()

    return item


@transaction.atomic
def update_cart_item_quantity(user, item_id, quantity):
    if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity < 1:
        raise ValidationError("Quantity must be a positive whole number.")

    item = CartItem.objects.select_for_update().select_related(
        "cart",
        "product",
        "product__vendor",
        "variant",
    ).filter(
        pk=item_id,
        cart__user=user,
        cart__status=Cart.Status.ACTIVE,
    ).first()

    if item is None:
        raise ValidationError("Cart item not found.")

    available_stock = validate_sellable_product(
        item.product,
        item.variant,
    )

    if quantity > available_stock:
        raise ValidationError(
            f"Only {available_stock} unit(s) are currently available."
        )

    item.quantity = quantity
    item.full_clean()
    item.save(update_fields=["quantity", "updated_at"])

    return item


@transaction.atomic
def remove_from_cart(user, item_id):
    deleted_count, _ = CartItem.objects.filter(
        pk=item_id,
        cart__user=user,
        cart__status=Cart.Status.ACTIVE,
    ).delete()

    if deleted_count == 0:
        raise ValidationError("Cart item not found.")

    return True


def get_cart_subtotal(cart):
    subtotal = 0

    for item in cart.items.select_related(
        "product",
        "variant",
    ).all():
        if item.variant_id:
            price = item.variant.effective_price
        else:
            price = item.product.price

        subtotal += price * item.quantity

    return subtotal
