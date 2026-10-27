from django.urls import path
from . import views

app_name = "orders"

urlpatterns = [
    path("", views.order_list, name="order_list"),
    path("checkout/", views.checkout, name="checkout"),
    path(
        "confirmation/<str:order_number>/",
        views.order_confirmation,
        name="order_confirmation",
    ),
    path(
        "<str:order_number>/",
        views.order_detail,
        name="order_detail",
    ),
]
