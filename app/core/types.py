"""Type definitions for Cactus Trading Bot."""

from typing import TypedDict, Literal, Optional
from datetime import datetime
from decimal import Decimal


class OrderSide(Literal["buy", "sell"]):
    """Order side: buy or sell."""
    pass


class OrderType(Literal["market", "limit", "stop", "stop_limit"]):
    """Order type."""
    pass


class OrderStatus(Literal["open", "closed", "canceled", "rejected"]):
    """Order status."""
    pass


class Ticker(TypedDict):
    """Market ticker data."""
    symbol: str
    last_price: float
    bid: float
    ask: float
    volume: float
    timestamp: datetime


class OHLCV(TypedDict):
    """OHLCV candle data."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class OrderRequest(TypedDict):
    """Order request data."""
    symbol: str
    side: OrderSide
    order_type: OrderType
    amount: float
    price: Optional[float]  # Required for limit/stop orders


class OrderResponse(TypedDict):
    """Order execution response."""
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    amount: float
    price: Optional[float]
    filled: float
    status: OrderStatus
    timestamp: datetime
