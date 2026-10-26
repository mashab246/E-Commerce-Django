from django.urls import path
from . import views

app_name = "products"

urlpatterns = [
    path("", views.product_list, name="product_list"),
    path("categories/", views.category_list, name="category_list"),
    path(
        "my-products/",
        views.my_products,
        name="my_products",
    ),
    path(
        "create/",
        views.product_create,
        name="product_create",
    ),
    path(
        "<int:pk>/<slug:slug>/",
        views.product_detail,
        name="product_detail",
    ),
    path(
        "<int:pk>/edit/",
        views.product_update,
        name="product_update",
    ),
    path(
        "<int:pk>/archive/",
        views.product_delete,
        name="product_delete",
    ),
    
]
