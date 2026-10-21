from django.contrib import admin
from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    autocomplete_fields = ("product", "variant")


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "status",
        "created_at",
        "updated_at",
    )

    list_filter = ("status", "created_at")
    search_fields = ("user__username", "user__email")
    list_select_related = ("user",)
    inlines = (CartItemInline,)


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = (
        "cart",
        "product",
        "variant",
        "quantity",
        "added_at",
    )

    list_filter = ("added_at",)
    search_fields = (
        "product__name",
        "variant__sku",
        "cart__user__username",
    )
    list_select_related = ("cart", "product", "variant")

