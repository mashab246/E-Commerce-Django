from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import get_user_model
from vendors.models import Vendor
from products.models import Product, Category
from orders.models import Order, VendorOrder
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import Q
from products.forms import CategoryForm, ProductForm


def is_marketplace_admin(user):
    return user.is_staff or user.is_superuser


@login_required
@user_passes_test(is_marketplace_admin)
def admin_dashboard(request):
    User = get_user_model()

    context = {
        "total_users": User.objects.count(),
        "total_vendors": Vendor.objects.count(),
        "total_products": Product.objects.count(),
        "total_orders": Order.objects.count(),
    }

    return render(request, "dashboards/admin_dashboard.html", context)


@login_required
@user_passes_test(is_marketplace_admin)
def vendor_approvals(request):
    vendors = Vendor.objects.select_related("user").order_by("-created_at")

    context = {
        "vendors": vendors,
        "pending_count": Vendor.objects.filter(
            status=Vendor.Status.PENDING
        ).count(),
    }

    return render(request, "dashboards/vendor_approvals.html", context)



@login_required
@user_passes_test(is_marketplace_admin)
@require_POST
def update_vendor_status(request, vendor_id):
    vendor = get_object_or_404(Vendor, pk=vendor_id)

    new_status = request.POST.get("status")

    allowed_statuses = {
        Vendor.Status.APPROVED,
        Vendor.Status.REJECTED,
        Vendor.Status.SUSPENDED,
    }

    if new_status not in allowed_statuses:
        messages.error(request, "Invalid vendor status.")
        return redirect("vendor_approvals")

    vendor.status = new_status
    vendor.save(update_fields=["status", "updated_at"])

    # Update the user's role based on the vendor decision.
    if new_status == Vendor.Status.APPROVED:
        vendor.user.role = vendor.user.Role.VENDOR
        vendor.user.save(update_fields=["role"])

    elif new_status == Vendor.Status.REJECTED:
        vendor.user.role = vendor.user.Role.CUSTOMER
        vendor.user.save(update_fields=["role"])

    messages.success(
        request,
        f"{vendor.store_name} status updated to "
        f"{vendor.get_status_display()}."
    )

    return redirect("vendor_approvals")


@login_required
@user_passes_test(is_marketplace_admin)
def user_management(request):
    User = get_user_model()

    search_query = request.GET.get("q", "").strip()

    users = User.objects.all().order_by("-date_joined")

    if search_query:
        users = users.filter(
            Q(username__icontains=search_query)
            | Q(email__icontains=search_query)
        )

    context = {
        "users": users,
        "search_query": search_query,
        "total_users": User.objects.count(),
        "active_users": User.objects.filter(is_active=True).count(),
        "staff_users": User.objects.filter(is_staff=True).count(),
    }

    return render(
        request,
        "dashboards/user_management.html",
        context,
    )
    
@login_required
@user_passes_test(is_marketplace_admin)
@require_POST
def toggle_user_status(request, user_id):
    User = get_user_model()
    account = get_object_or_404(User, pk=user_id)

    # Prevent an administrator from disabling their own account.
    if account.pk == request.user.pk:
        messages.error(
            request,
            "You cannot deactivate your own account here."
        )
        return redirect("user_management")

    # Protect superuser accounts from being deactivated here.
    if account.is_superuser:
        messages.error(
            request,
            "Superuser accounts cannot be deactivated here."
        )
        return redirect("user_management")

    # Toggle the account's active status.
    account.is_active = not account.is_active
    account.save(update_fields=["is_active"])

    if account.is_active:
        messages.success(
            request,
            f"{account.username}'s account has been activated."
        )
    else:
        messages.success(
            request,
            f"{account.username}'s account has been deactivated."
        )

    return redirect("user_management")

@login_required
@user_passes_test(is_marketplace_admin)
def product_management(request):
    search_query = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "").strip()

    products = (
        Product.objects
        .select_related("vendor", "category", "brand")
        .order_by("-created_at")
    )

    if search_query:
        products = products.filter(
            Q(name__icontains=search_query)
            | Q(sku__icontains=search_query)
            | Q(vendor__store_name__icontains=search_query)
            | Q(category__name__icontains=search_query)
        )

    valid_statuses = Product.Status.values

    if status_filter in valid_statuses:
        products = products.filter(status=status_filter)
    else:
        status_filter = ""

    context = {
        "products": products,
        "search_query": search_query,
        "status_filter": status_filter,
        "total_products": Product.objects.count(),
        "published_products": Product.objects.filter(
            status=Product.Status.PUBLISHED
        ).count(),
        "draft_products": Product.objects.filter(
            status=Product.Status.DRAFT
        ).count(),
        "archived_products": Product.objects.filter(
            status=Product.Status.ARCHIVED
        ).count(),
    }

    return render(
        request,
        "dashboards/product_management.html",
        context,
    )
    
