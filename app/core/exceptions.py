"""Custom exceptions for Cactus Trading Bot."""


class CactusError(Exception):
    """Base exception for all Cactus errors."""
    pass


class ExchangeError(CactusError):
    """Exception raised for exchange-related errors."""
    pass


class DatabaseError(CactusError):
    """Exception raised for database-related errors."""
    pass


class ValidationError(CactusError):
    """Exception raised for data validation errors."""
    pass


class InsufficientBalanceError(CactusError):
    """Exception raised when insufficient balance for trade."""
    pass


class RateLimitError(CactusError):
    """Exception raised when rate limit is exceeded."""
    pass


class OrderExecutionError(CactusError):
    """Exception raised when order execution fails."""
    pass
