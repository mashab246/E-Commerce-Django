from django.urls import path
from . import views

app_name = "vendors"

urlpatterns = [
    path(
        "dashboard/",
        views.vendor_dashboard,
        name="vendor_dashboard",
    ),
    path(
        "register/",
        views.vendor_register,
        name="vendor_register",
    ),
    path(
        "orders/",
        views.vendor_orders,
        name="vendor_orders",
    ),
    path(
        "orders/<int:pk>/",
        views.vendor_order_detail,
        name="vendor_order_detail",
    ),
    path(
        "orders/<int:pk>/update-status/",
        views.update_vendor_order_status,
        name="update_vendor_order_status",
    ),
]
