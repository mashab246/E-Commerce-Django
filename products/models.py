from django.conf import settings
from django.db import models
from django.utils.text import slugify
 

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)

    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="subcategories",
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(
        upload_to="brands/",
        blank=True,
        null=True,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name



class Product(models.Model):

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PUBLISHED = "PUBLISHED", "Published"
        ARCHIVED = "ARCHIVED", "Archived"

    vendor = models.ForeignKey(
        "vendors.Vendor",
        on_delete=models.PROTECT,
        related_name="products",
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
    )
    
    
    brand = models.ForeignKey(
        "Brand",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products",
    )


    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, blank=True)
    sku = models.CharField(max_length=100)

    description = models.TextField()
    price = models.DecimalField(max_digits=12, decimal_places=2)

    stock_quantity = models.PositiveIntegerField(default=0)

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["vendor", "sku"],
                name="unique_vendor_sku",
            ),
            models.UniqueConstraint(
                fields=["vendor", "slug"],
                name="unique_vendor_product_slug",
            ),
        ]
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="images",
    )

    image = models.ImageField(upload_to="products/")
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_primary", "created_at"]

    def __str__(self):
        return f"Image for {self.product.name}"


class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="variants",
    )

    name = models.CharField(max_length=150)
    sku = models.CharField(max_length=100, unique=True)

    attributes = models.JSONField(default=dict, blank=True)

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )

    stock_quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["product__name", "name"]

    def __str__(self):
        return f"{self.product.name} - {self.name}"

    @property
    def effective_price(self):
        return self.price if self.price is not None else self.product.price


class InventoryMovement(models.Model):

    class MovementType(models.TextChoices):
        STOCK_IN = "IN", "Stock added"
        STOCK_OUT = "OUT", "Stock removed"
        ADJUSTMENT = "ADJUSTMENT", "Stock adjustment"

    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.PROTECT,
        related_name="inventory_movements",
    )

    movement_type = models.CharField(
        max_length=10,
        choices=MovementType.choices,
    )

    quantity = models.PositiveIntegerField()
    note = models.CharField(max_length=255, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inventory_movements",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return (
            f"{self.variant.sku} - "
            f"{self.get_movement_type_display()} "
            f"({self.quantity})"
        )
