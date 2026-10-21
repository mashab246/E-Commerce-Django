from django.contrib import admin
from .models import Category, Product, Brand, ProductImage, ProductVariant, InventoryMovement


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "parent", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "vendor",
        "category",
        "price",
        "stock_quantity",
        "status",
        "created_at",
    )

    list_filter = ("status", "category", "created_at")
    search_fields = ("name", "sku", "vendor__store_name")
    readonly_fields = ("created_at", "updated_at")
    list_select_related = ("vendor", "category")


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("product", "is_primary", "created_at")
    list_filter = ("is_primary", "created_at")
    search_fields = ("product__name", "alt_text")
    list_select_related = ("product",)


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "sku",
        "product",
        "price",
        "stock_quantity",
        "is_active",
    )

    list_filter = ("is_active",)
    search_fields = ("name", "sku", "product__name")
    list_select_related = ("product",)


@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    list_display = (
        "variant",
        "movement_type",
        "quantity",
        "created_by",
        "created_at",
    )

    list_filter = ("movement_type", "created_at")
    search_fields = ("variant__sku", "variant__product__name")
    list_select_related = ("variant", "created_by")
    readonly_fields = ("created_at",)
