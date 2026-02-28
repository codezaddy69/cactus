"""Base exchange interface for all exchange implementations."""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from decimal import Decimal
import ccxt.async_support as ccxt

from app.core.types import (
    Ticker,
    OHLCV,
    OrderRequest,
    OrderResponse,
    OrderSide,
    OrderType,
    OrderStatus
)
from app.core.exceptions import ExchangeError, RateLimitError


class BaseExchange(ABC):
    """Abstract base class for exchange integrations."""

    def __init__(self, api_key: Optional[str] = None, secret: Optional[str] = None):
        """
        Initialize exchange connection.

        Args:
            api_key: Exchange API key
            secret: Exchange API secret
        """
        self.api_key = api_key
        self.secret = secret
        self._exchange: Optional[ccxt.Exchange] = None

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to exchange."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close exchange connection."""
        pass

    @abstractmethod
    async def get_ticker(self, symbol: str) -> Ticker:
        """
        Fetch current ticker for a symbol.

        Args:
            symbol: Trading pair symbol (e.g., 'BTC/USDT')

        Returns:
            Ticker data

        Raises:
            ExchangeError: If fetch fails
        """
        pass

    @abstractmethod
    async def get_ohlcv(
        self,
        symbol: str,
        timeframe: str = '1h',
        limit: int = 100
    ) -> List[OHLCV]:
        """
        Fetch OHLCV candle data.

        Args:
            symbol: Trading pair symbol
            timeframe: Candle timeframe (1m, 5m, 1h, 4h, 1d)
            limit: Number of candles to fetch

        Returns:
            List of OHLCV candles

        Raises:
            ExchangeError: If fetch fails
        """
        pass

    @abstractmethod
    async def create_order(self, order: OrderRequest) -> OrderResponse:
        """
        Create and execute order.

        Args:
            order: Order request with symbol, side, type, amount, price

        Returns:
            Order response with execution details

        Raises:
            ExchangeError: If order creation fails
            RateLimitError: If rate limit exceeded
        """
        pass

    @abstractmethod
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """
        Cancel an existing order.

        Args:
            order_id: Order ID to cancel
            symbol: Trading pair symbol

        Returns:
            True if canceled successfully

        Raises:
            ExchangeError: If cancellation fails
        """
        pass

    @abstractmethod
    async def get_balance(self) -> Dict[str, Any]:
        """
        Fetch account balance.

        Returns:
            Dictionary with balance information

        Raises:
            ExchangeError: If fetch fails
        """
        pass

    @abstractmethod
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch open orders.

        Args:
            symbol: Filter by symbol (optional)

        Returns:
            List of open orders

        Raises:
            ExchangeError: If fetch fails
        """
        pass

    async def test_connection(self) -> bool:
        """
        Test if exchange connection is working.

        Returns:
            True if connection is healthy

        Raises:
            ExchangeError: If connection test fails
        """
        try:
            await self.connect()
            await self.get_balance()
            return True
        except Exception as e:
            raise ExchangeError(f"Connection test failed: {str(e)}")
