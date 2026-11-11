import uuid

from django.db import models
from django.db.models import Q, F

from apps.tenants.models import Tenant


class Unit(models.Model):

    code = models.CharField(
        max_length=20,
        unique=True
    )

    name = models.CharField(max_length=50)

    allows_fraction = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.code})"


class Category(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="categories"
    )

    name = models.CharField(max_length=100)

    parent = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="children"
    )

    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "name"],
                name="unique_category_per_tenant"
            )
        ]

    def __str__(self):
        return self.name


class Product(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="products"
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="products"
    )

    name = models.CharField(max_length=255)

    sku = models.CharField(max_length=100)

    description = models.TextField(blank=True)

    unit = models.ForeignKey(
        Unit,
        on_delete=models.PROTECT,
        related_name="products"
    )

    purchase_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    selling_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    minimum_stock = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=0
    )

    hsn_code = models.CharField(
        max_length=20,
        blank=True
    )

    gst_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    image = models.ImageField(
        upload_to="products/",
        null=True,
        blank=True
    )

    is_published = models.BooleanField(default=False)

    public_description = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "sku"],
                name="unique_product_sku_per_tenant"
            ),
            models.CheckConstraint(
                condition=Q(purchase_price__gte=0),
                name="product_purchase_price_nonnegative"
            ),
            models.CheckConstraint(
                condition=Q(selling_price__gte=0),
                name="product_selling_price_nonnegative"
            ),
            models.CheckConstraint(
                condition=Q(minimum_stock__gte=0),
                name="product_minimum_stock_nonnegative"
            ),
            models.CheckConstraint(
                condition=(
                    Q(gst_rate__isnull=True) |
                    Q(gst_rate__gte=0, gst_rate__lte=100)
                ),
                name="product_gst_rate_valid"
            )
        ]

        indexes = [
            models.Index(
                fields=["tenant", "name"],
                name="product_tenant_name_idx"
            ),
            models.Index(
                fields=["tenant", "category"],
                name="product_tenant_category_idx"
            )
        ]

    def __str__(self):
        return self.name


class ProductBarcode(models.Model):

    class BarcodeType(models.TextChoices):
        EAN13 = "EAN13", "EAN-13"
        UPC = "UPC", "UPC"
        CODE128 = "CODE128", "Code 128"
        QR = "QR", "QR Code"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="barcodes"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="barcodes"
    )

    barcode_value = models.CharField(max_length=100)

    barcode_type = models.CharField(
        max_length=20,
        choices=BarcodeType.choices
    )

    is_primary = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "barcode_value"],
                name="unique_barcode_per_tenant"
            ),
            models.UniqueConstraint(
                fields=["product"],
                condition=Q(is_primary=True),
                name="unique_primary_barcode_per_product"
            )
        ]

    def __str__(self):
        return self.barcode_value