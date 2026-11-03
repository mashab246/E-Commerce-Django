"""
URL configuration for ecommerce project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from .views import admin_dashboard, vendor_approvals, update_vendor_status, user_management, toggle_user_status, product_management, category_management, category_create, category_edit, toggle_category_status, admin_product_edit, update_product_status, order_management, admin_order_detail, update_order_status, payment_management


urlpatterns = [
    path('admin/', admin.site.urls),
    path("dashboard/admin/", admin_dashboard, name="admin_dashboard"),
    path("products/", include("products.urls")),
    path("accounts/", include("accounts.urls")),
    path("cart/", include("carts.urls")),
    path("orders/", include("orders.urls")),
    path("vendors/", include("vendors.urls")),
    path(
        "dashboard/admin/vendors/",
        vendor_approvals,
        name="vendor_approvals",
    ),
    path(
        "dashboard/admin/vendors/<int:vendor_id>/status/",
        update_vendor_status,
        name="update_vendor_status",
    ),
    path(
        "dashboard/admin/users/",
        user_management,
        name="user_management",
    ),
    path(
        "dashboard/admin/users/<int:user_id>/toggle-status/",
        toggle_user_status,
        name="toggle_user_status",
    ),
    path(
        "dashboard/admin/products/",
        product_management,
        name="product_management",
    ),
    path(
        "dashboard/admin/categories/",
        category_management,
        name="category_management",
    ),
    path(
        "dashboard/admin/categories/add/",
        category_create,
        name="category_create",
    ),
    path(
        "dashboard/admin/categories/<int:category_id>/edit/",
        category_edit,
        name="category_edit",
    ),
    path(
        "dashboard/admin/categories/<int:category_id>/toggle-status/",
        toggle_category_status,
        name="toggle_category_status",
    ),
    path(
        "dashboard/admin/products/<int:product_id>/edit/",
        admin_product_edit,
        name="admin_product_edit",
    ),
    path(
        "dashboard/admin/products/<int:product_id>/status/",
        update_product_status,
        name="update_product_status",
    ),
    path(
        "dashboard/admin/orders/",
        order_management,
        name="order_management",
    ),
    path(
        "dashboard/admin/orders/<str:order_number>/",
        admin_order_detail,
        name="admin_order_detail",
    ),
    path(
        "dashboard/admin/orders/<str:order_number>/status/",
        update_order_status,
        name="update_order_status",
    ),
    path(
        "dashboard/admin/payments/",
        payment_management,
        name="payment_management"
    ),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )