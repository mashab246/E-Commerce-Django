from decimal import Decimal
from django.core.exceptions import ValidationError
from django.test import TestCase
from accounts.models import User
from vendors.models import Vendor
from products.models import Category, Product, ProductVariant
from .services import (
    add_to_cart,
    get_cart_subtotal,
    get_or_create_active_cart,
    remove_from_cart,
    update_cart_item_quantity,
)


class CartServiceTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="testvendor",
            email="vendor@example.com",
            password="StrongTestPass123!",
            role=User.Role.VENDOR,
        )

        self.vendor = Vendor.objects.create(
            user=self.user,
            store_name="Test Store",
            status=Vendor.Status.APPROVED,
        )

        self.category = Category.objects.create(
            name="Test Electronics",
        )

        self.product = Product.objects.create(
            vendor=self.vendor,
            category=self.category,
            name="Test Phone",
            sku="PHONE-001",
            description="A test phone",
            price=Decimal("500000.00"),
            stock_quantity=10,
            status=Product.Status.PUBLISHED,
        )

    def test_get_or_create_cart(self):
        cart = get_or_create_active_cart(self.user)

        self.assertEqual(cart.user, self.user)
        self.assertEqual(cart.status, "ACTIVE")

        same_cart = get_or_create_active_cart(self.user)
        self.assertEqual(cart.pk, same_cart.pk)

    def test_add_product_to_cart(self):
        item = add_to_cart(self.user, self.product, quantity=2)

        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.product, self.product)

    def test_adding_same_product_increases_quantity(self):
        add_to_cart(self.user, self.product, quantity=2)
        item = add_to_cart(self.user, self.product, quantity=3)

        self.assertEqual(item.quantity, 5)
        self.assertEqual(CartItemCount.count(self.user), 1)

    def test_cannot_exceed_available_stock(self):
        with self.assertRaises(ValidationError):
            add_to_cart(self.user, self.product, quantity=11)

    def test_variant_price_is_used(self):
        variant = ProductVariant.objects.create(
            product=self.product,
            name="128GB",
            sku="PHONE-001-128",
            price=Decimal("600000.00"),
            stock_quantity=5,
        )

        add_to_cart(
            self.user,
            self.product,
            quantity=2,
            variant=variant,
        )

        cart = get_or_create_active_cart(self.user)

        self.assertEqual(
            get_cart_subtotal(cart),
            Decimal("1200000.00"),
        )

    def test_update_and_remove_cart_item(self):
        item = add_to_cart(self.user, self.product, quantity=2)

        updated = update_cart_item_quantity(
            self.user,
            item.pk,
            quantity=4,
        )
        self.assertEqual(updated.quantity, 4)

        remove_from_cart(self.user, item.pk)

        self.assertFalse(cart_item_exists(self.user))


def cart_item_exists(user):
    return user.carts.filter(
        status="ACTIVE",
        items__isnull=False,
    ).exists()


class CartItemCount:
    @staticmethod
    def count(user):
        return sum(
            cart.items.count()
            for cart in user.carts.filter(status="ACTIVE")
        )