@login_required
@user_passes_test(is_marketplace_admin)
def category_management(request):
    search_query = request.GET.get("q", "").strip()

    categories = (
        Category.objects
        .select_related("parent")
        .order_by("parent__name", "name")
    )

    if search_query:
        categories = categories.filter(
            Q(name__icontains=search_query)
            | Q(description__icontains=search_query)
        )

    context = {
        "categories": categories,
        "search_query": search_query,
        "total_categories": Category.objects.count(),
        "active_categories": Category.objects.filter(
            is_active=True
        ).count(),
        "inactive_categories": Category.objects.filter(
            is_active=False
        ).count(),
    }

    return render(
        request,
        "dashboards/category_management.html",
        context,
    )
    
@login_required
@user_passes_test(is_marketplace_admin)
def category_create(request):
    if request.method == "POST":
        form = CategoryForm(request.POST)

        if form.is_valid():
            category = form.save()

            messages.success(
                request,
                f'Category "{category.name}" created successfully.',
            )

            return redirect("category_management")
    else:
        form = CategoryForm()

    return render(
        request,
        "dashboards/category_form.html",
        {
            "form": form,
            "page_title": "Add Category",
            "submit_label": "Create Category",
        },
    )
    
@login_required
@user_passes_test(is_marketplace_admin)
def category_edit(request, category_id):
    category = get_object_or_404(Category, pk=category_id)

    if request.method == "POST":
        form = CategoryForm(request.POST, instance=category)

        if form.is_valid():
            updated_category = form.save()

            messages.success(
                request,
                f'Category "{updated_category.name}" updated successfully.',
            )

            return redirect("category_management")
    else:
        form = CategoryForm(instance=category)

    return render(
        request,
        "dashboards/category_form.html",
        {
            "form": form,
            "page_title": "Edit Category",
            "submit_label": "Save Changes",
            "category": category,
        },
    )
    
@login_required
@user_passes_test(is_marketplace_admin)
@require_POST
def toggle_category_status(request, category_id):
    category = get_object_or_404(Category, pk=category_id)

    category.is_active = not category.is_active
    category.save(update_fields=["is_active"])

    status = "activated" if category.is_active else "deactivated"

    messages.success(
        request,
        f'Category "{category.name}" was {status} successfully.'
    )

    return redirect("category_management")

@login_required
@user_passes_test(is_marketplace_admin)
def admin_product_edit(request, product_id):
    product = get_object_or_404(
        Product.objects.select_related("vendor"),
        pk=product_id,
    )

    if request.method == "POST":
        form = ProductForm(request.POST, instance=product)

        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'Product "{product.name}" updated successfully.',
            )
            return redirect("product_management")
    else:
        form = ProductForm(instance=product)

    return render(
        request,
        "products/product_form.html",
        {
            "form": form,
            "title": f"Admin Edit: {product.name}",
            "product": product,
        },
    )
    

