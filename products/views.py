from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from vendors.models import Vendor
from .forms import ProductForm
from .models import Product, Category


def get_vendor_for_user(user):
    vendor = getattr(user, "vendor_profile", None)

    if vendor is None:
        raise PermissionDenied(
            "You must have a vendor profile to manage products."
        )

    return vendor


def product_list(request):
    products = (
        Product.objects.filter(
            status=Product.Status.PUBLISHED,
            vendor__status=Vendor.Status.APPROVED,
        )
        .select_related("vendor", "category", "brand")
        .prefetch_related("images")
        .order_by("-created_at")
    )

    search_query = request.GET.get("q", "").strip()
    category_slug = request.GET.get("category", "").strip()

    if search_query:
        products = products.filter(
            Q(name__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(brand__name__icontains=search_query)
            | Q(category__name__icontains=search_query)
        )

    selected_category = None

    if category_slug:
        selected_category = Category.objects.filter(
            slug=category_slug,
            is_active=True,
        ).first()

        if selected_category:
            # Include products in this category and its descendants.
            category_ids = [selected_category.pk]
            pending_ids = [selected_category.pk]

            while pending_ids:
                child_ids = list(
                    Category.objects.filter(
                        parent_id__in=pending_ids,
                        is_active=True,
                    ).values_list("id", flat=True)
                )
                category_ids.extend(child_ids)
                pending_ids = child_ids

            products = products.filter(category_id__in=category_ids)

    categories = Category.objects.filter(
        is_active=True,
        parent__isnull=True,
    ).order_by("name")

    return render(
        request,
        "products/product_list.html",
        {
            "products": products[:24],
            "categories": categories[:8],
            "all_categories": categories,
            "selected_category": selected_category,
            "search_query": search_query,
        },
    )




def product_detail(request, pk, slug):
    product = get_object_or_404(
        Product.objects.select_related("vendor", "category", "brand"),
        pk=pk,
        slug=slug,
        status=Product.Status.PUBLISHED,
        vendor__status=Vendor.Status.APPROVED,
    )

    return render(
        request,
        "products/product_detail.html",
        {"product": product},
    )


@login_required
def my_products(request):
    vendor = get_vendor_for_user(request.user)

    products = (
        Product.objects.filter(vendor=vendor)
        .select_related("category", "brand")
        .order_by("-created_at")
    )

    return render(
        request,
        "products/my_products.html",
        {"products": products},
    )


@login_required
def product_create(request):
    vendor = get_vendor_for_user(request.user)

    if request.method == "POST":
        form = ProductForm(request.POST)

        if form.is_valid():
            product = form.save(commit=False)
            product.vendor = vendor

            # Unapproved vendors may save drafts, but cannot publish.
            if vendor.status != Vendor.Status.APPROVED:
                product.status = Product.Status.DRAFT

            product.save()
            messages.success(request, "Product created successfully.")
            return redirect("products:my_products")
    else:
        form = ProductForm()

    return render(
        request,
        "products/product_form.html",
        {"form": form, "title": "Add Product"},
    )


@login_required
def product_update(request, pk):
    vendor = get_vendor_for_user(request.user)

    product = get_object_or_404(
        Product,
        pk=pk,
        vendor=vendor,
    )

    if request.method == "POST":
        form = ProductForm(request.POST, instance=product)

        if form.is_valid():
            product = form.save(commit=False)

            if vendor.status != Vendor.Status.APPROVED:
                product.status = Product.Status.DRAFT

            product.save()
            messages.success(request, "Product updated successfully.")
            return redirect("products:my_products")
    else:
        form = ProductForm(instance=product)

    return render(
        request,
        "products/product_form.html",
        {"form": form, "title": "Edit Product"},
    )


@login_required
def product_delete(request, pk):
    vendor = get_vendor_for_user(request.user)

    product = get_object_or_404(
        Product,
        pk=pk,
        vendor=vendor,
    )

    if request.method == "POST":
        # Archive instead of deleting a product that may be referenced
        # by carts, orders or inventory history.
        product.status = Product.Status.ARCHIVED
        product.save(update_fields=["status", "updated_at"])

        messages.success(request, "Product archived successfully.")
        return redirect("products:my_products")

    return render(
        request,
        "products/product_confirm_delete.html",
        {"product": product},
    )


def category_list(request):
    categories = Category.objects.filter(
        is_active=True,
        parent__isnull=True,
    ).prefetch_related("subcategories").order_by("name")

    category_slug = request.GET.get("category", "").strip()
    selected_category = None

    if category_slug:
        selected_category = Category.objects.filter(
            slug=category_slug,
            is_active=True,
        ).first()

    if selected_category:
        display_categories = [selected_category]
    else:
        display_categories = categories

    return render(
        request,
        "products/category_list.html",
        {
            "all_categories": categories,
            "display_categories": display_categories,
            "selected_category": selected_category,
        },
    )


def navigation_categories(request):
    categories = (
        Category.objects
        .filter(is_active=True, parent__isnull=True)
        .prefetch_related("subcategories")
        .order_by("name")
    )

    return {
        "navigation_categories": categories,
    }
