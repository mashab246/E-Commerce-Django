from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import redirect, render
from .forms import VendorRegistrationForm
from .models import Vendor
from products.models import Product
from orders.models import VendorOrder
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

@login_required
def vendor_dashboard(request):
    vendor = Vendor.objects.filter(user=request.user).first()

    # Users without a vendor profile must apply first.
    if vendor is None:
        return redirect("vendors:vendor_register")

    # Only approved vendors can access store statistics.
    if vendor.status != Vendor.Status.APPROVED:
        return render(
            request,
            "vendors/vendor_dashboard.html",
            {
                "vendor": vendor,
            },
        )

    # Approved vendor statistics.
    vendor_orders = VendorOrder.objects.filter(vendor=vendor)
    products = Product.objects.filter(vendor=vendor)

    total_products = products.count()
    total_orders = vendor_orders.count()

    pending_orders = vendor_orders.filter(
        status=VendorOrder.Status.PENDING
    ).count()

    completed_orders = vendor_orders.filter(
        status=VendorOrder.Status.DELIVERED
    ).count()

    delivered_sales = vendor_orders.filter(
        status=VendorOrder.Status.DELIVERED
    ).aggregate(
        total=Sum("total_amount")
    )["total"] or 0

    context = {
        "vendor": vendor,
        "total_products": total_products,
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "completed_orders": completed_orders,
        "delivered_sales": delivered_sales,
        "recent_orders": vendor_orders.select_related(
            "order",
            "order__customer",
        ).order_by("-created_at")[:5],
    }

    return render(
        request,
        "vendors/vendor_dashboard.html",
        context,
    )


@login_required
def vendor_register(request):
    if hasattr(request.user, "vendor_profile"):
        messages.info(
            request,
            "You already have a vendor application."
        )
        return redirect("vendors:vendor_dashboard")

    if request.method == "POST":
        form = VendorRegistrationForm(request.POST)

        if form.is_valid():
            vendor = form.save(commit=False)
            vendor.user = request.user
            vendor.status = Vendor.Status.PENDING
            vendor.save()

            request.user.role = request.user.Role.VENDOR
            request.user.save(update_fields=["role"])

            messages.success(
                request,
                "Your vendor application has been submitted. "
                "Please wait for administrator approval."
            )

            return redirect("vendors:vendor_dashboard")

    else:
        form = VendorRegistrationForm()

    return render(
        request,
        "vendors/vendor_register.html",
        {"form": form},
    )

@login_required
def vendor_orders(request):
    vendor = Vendor.objects.filter(user=request.user).first()

    if vendor is None:
        return redirect("vendors:vendor_register")

    if vendor.status != Vendor.Status.APPROVED:
        raise PermissionDenied(
            "Your vendor account must be approved to manage orders."
        )

    orders = (
        VendorOrder.objects.filter(vendor=vendor)
        .select_related("order", "order__customer")
        .prefetch_related("items")
        .order_by("-created_at")
    )

    return render(
        request,
        "vendors/vendor_orders.html",
        {
            "vendor": vendor,
            "orders": orders,
        },
    )


@login_required
def vendor_order_detail(request, pk):
    vendor = Vendor.objects.filter(user=request.user).first()

    if vendor is None:
        return redirect("vendors:vendor_register")

    if vendor.status != Vendor.Status.APPROVED:
        raise PermissionDenied(
            "Your vendor account must be approved to manage orders."
        )

    vendor_order = get_object_or_404(
        VendorOrder.objects.select_related(
            "order",
            "order__customer",
            "vendor",
        ).prefetch_related("items"),
        pk=pk,
        vendor=vendor,
    )

    return render(
        request,
        "vendors/vendor_order_detail.html",
        {
            "vendor": vendor,
            "vendor_order": vendor_order,
        },
    )


@login_required
@require_POST
def update_vendor_order_status(request, pk):
    vendor = Vendor.objects.filter(user=request.user).first()

    if vendor is None:
        return redirect("vendors:vendor_register")

    if vendor.status != Vendor.Status.APPROVED:
        raise PermissionDenied(
            "Your vendor account must be approved to manage orders."
        )

    vendor_order = get_object_or_404(
        VendorOrder,
        pk=pk,
        vendor=vendor,
    )

    new_status = request.POST.get("status")

    valid_statuses = [
        choice[0] for choice in VendorOrder.Status.choices
    ]

    if new_status not in valid_statuses:
        messages.error(request, "Please select a valid order status.")
        return redirect(
            "vendors:vendor_order_detail",
            pk=vendor_order.pk,
        )

    vendor_order.status = new_status
    vendor_order.save(update_fields=["status", "updated_at"])

    messages.success(
        request,
        f"Order {vendor_order.order.order_number} "
        f"status updated to {vendor_order.get_status_display()}.",
    )

    return redirect(
        "vendors:vendor_order_detail",
        pk=vendor_order.pk,
    )
    
