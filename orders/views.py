from collections import defaultdict
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.views.decorators.http import require_http_methods
from carts.models import Cart, CartItem
from products.models import Product, ProductVariant
from .forms import CheckoutForm
from .models import Order, OrderItem, VendorOrder
from django.shortcuts import get_object_or_404, redirect, render


@login_required
@require_http_methods(["GET", "POST"])
def checkout(request):
    cart = Cart.objects.filter(
        user=request.user,
        status=Cart.Status.ACTIVE,
    ).first()

    if cart is None or not cart.items.exists():
        messages.info(request, "Your cart is empty. Add products before checkout.")
        return redirect("cart:cart_detail")

    if request.method == "POST":
        form = CheckoutForm(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():
                    # Lock the active cart and its items during checkout.
                    locked_cart = Cart.objects.select_for_update().get(
                        pk=cart.pk,
                        user=request.user,
                        status=Cart.Status.ACTIVE,
                    )

                    cart_items = list(
                        CartItem.objects.select_for_update()
                        .filter(cart=locked_cart)
                        .select_related(
                            "product",
                            "product__vendor",
                            "variant",
                        )
                    )

                    if not cart_items:
                        messages.error(
                            request,
                            "Your cart is empty. Please add products first.",
                        )
                        return redirect("cart:cart_detail")

                    prepared_items = []
                    vendor_groups = defaultdict(list)
                    order_subtotal = Decimal("0.00")

                    # Recheck availability and calculate prices on the server.
                    for cart_item in cart_items:
                        product = (
                            Product.objects.select_for_update()
                            .select_related("vendor")
                            .get(pk=cart_item.product_id)
                        )

                        if (
                            product.status != Product.Status.PUBLISHED
                            or product.vendor.status != "APPROVED"
                        ):
                            raise ValueError(
                                f"{product.name} is no longer available."
                            )

                        variant = None

                        if cart_item.variant_id:
                            variant = (
                                ProductVariant.objects.select_for_update()
                                .get(pk=cart_item.variant_id)
                            )

                            if (
                                variant.product_id != product.pk
                                or not variant.is_active
                            ):
                                raise ValueError(
                                    f"An option for {product.name} is no longer available."
                                )

                            available_stock = variant.stock_quantity
                            unit_price = variant.effective_price
                            sku = variant.sku
                            item_name = f"{product.name} - {variant.name}"

                        else:
                            # Products with active variants must have a
                            # valid variant selected.
                            if ProductVariant.objects.filter(
                                product=product,
                                is_active=True,
                            ).exists():
                                raise ValueError(
                                    f"Please select an option for {product.name}."
                                )

                            available_stock = product.stock_quantity
                            unit_price = product.price
                            sku = product.sku
                            item_name = product.name

                        if cart_item.quantity > available_stock:
                            raise ValueError(
                                f"Insufficient stock for {item_name}. "
                                f"Available quantity: {available_stock}."
                            )

                        line_total = unit_price * cart_item.quantity

                        prepared = {
                            "cart_item": cart_item,
                            "product": product,
                            "variant": variant,
                            "vendor": product.vendor,
                            "item_name": item_name,
                            "sku": sku,
                            "unit_price": unit_price,
                            "quantity": cart_item.quantity,
                            "line_total": line_total,
                        }

                        prepared_items.append(prepared)
                        vendor_groups[product.vendor_id].append(prepared)
                        order_subtotal += line_total

                    # Shipping and taxes remain zero until their rules
                    # are implemented.
                    shipping_cost = Decimal("0.00")
                    tax_amount = Decimal("0.00")

                    order = form.save(commit=False)
                    order.customer = request.user
                    order.subtotal = order_subtotal
                    order.shipping_cost = shipping_cost
                    order.tax_amount = tax_amount
                    order.total_amount = (
                        order_subtotal + shipping_cost + tax_amount
                    )
                    order.payment_status = Order.PaymentStatus.UNPAID
                    order.save()

                    # Create one vendor order per vendor.
                    for vendor_items in vendor_groups.values():
                        vendor = vendor_items[0]["vendor"]

                        vendor_subtotal = sum(
                            (
                                item["line_total"]
                                for item in vendor_items
                            ),
                            Decimal("0.00"),
                        )

                        vendor_order = VendorOrder.objects.create(
                            order=order,
                            vendor=vendor,
                            subtotal=vendor_subtotal,
                            shipping_cost=Decimal("0.00"),
                            total_amount=vendor_subtotal,
                        )

                        for item in vendor_items:
                            OrderItem.objects.create(
                                vendor_order=vendor_order,
                                product=item["product"],
                                variant=item["variant"],
                                product_name=item["item_name"],
                                sku=item["sku"],
                                vendor_store_name=vendor.store_name,
                                unit_price=item["unit_price"],
                                quantity=item["quantity"],
                                line_total=item["line_total"],
                            )

                    # Reduce stock only after all items have been validated.
                    for item in prepared_items:
                        if item["variant"]:
                            variant = item["variant"]
                            variant.stock_quantity -= item["quantity"]
                            variant.save(update_fields=["stock_quantity"])
                        else:
                            product = item["product"]
                            product.stock_quantity -= item["quantity"]
                            product.save(update_fields=["stock_quantity"])

                    # Mark the old cart as converted after successful order
                    # creation. Its items remain as historical cart records.
                    locked_cart.status = Cart.Status.CONVERTED
                    locked_cart.save(update_fields=["status", "updated_at"])

                messages.success(
                    request,
                    f"Order {order.order_number} was placed successfully.",
                )
                return redirect(
                    "orders:order_confirmation",
                    order_number=order.order_number,
                )

            except (
                ValueError,
                Product.DoesNotExist,
                ProductVariant.DoesNotExist,
                Cart.DoesNotExist,
            ) as error:
                messages.error(request, str(error))
                return redirect("cart:cart_detail")

    else:
        form = CheckoutForm()

    items = list(
        cart.items.select_related(
            "product",
            "product__vendor",
            "variant",
        ).prefetch_related("product__images")
    )

    for item in items:
        item.unit_price = (
            item.variant.effective_price
            if item.variant_id
            else item.product.price
        )
        item.subtotal = item.unit_price * item.quantity

    total = sum(
        (item.subtotal for item in items),
        Decimal("0.00"),
    )

    return render(
        request,
        "orders/checkout.html",
        {
            "form": form,
            "cart": cart,
            "items": items,
            "total": total,
        },
    )

@login_required
def order_confirmation(request, order_number):
    order = get_object_or_404(
        Order.objects.filter(customer=request.user)
        .prefetch_related("vendor_orders__items"),
        order_number=order_number,
    )

    return render(
        request,
        "orders/order_confirmation.html",
        {"order": order},
    )
    
    

from django.shortcuts import get_object_or_404


@login_required
def order_list(request):
    orders = (
        Order.objects.filter(customer=request.user)
        .prefetch_related("vendor_orders__items")
        .order_by("-created_at")
    )

    return render(
        request,
        "orders/order_list.html",
        {"orders": orders},
    )


@login_required
def order_detail(request, order_number):
    order = get_object_or_404(
        Order.objects.filter(customer=request.user)
        .prefetch_related("vendor_orders__items"),
        order_number=order_number,
    )

    return render(
        request,
        "orders/order_detail.html",
        {"order": order},
    )
