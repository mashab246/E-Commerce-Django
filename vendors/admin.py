from django.contrib import admin
from .models import Vendor


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = (
        "store_name",
        "user",
        "phone_number",
        "status",
        "created_at",
    )

    list_filter = ("status", "created_at")
    search_fields = ("store_name", "user__username", "user__email")
    readonly_fields = ("created_at", "updated_at", "slug")
    ordering = ("-created_at",)

