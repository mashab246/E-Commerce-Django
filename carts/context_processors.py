from .models import Cart

def cart_item_count(request):
    if not request.user.is_authenticated:
        return {"cart_item_count": 0}

    cart = Cart.objects.filter(
        user=request.user,
        status=Cart.Status.ACTIVE,
    ).first()

    if cart is None:
        return {"cart_item_count": 0}

    return {
        "cart_item_count": sum(
            item.quantity for item in cart.items.all()
        )
    }
