
from django.contrib import admin
from .models import Order, VendorOrder, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = (
        "product_name",
        "sku",
        "vendor_store_name",
        "unit_price",
        "quantity",
        "line_total",
    )


class VendorOrderInline(admin.TabularInline):
    model = VendorOrder
    extra = 0
    readonly_fields = (
        "vendor",
        "status",
        "subtotal",
        "shipping_cost",
        "total_amount",
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "customer",
        "status",
        "payment_status",
        "total_amount",
        "created_at",
    )
    list_filter = ("status", "payment_status", "payment_method")
    search_fields = ("order_number", "customer__username", "customer__email")
    readonly_fields = ("order_number", "created_at", "updated_at")
    inlines = [VendorOrderInline]


@admin.register(VendorOrder)
class VendorOrderAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "vendor",
        "status",
        "total_amount",
        "created_at",
    )
    list_filter = ("status",)
    search_fields = ("order__order_number", "vendor__store_name")
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "product_name",
        "sku",
        "vendor_store_name",
        "quantity",
        "unit_price",
        "line_total",
    )
    search_fields = ("product_name", "sku", "vendor_store_name")
    readonly_fields = (
        "vendor_order",
        "product",
        "variant",
        "product_name",
        "sku",
        "vendor_store_name",
        "unit_price",
        "quantity",
        "line_total",
        "created_at",
    )

from django.contrib import admin
from .models import PaymentTransaction


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = (
        "transaction_reference",
        "order",
        "provider",
        "amount",
        "currency",
        "status",
        "paid_at",
        "created_at",
    )

    list_filter = (
        "provider",
        "status",
        "currency",
    )

    search_fields = (
        "transaction_reference",
        "provider_transaction_id",
        "order__order_number",
        "order__customer__username",
    )

    readonly_fields = (
        "transaction_reference",
        "created_at",
        "updated_at",
    )
    