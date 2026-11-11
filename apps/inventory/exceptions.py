class InventoryError(Exception):
    """Base exception for inventory operations."""


class InsufficientStockError(InventoryError):
    """Raised when requested quantity exceeds available stock."""


class InvalidInventoryOperation(InventoryError):
    """Raised when an inventory operation is invalid."""