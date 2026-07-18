"""
Custom exceptions for the application.
Provides standardized error handling.
"""
from fastapi import HTTPException, status


class MarketplaceException(HTTPException):
    """Base exception for marketplace-specific errors"""
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)


class InsufficientStockError(MarketplaceException):
    """Raised when there's insufficient stock for an operation"""
    def __init__(self, product_name: str, available: int, requested: int):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient stock for product '{product_name}'. Available: {available}, Requested: {requested}"
        )


class InvalidStockOperationError(MarketplaceException):
    """Raised when stock operation is invalid (e.g., negative quantity)"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )


class ProductNotFoundError(MarketplaceException):
    """Raised when a product is not found"""
    def __init__(self, product_id: int = None):
        detail = f"Product not found"
        if product_id:
            detail = f"Product with ID {product_id} not found"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )


class OrderNotFoundError(MarketplaceException):
    """Raised when an order is not found"""
    def __init__(self, order_id: int = None):
        detail = "Order not found"
        if order_id:
            detail = f"Order with ID {order_id} not found"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )


class UnauthorizedError(MarketplaceException):
    """Raised when user is not authorized"""
    def __init__(self, detail: str = "Not authorized"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class ValidationError(MarketplaceException):
    """Raised when request validation fails"""
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )
