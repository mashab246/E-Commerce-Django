
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F

from carts.models import Cart, CartItem
from products.models import InventoryMovement, Product, ProductVariant
from vendors.models import Vendor

from .models import Order, OrderItem, VendorOrder


def money(value, field_name):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError(f"{field_name} must be a valid amount.")

    if not amount.is_finite() or amount < 0:
        raise ValidationError(
            f"{field_name} must be a non-negative amount."
        )

    return amount.quantize(Decimal("0.01"))


@transaction.atomic
def checkout_cart(
    user,
    shipping_details,
    payment_method=Order.PaymentMethod.CASH_ON_DELIVERY,
    customer_note="",
    shipping_cost_per_vendor=Decimal("0.00"),
    tax_amount=Decimal("0.00"),
):
    if not user.is_authenticated:
        raise ValidationError("You must log in before checking out.")

    if not isinstance(shipping_details, dict):
        raise ValidationError("Shipping details must be provided.")

    required_fields = ("full_name", "phone", "address", "city")

    for field in required_fields:
        if not str(shipping_details.get(field, "")).strip():
            raise ValidationError(
                f"Shipping detail '{field}' is required."
            )

    valid_payment_methods = {
        choice[0] for choice in Order.PaymentMethod.choices
    }
    if payment_method not in valid_payment_methods:
        raise ValidationError("Invalid payment method.")

    shipping_per_vendor = money(
        shipping_cost_per_vendor, "Shipping cost"
    )
    tax = money(tax_amount, "Tax amount")

    cart = (
        Cart.objects.select_for_update()
        .filter(user=user, status=Cart.Status.ACTIVE)
        .first()
    )

    if cart is None:
        raise ValidationError("You do not have an active cart.")

    items = list(
        CartItem.objects.filter(cart=cart)
        .select_related("product", "variant")
        .order_by("id")
    )

    if not items:
        raise ValidationError("Your cart is empty.")

    # Lock stock records and validate every item before changing stock.
    lines = []
    vendor_totals = {}

    for cart_item in items:
        product = (
            Product.objects.select_for_update()
            .select_related("vendor")
            .get(pk=cart_item.product_id)
        )

        vendor = product.vendor

        if product.status != Product.Status.PUBLISHED:
            raise ValidationError(
                f"'{product.name}' is no longer available."
            )

        if vendor.status != Vendor.Status.APPROVED:
            raise ValidationError(
                f"'{vendor.store_name}' is not currently approved."
            )

        variant = None

        if cart_item.variant_id:
            variant = (
                ProductVariant.objects.select_for_update()
                .get(pk=cart_item.variant_id)
            )

            if variant.product_id != product.pk:
                raise ValidationError(
                    "A cart variant does not belong to its product."
                )

            if not variant.is_active:
                raise ValidationError(
                    f"Variant '{variant.name}' is inactive."
                )

            available_stock = variant.stock_quantity
            unit_price = variant.effective_price
            sku = variant.sku
        else:
            available_stock = product.stock_quantity
            unit_price = product.price
            sku = product.sku

        if cart_item.quantity < 1:
            raise ValidationError("Cart quantities must be positive.")

        if cart_item.quantity > available_stock:
            raise ValidationError(
                f"Insufficient stock for '{product.name}'. "
                f"Available: {available_stock}; "
                f"requested: {cart_item.quantity}."
            )

        unit_price = money(unit_price, "Product price")
        line_total = unit_price * cart_item.quantity

        lines.append({
            "cart_item": cart_item,
            "product": product,
            "variant": variant,
            "vendor": vendor,
            "unit_price": unit_price,
            "line_total": line_total,
            "sku": sku,
        })

        vendor_totals[vendor.pk] = (
            vendor_totals.get(vendor.pk, Decimal("0.00"))
            + line_total
        )

    subtotal = sum(
        (line["line_total"] for line in lines),
        Decimal("0.00"),
    )

    shipping_total = shipping_per_vendor * len(vendor_totals)
    total_amount = subtotal + shipping_total + tax

    order = Order.objects.create(
        customer=user,
        payment_method=payment_method,
        shipping_full_name=shipping_details["full_name"].strip(),
        shipping_phone=shipping_details["phone"].strip(),
        shipping_address=shipping_details["address"].strip(),
        shipping_city=shipping_details["city"].strip(),
        shipping_region=shipping_details.get("region", "").strip(),
        shipping_postal_code=shipping_details.get(
            "postal_code", ""
        ).strip(),
        shipping_country=shipping_details.get(
            "country", "Uganda"
        ).strip() or "Uganda",
        customer_note=customer_note,
        subtotal=subtotal,
        shipping_cost=shipping_total,
        tax_amount=tax,
        total_amount=total_amount,
    )

    vendor_orders = {}

    for vendor_id, vendor_subtotal in vendor_totals.items():
        vendor = Vendor.objects.get(pk=vendor_id)

        vendor_orders[vendor_id] = VendorOrder.objects.create(
            order=order,
            vendor=vendor,
            subtotal=vendor_subtotal,
            shipping_cost=shipping_per_vendor,
            total_amount=vendor_subtotal + shipping_per_vendor,
        )

    # Deduct inventory and create purchase-time snapshots.
    for line in lines:
        product = line["product"]
        variant = line["variant"]
        quantity = line["cart_item"].quantity

        if variant is not None:
            ProductVariant.objects.filter(pk=variant.pk).update(
                stock_quantity=F("stock_quantity") - quantity
            )

            InventoryMovement.objects.create(
                variant=variant,
                movement_type=InventoryMovement.MovementType.OUT,
                quantity=quantity,
                note=f"Order {order.order_number}",
                created_by=user,
            )
        else:
            Product.objects.filter(pk=product.pk).update(
                stock_quantity=F("stock_quantity") - quantity
            )

        product_name = product.name
        if variant is not None:
            product_name = f"{product.name} - {variant.name}"

        OrderItem.objects.create(
            vendor_order=vendor_orders[line["vendor"].pk],
            product=product,
            variant=variant,
            product_name=product_name,
            sku=line["sku"],
            vendor_store_name=line["vendor"].store_name,
            unit_price=line["unit_price"],
            quantity=quantity,
            line_total=line["line_total"],
        )

    cart.status = Cart.Status.CONVERTED
    cart.save(update_fields=["status", "updated_at"])

    return order
