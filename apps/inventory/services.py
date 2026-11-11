
from decimal import Decimal

from django.db import transaction

from apps.catalog.models import Product
from apps.tenants.models import Tenant, Store
from apps.inventory.models import StockBalance, StockMovement

from apps.inventory.exceptions import (
    InsufficientStockError,
    InvalidInventoryOperation,
)


# Direction of each inventory operation.
MOVEMENT_DIRECTIONS = {
    StockMovement.MovementType.OPENING: 1,
    StockMovement.MovementType.PURCHASE: 1,
    StockMovement.MovementType.SALE: -1,
    StockMovement.MovementType.SALE_RETURN: 1,
    StockMovement.MovementType.PURCHASE_RETURN: -1,
    StockMovement.MovementType.DAMAGED: -1,
    StockMovement.MovementType.EXPIRED: -1,
}


@transaction.atomic
def post_stock_movement(
    *,
    tenant: Tenant,
    store: Store,
    product: Product,
    movement_type: str,
    quantity: Decimal,
    user,
    unit_cost=None,
    reason="",
    reference_type="",
    reference_id=None,
):
    """
    The single entry point for modifying inventory.

    Normal operations accept a positive quantity.
    ADJUSTMENT accepts a signed quantity.
    """

    quantity = Decimal(str(quantity))

    if not quantity.is_finite() or quantity == 0:
        raise InvalidInventoryOperation(
            "Quantity must be a finite non-zero number."
        )

    # Validate the movement type and calculate its direction.
    if movement_type == StockMovement.MovementType.ADJUSTMENT:
        delta = quantity

    elif movement_type in MOVEMENT_DIRECTIONS:
        if quantity <= 0:
            raise InvalidInventoryOperation(
                "Quantity must be positive."
            )

        delta = quantity * MOVEMENT_DIRECTIONS[movement_type]

    else:
        raise InvalidInventoryOperation(
            "Unsupported stock movement type."
        )

    # Lock the product row.
    # This serializes inventory operations for the same product.
    locked_product = Product.objects.select_for_update().get(
        pk=product.pk,
        tenant=tenant,
        is_active=True,
    )

    # Verify store ownership.
    if store.tenant_id != tenant.pk:
        raise InvalidInventoryOperation(
            "Store does not belong to this tenant."
        )

    # Get or create the balance.
    # Product locking prevents competing first-time balance creation
    # through this service.
    balance, _ = StockBalance.objects.get_or_create(
        tenant=tenant,
        store=store,
        product=locked_product,
        defaults={"quantity": Decimal("0")},
    )

    # Lock the balance before modifying it.
    balance = StockBalance.objects.select_for_update().get(
        pk=balance.pk
    )

    new_quantity = balance.quantity + delta

    # Our business rule: negative inventory is not permitted.
    if new_quantity < 0:
        raise InsufficientStockError(
            f"Available stock: {balance.quantity}, "
            f"Requested stock: {abs(delta)}"
        )

    # Update current stock.
    balance.quantity = new_quantity
    balance.save(update_fields=["quantity", "updated_at"])

    # Append the historical movement.
    movement = StockMovement.objects.create(
        tenant=tenant,
        store=store,
        product=locked_product,
        movement_type=movement_type,
        quantity_delta=delta,
        unit_cost=unit_cost,
        reason=reason,
        reference_type=reference_type,
        reference_id=reference_id,
        created_by=user,
    )

    return movement
