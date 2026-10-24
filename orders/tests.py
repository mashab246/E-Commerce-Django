from decimal import Decimal
from django.core.exceptions import ValidationError
from django.test import TestCase
from accounts.models import User
from carts.services import add_to_cart
from products.models import Category, Product
from vendors.models import Vendor
from .models import Order, OrderItem, VendorOrder
from .services import checkout_cart


class CheckoutServiceTests(TestCase):
    def setUp(self):
        self.vendor_user = User.objects.create_user(
            username="checkout_vendor",
            email="checkout_vendor@example.com",
            password="TestPass123!",
            role=User.Role.VENDOR,
        )

        self.vendor = Vendor.objects.create(
            user=self.vendor_user,
            store_name="Checkout Store",
            status=Vendor.Status.APPROVED,
        )

        self.customer = User.objects.create_user(
            username="checkout_customer",
            email="checkout_customer@example.com",
            password="TestPass123!",
        )

        self.category = Category.objects.create(
            name="Checkout Electronics"
        )

        self.product = Product.objects.create(
            vendor=self.vendor,
            category=self.category,
            name="Checkout Phone",
            sku="CHECKOUT-PHONE-001",
            description="A checkout test product",
            price=Decimal("500000.00"),
            stock_quantity=10,
            status=Product.Status.PUBLISHED,
        )

        self.shipping_details = {
            "full_name": "Test Customer",
            "phone": "+256700000000",
            "address": "123 Test Road",
            "city": "Kampala",
        }

    def test_checkout_creates_order_and_reduces_stock(self):
        add_to_cart(self.customer, self.product, quantity=2)

        order = checkout_cart(
            self.customer,
            self.shipping_details,
        )

        self.product.refresh_from_db()

        self.assertEqual(order.customer, self.customer)
        self.assertEqual(order.subtotal, Decimal("1000000.00"))
        self.assertEqual(order.total_amount, Decimal("1000000.00"))
        self.assertEqual(self.product.stock_quantity, 8)
        self.assertEqual(order.vendor_orders.count(), 1)
        self.assertEqual(
            OrderItem.objects.filter(
                vendor_order__order=order
            ).count(),
            1,
        )

    def test_checkout_rejects_insufficient_stock(self):
        add_to_cart(self.customer, self.product, quantity=2)

        # Simulate stock being reduced after the item entered the cart.
        Product.objects.filter(pk=self.product.pk).update(
            stock_quantity=1
        )

        with self.assertRaises(ValidationError):
            checkout_cart(self.customer, self.shipping_details)

        self.product.refresh_from_db()

        self.assertEqual(self.product.stock_quantity, 1)
        self.assertEqual(Order.objects.count(), 0)
        self.assertEqual(VendorOrder.objects.count(), 0)

    def test_checkout_rejects_empty_cart(self):
        with self.assertRaises(ValidationError):
            checkout_cart(self.customer, self.shipping_details)

        self.assertEqual(Order.objects.count(), 0)
