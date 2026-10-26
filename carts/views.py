from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from products.models import Product
from .models import Cart, CartItem


def get_or_create_active_cart(user):
    cart, _ = Cart.objects.get_or_create(
        user=user,
        status=Cart.Status.ACTIVE,
    )
    return cart


@login_required
def cart_detail(request):
    cart = get_or_create_active_cart(request.user)

    items = cart.items.select_related(
        "product",
        "product__brand",
        "variant",
    ).prefetch_related("product__images")

    total = sum(
        item.product.price * item.quantity
        for item in items
    )

    return render(
        request,
        "cart/cart_detail.html",
        {
            "cart": cart,
            "items": items,
            "total": total,
        },
    )


@login_required
@require_POST
@transaction.atomic
def add_to_cart(request, product_id):
    product = get_object_or_404(
        Product.objects.select_related("vendor"),
        pk=product_id,
        status=Product.Status.PUBLISHED,
        vendor__status="APPROVED",
    )

    try:
        quantity = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        quantity = 1

    if quantity < 1:
        messages.error(request, "Quantity must be at least 1.")
        return redirect(
            "products:product_detail",
            pk=product.pk,
            slug=product.slug,
        )

    if product.stock_quantity < quantity:
        messages.error(
            request,
            "There isn't enough stock for that quantity.",
        )
        return redirect(
            "products:product_detail",
            pk=product.pk,
            slug=product.slug,
        )

    cart = get_or_create_active_cart(request.user)

    item = CartItem.objects.filter(
        cart=cart,
        product=product,
        variant__isnull=True,
    ).first()

    new_quantity = quantity + (item.quantity if item else 0)

    if new_quantity > product.stock_quantity:
        messages.error(
            request,
            "Your cart quantity would exceed available stock.",
        )
        return redirect(
            "products:product_detail",
            pk=product.pk,
            slug=product.slug,
        )

    if item:
        item.quantity = new_quantity
        item.save(update_fields=["quantity", "updated_at"])
    else:
        CartItem.objects.create(
            cart=cart,
            product=product,
            quantity=quantity,
        )

    messages.success(request, f"{product.name} added to your cart.")

    return redirect("cart:cart_detail")


@login_required
@require_POST
@transaction.atomic
def remove_from_cart(request, item_id):
    cart = get_or_create_active_cart(request.user)

    item = get_object_or_404(
        CartItem,
        pk=item_id,
        cart=cart,
    )
    item.delete()

    messages.success(request, "Item removed from your cart.")
    return redirect("cart:cart_detail")

