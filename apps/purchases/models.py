import uuid

from django.db import models
from django.db.models import Q
from django.conf import settings

from apps.tenants.models import Tenant, Store
from apps.catalog.models import Product


class Supplier(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="suppliers"
    )

    name = models.CharField(max_length=200)

    phone = models.CharField(max_length=15, blank=True)

    email = models.EmailField(blank=True)

    address = models.TextField(blank=True)

    gstin = models.CharField(max_length=15, blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "name"],
                name="unique_supplier_per_tenant"
            )
        ]

        indexes = [
            models.Index(
                fields=["tenant", "name"],
                name="supplier_tenant_name_idx"
            )
        ]

    def __str__(self):
        return self.name


class Purchase(models.Model):

    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        RECEIVED = "RECEIVED", "Received"
        CANCELLED = "CANCELLED", "Cancelled"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.PROTECT,
        related_name="purchases"
    )

    store = models.ForeignKey(
        Store,
        on_delete=models.PROTECT,
        related_name="purchases"
    )

    supplier = models.ForeignKey(
        Supplier,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="purchases"
    )

    purchase_number = models.CharField(max_length=50)

    supplier_invoice_number = models.CharField(
        max_length=100,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )

    subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    discount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    tax_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    grand_total = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    notes = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_purchases"
    )

    purchased_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "purchase_number"],
                name="unique_purchase_number_per_tenant"
            ),
            models.UniqueConstraint(
                fields=[
                    "tenant",
                    "supplier",
                    "supplier_invoice_number"
                ],
                condition=~Q(supplier_invoice_number=""),
                name="unique_supplier_invoice_per_tenant"
            ),
            models.CheckConstraint(
                condition=Q(subtotal__gte=0),
                name="purchase_subtotal_nonnegative"
            ),
            models.CheckConstraint(
                condition=Q(discount__gte=0),
                name="purchase_discount_nonnegative"
            ),
            models.CheckConstraint(
                condition=Q(tax_amount__gte=0),
                name="purchase_tax_nonnegative"
            ),
            models.CheckConstraint(
                condition=Q(grand_total__gte=0),
                name="purchase_total_nonnegative"
            )
        ]

        indexes = [
            models.Index(
                fields=["tenant", "status", "created_at"],
                name="purchase_tenant_status_idx"
            )
        ]

    def __str__(self):
        return self.purchase_number


class PurchaseItem(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    purchase = models.ForeignKey(
        Purchase,
        on_delete=models.CASCADE,
        related_name="items"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="purchase_items"
    )

    # Historical snapshots
    product_name = models.CharField(max_length=255)

    sku = models.CharField(max_length=100)

    unit_code = models.CharField(max_length=20)

    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3
    )

    unit_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    discount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    line_subtotal = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    line_tax = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    line_total = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(quantity__gt=0),
                name="purchase_item_quantity_positive"
            ),
            models.CheckConstraint(
                condition=Q(unit_cost__gte=0),
                name="purchase_item_cost_nonnegative"
            ),
            models.CheckConstraint(
                condition=Q(tax_rate__gte=0, tax_rate__lte=100),
                name="purchase_item_tax_valid"
            ),
            models.CheckConstraint(
                condition=Q(discount__gte=0),
                name="purchase_item_discount_nonnegative"
            )
        ]

    def __str__(self):
        return f"{self.product_name} - {self.quantity}"