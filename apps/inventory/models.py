import uuid

from django.db import models
from django.db.models import Q

from django.conf import settings

from apps.tenants.models import Tenant, Store
from apps.catalog.models import Product


class StockBalance(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name="stock_balances"
    )

    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name="stock_balances"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="stock_balances"
    )

    quantity = models.DecimalField(
        max_digits=12,
        decimal_places=3,
        default=0
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["store", "product"],
                name="unique_stock_per_store_product"
            ),
            models.CheckConstraint(
                condition=Q(quantity__gte=0),
                name="stock_quantity_nonnegative"
            )
        ]

        indexes = [
            models.Index(
                fields=["tenant", "store"],
                name="stock_tenant_store_idx"
            )
        ]

    def __str__(self):
        return f"{self.product.name}: {self.quantity}"


class StockMovement(models.Model):

    class MovementType(models.TextChoices):
        OPENING = "OPENING", "Opening Stock"
        PURCHASE = "PURCHASE", "Purchase"
        SALE = "SALE", "Sale"
        SALE_RETURN = "SALE_RETURN", "Sale Return"
        PURCHASE_RETURN = "PURCHASE_RETURN", "Purchase Return"
        DAMAGED = "DAMAGED", "Damaged"
        EXPIRED = "EXPIRED", "Expired"
        ADJUSTMENT = "ADJUSTMENT", "Manual Adjustment"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.PROTECT,
        related_name="stock_movements"
    )

    store = models.ForeignKey(
        Store,
        on_delete=models.PROTECT,
        related_name="stock_movements"
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="stock_movements"
    )

    movement_type = models.CharField(
        max_length=20,
        choices=MovementType.choices
    )

    quantity_delta = models.DecimalField(
        max_digits=12,
        decimal_places=3
    )

    unit_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    reference_type = models.CharField(
        max_length=30,
        blank=True
    )

    reference_id = models.UUIDField(
        null=True,
        blank=True
    )

    reason = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="stock_movements"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:

        constraints = [
            models.CheckConstraint(
                condition=~Q(quantity_delta=0),
                name="stock_movement_nonzero_quantity"
            ),
            models.CheckConstraint(
                condition=(
                    Q(unit_cost__isnull=True) |
                    Q(unit_cost__gte=0)
                ),
                name="stock_movement_valid_cost"
            )
        ]

        indexes = [
            models.Index(
                fields=["tenant", "product", "created_at"],
                name="movement_product_history_idx"
            ),
            models.Index(
                fields=["store", "created_at"],
                name="movement_store_history_idx"
            ),
            models.Index(
                fields=["reference_type", "reference_id"],
                name="movement_reference_idx"
            )
        ]

    def __str__(self):
        return (
            f"{self.product.name}: "
            f"{self.quantity_delta}"
        )