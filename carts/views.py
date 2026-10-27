from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from products.models import Product, ProductVariant
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

    items = list(
        cart.items.select_related(
            "product",
            "product__brand",
            "variant",
        ).prefetch_related("product__images")
    )

    total = 0

    for item in items:
        item.unit_price = (
            item.variant.effective_price
            if item.variant_id
            else item.product.price
        )
        item.subtotal = item.unit_price * item.quantity
        total += item.subtotal

    return render(
        request,
        "carts/cart_detail.html",
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
        messages.error(request, "Please enter a valid quantity.")
        return redirect(
            "products:product_detail",
            pk=product.pk,
            slug=product.slug,
        )

    if quantity < 1:
        messages.error(request, "Quantity must be at least 1.")
        return redirect(
            "products:product_detail",
            pk=product.pk,
            slug=product.slug,
        )

    variant_id = request.POST.get("variant_id")
    variant = None

    active_variants = ProductVariant.objects.filter(
        product=product,
        is_active=True,
    )

    if active_variants.exists():
        if not variant_id:
            messages.error(request, "Please select a product option.")
            return redirect(
                "products:product_detail",
                pk=product.pk,
                slug=product.slug,
            )

        try:
            variant = active_variants.get(pk=int(variant_id))
        except (TypeError, ValueError, ProductVariant.DoesNotExist):
            messages.error(request, "Please select a valid product option.")
            return redirect(
                "products:product_detail",
                pk=product.pk,
                slug=product.slug,
            )

        available_stock = variant.stock_quantity
    else:
        if variant_id:
            messages.error(
                request,
                "This product does not have selectable options.",
            )
            return redirect(
                "products:product_detail",
                pk=product.pk,
                slug=product.slug,
            )

        available_stock = product.stock_quantity

    if available_stock < 1:
        messages.error(request, "This option is out of stock.")
        return redirect(
            "products:product_detail",
            pk=product.pk,
            slug=product.slug,
        )

    cart = get_or_create_active_cart(request.user)

    item = CartItem.objects.filter(
        cart=cart,
        product=product,
        variant=variant,
    ).first()

    new_quantity = quantity + (item.quantity if item else 0)

    if new_quantity > available_stock:
        messages.error(
            request,
            f"Only {available_stock} unit(s) are currently available.",
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
            variant=variant,
            quantity=quantity,
        )

    if variant:
        messages.success(
            request,
            f"{product.name} ({variant.name}) added to your cart.",
        )
    else:
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


@login_required
@require_POST
@transaction.atomic
def update_cart(request, item_id):
    cart = get_or_create_active_cart(request.user)

    item = get_object_or_404(
        CartItem.objects.select_related("product", "variant"),
        pk=item_id,
        cart=cart,
    )

    try:
        quantity = int(request.POST.get("quantity", ""))
    except (TypeError, ValueError):
        messages.error(request, "Please enter a valid quantity.")
        return redirect("cart:cart_detail")

    if quantity < 1:
        messages.error(request, "Quantity must be at least 1.")
        return redirect("cart:cart_detail")

    available_stock = (
        item.variant.stock_quantity
        if item.variant_id
        else item.product.stock_quantity
    )

    if quantity > available_stock:
        messages.error(
            request,
            f"Only {available_stock} unit(s) are currently available.",
        )
        return redirect("cart:cart_detail")

    item.quantity = quantity
    item.save(update_fields=["quantity", "updated_at"])

    messages.success(request, "Cart quantity updated.")
    return redirect("cart:cart_detail")
