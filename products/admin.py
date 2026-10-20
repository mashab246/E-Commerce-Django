from django.contrib import admin
from .models import Category, Product


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

