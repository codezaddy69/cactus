"""Coinbase exchange implementation."""

from typing import Optional, List, Dict, Any
from datetime import datetime
import ccxt.async_support as ccxt

from app.exchanges.base import BaseExchange
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
from app.core.logging_config import logger


class CoinbaseExchange(BaseExchange):
    """Coinbase exchange integration using CCXT."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        secret: Optional[str] = None,
        passphrase: Optional[str] = None
    ):
        """
        Initialize Coinbase exchange.

        Args:
            api_key: Coinbase API key
            secret: Coinbase API secret
            passphrase: Coinbase API passphrase
        """
        super().__init__(api_key, secret)
        self.passphrase = passphrase

    async def connect(self) -> None:
        """Establish connection to Coinbase."""
        try:
            config = {
                'apiKey': self.api_key,
                'secret': self.secret,
                'password': self.passphrase,
                'enableRateLimit': True
            }

            self._exchange = ccxt.coinbase(config)
            logger.info("Connected to Coinbase")
        except Exception as e:
            logger.error(f"Failed to connect to Coinbase: {str(e)}")
            raise ExchangeError(f"Connection failed: {str(e)}")

    async def disconnect(self) -> None:
        """Close Coinbase connection."""
        if self._exchange:
            await self._exchange.close()
            self._exchange = None
            logger.info("Disconnected from Coinbase")

    async def get_ticker(self, symbol: str) -> Ticker:
        """Fetch current ticker for a symbol."""
        if not self._exchange:
            raise ExchangeError("Not connected to exchange")

        try:
            ticker = await self._exchange.fetch_ticker(symbol)

            return Ticker(
                symbol=symbol,
                last_price=float(ticker['last']),
                bid=float(ticker['bid']),
                ask=float(ticker['ask']),
                volume=float(ticker['quoteVolume']),
                timestamp=datetime.fromtimestamp(ticker['timestamp'] / 1000)
            )
        except ccxt.RateLimitExceeded as e:
            logger.error(f"Rate limit exceeded: {str(e)}")
            raise RateLimitError(f"Rate limit exceeded: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to fetch ticker for {symbol}: {str(e)}")
            raise ExchangeError(f"Ticker fetch failed: {str(e)}")

    async def get_ohlcv(
        self,
        symbol: str,
        timeframe: str = '1h',
        limit: int = 100
    ) -> List[OHLCV]:
        """Fetch OHLCV candle data."""
        if not self._exchange:
            raise ExchangeError("Not connected to exchange")

        try:
            candles = await self._exchange.fetch_ohlcv(symbol, timeframe, limit=limit)

            ohlcv_list = []
            for candle in candles:
                ohlcv_list.append(OHLCV(
                    timestamp=datetime.fromtimestamp(candle[0] / 1000),
                    open=float(candle[1]),
                    high=float(candle[2]),
                    low=float(candle[3]),
                    close=float(candle[4]),
                    volume=float(candle[5])
                ))

            logger.debug(f"Fetched {len(ohlcv_list)} candles for {symbol}")
            return ohlcv_list
        except Exception as e:
            logger.error(f"Failed to fetch OHLCV for {symbol}: {str(e)}")
            raise ExchangeError(f"OHLCV fetch failed: {str(e)}")

    async def create_order(self, order: OrderRequest) -> OrderResponse:
        """Create and execute order."""
        if not self._exchange:
            raise ExchangeError("Not connected to exchange")

        try:
            # Map order types to CCXT
            ccxt_order_type = order['order_type']

            # Execute order
            executed_order = await self._exchange.create_order(
                symbol=order['symbol'],
                type=ccxt_order_type,
                side=order['side'],
                amount=order['amount'],
                price=order.get('price')
            )

            return OrderResponse(
                order_id=str(executed_order['id']),
                symbol=order['symbol'],
                side=order['side'],
                order_type=order['order_type'],
                amount=float(executed_order['amount']),
                price=float(executed_order.get('price', 0)),
                filled=float(executed_order.get('filled', 0)),
                status=OrderStatus(executed_order['status']),
                timestamp=datetime.fromtimestamp(executed_order['timestamp'] / 1000)
            )
        except ccxt.RateLimitExceeded as e:
            logger.error(f"Rate limit exceeded: {str(e)}")
            raise RateLimitError(f"Rate limit exceeded: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to create order: {str(e)}")
            raise ExchangeError(f"Order creation failed: {str(e)}")

    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an existing order."""
        if not self._exchange:
            raise ExchangeError("Not connected to exchange")

        try:
            await self._exchange.cancel_order(order_id, symbol)
            logger.info(f"Canceled order {order_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {str(e)}")
            raise ExchangeError(f"Order cancellation failed: {str(e)}")

    async def get_balance(self) -> Dict[str, Any]:
        """Fetch account balance."""
        if not self._exchange:
            raise ExchangeError("Not connected to exchange")

        try:
            balance = await self._exchange.fetch_balance()

            # Convert to more readable format
            balances = {}
            for currency, data in balance.items():
                if isinstance(data, dict) and 'total' in data:
                    total = float(data['total'])
                    if total > 0:
                        balances[currency] = {
                            'total': total,
                            'free': float(data['free']),
                            'used': float(data['used'])
                        }

            logger.debug(f"Fetched balance for {len(balances)} currencies")
            return balances
        except Exception as e:
            logger.error(f"Failed to fetch balance: {str(e)}")
            raise ExchangeError(f"Balance fetch failed: {str(e)}")

    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch open orders."""
        if not self._exchange:
            raise ExchangeError("Not connected to exchange")

        try:
            orders = await self._exchange.fetch_open_orders(symbol)

            # Format orders
            formatted_orders = []
            for order in orders:
                formatted_orders.append({
                    'order_id': str(order['id']),
                    'symbol': order['symbol'],
                    'side': order['side'],
                    'type': order['type'],
                    'amount': float(order['amount']),
                    'price': float(order.get('price', 0)),
                    'filled': float(order.get('filled', 0)),
                    'remaining': float(order.get('remaining', 0)),
                    'status': order['status'],
                    'timestamp': datetime.fromtimestamp(order['timestamp'] / 1000)
                })

            logger.debug(f"Fetched {len(formatted_orders)} open orders")
            return formatted_orders
        except Exception as e:
            logger.error(f"Failed to fetch open orders: {str(e)}")
            raise ExchangeError(f"Open orders fetch failed: {str(e)}")