@login_required
@user_passes_test(is_marketplace_admin)
@require_POST
def update_product_status(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    new_status = request.POST.get("status")

    allowed_statuses = {
        Product.Status.DRAFT,
        Product.Status.PUBLISHED,
        Product.Status.ARCHIVED,
    }

    if new_status not in allowed_statuses:
        messages.error(request, "Invalid product status.")
        return redirect("product_management")

    if new_status == product.status:
        messages.info(request, "The product already has that status.")
        return redirect("product_management")

    old_status = product.get_status_display()
    product.status = new_status
    product.save(update_fields=["status", "updated_at"])

    messages.success(
        request,
        f'"{product.name}" changed from {old_status} '
        f'to {product.get_status_display()}.',
    )

    return redirect("product_management")

@login_required
@user_passes_test(is_marketplace_admin)
def order_management(request):
    search_query = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "").strip()
    payment_filter = request.GET.get("payment_status", "").strip()

    orders = (
        Order.objects
        .select_related("customer")
        .prefetch_related("vendor_orders")
        .order_by("-created_at")
    )

    if search_query:
        orders = orders.filter(
            Q(order_number__icontains=search_query)
            | Q(customer__username__icontains=search_query)
            | Q(customer__email__icontains=search_query)
            | Q(shipping_full_name__icontains=search_query)
            | Q(shipping_phone__icontains=search_query)
        )

    if status_filter in Order.Status.values:
        orders = orders.filter(status=status_filter)
    else:
        status_filter = ""

    if payment_filter in Order.PaymentStatus.values:
        orders = orders.filter(payment_status=payment_filter)
    else:
        payment_filter = ""

    context = {
        "orders": orders,
        "search_query": search_query,
        "status_filter": status_filter,
        "payment_filter": payment_filter,
        "total_orders": Order.objects.count(),
        "pending_orders": Order.objects.filter(
            status=Order.Status.PENDING
        ).count(),
        "completed_orders": Order.objects.filter(
            status=Order.Status.DELIVERED
        ).count(),
        "cancelled_orders": Order.objects.filter(
            status=Order.Status.CANCELLED
        ).count(),
        "order_statuses": Order.Status.choices,
        "payment_statuses": Order.PaymentStatus.choices,
    }

    return render(
        request,
        "dashboards/order_management.html",
        context,
    )


@login_required
@user_passes_test(is_marketplace_admin)
def admin_order_detail(request, order_number):
    order = get_object_or_404(
        Order.objects
        .select_related("customer")
        .prefetch_related(
            "vendor_orders__vendor",
            "vendor_orders__items",
        ),
        order_number=order_number,
    )

    return render(
        request,
        "dashboards/admin_order_detail.html",
        {"order": order},
    )


@login_required
@user_passes_test(is_marketplace_admin)
@require_POST
def update_order_status(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    new_status = request.POST.get("status")

    allowed_statuses = {
        value for value, label in Order.Status.choices
    }

    if new_status not in allowed_statuses:
        messages.error(request, "Invalid order status.")
        return redirect(
            "admin_order_detail",
            order_number=order.order_number,
        )

    if new_status == order.status:
        messages.info(request, "The order already has that status.")
        return redirect(
            "admin_order_detail",
            order_number=order.order_number,
        )

    old_status = order.get_status_display()
    order.status = new_status
    order.save(update_fields=["status", "updated_at"])

    messages.success(
        request,
        f"Order {order.order_number} changed from "
        f"{old_status} to {order.get_status_display()}.",
    )

    return redirect(
        "admin_order_detail",
        order_number=order.order_number,
    )
    
@login_required
@user_passes_test(is_marketplace_admin)
def payment_management(request):
    search_query = request.GET.get("q", "").strip()
    status_filter = request.GET.get("status", "").strip()
    method_filter = request.GET.get("method", "").strip()

    payments = Order.objects.select_related(
        "customer"
    ).order_by("-created_at")

    if search_query:
        payments = payments.filter(
            Q(order_number__icontains=search_query)
            | Q(customer__username__icontains=search_query)
            | Q(customer__email__icontains=search_query)
            | Q(shipping_full_name__icontains=search_query)
        )

    if status_filter in Order.PaymentStatus.values:
        payments = payments.filter(payment_status=status_filter)
    else:
        status_filter = ""

    if method_filter in Order.PaymentMethod.values:
        payments = payments.filter(payment_method=method_filter)
    else:
        method_filter = ""

    context = {
        "payments": payments,
        "search_query": search_query,
        "status_filter": status_filter,
        "method_filter": method_filter,
        "payment_statuses": Order.PaymentStatus.choices,
        "payment_methods": Order.PaymentMethod.choices,
        "total_payments": Order.objects.count(),
        "paid_count": Order.objects.filter(
            payment_status=Order.PaymentStatus.PAID
        ).count(),
        "unpaid_count": Order.objects.filter(
            payment_status=Order.PaymentStatus.UNPAID
        ).count(),
        "pending_count": Order.objects.filter(
            payment_status=Order.PaymentStatus.PENDING
        ).count(),
        "failed_count": Order.objects.filter(
            payment_status=Order.PaymentStatus.FAILED
        ).count(),
    }

    return render(
        request,
        "dashboards/payment_management.html",
        context
    )   