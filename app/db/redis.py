"""Redis client for caching and pub/sub."""

from typing import Optional, Dict, Any, List
import json
import redis.asyncio as redis
from redis.asyncio import Redis

from app.core.types import Ticker, OHLCV
from app.core.exceptions import DatabaseError
from app.core.logging_config import logger
from config.settings import settings


class RedisClient:
    """Redis client for caching and message queue."""

    def __init__(
        self,
        url: Optional[str] = None,
        password: Optional[str] = None,
        db: Optional[int] = None
    ):
        """
        Initialize Redis client.

        Args:
            url: Redis connection URL
            password: Redis password (optional)
            db: Database number (default: 0)
        """
        self.url = url or settings.redis_url
        self.password = password or settings.redis_password
        self.db = db or settings.redis_db

        self._client: Optional[Redis] = None

    async def connect(self) -> None:
        """Establish connection to Redis."""
        try:
            self._client = redis.from_url(
                self.url,
                password=self.password,
                db=self.db,
                encoding="utf-8",
                decode_responses=True
            )

            # Test connection
            await self._client.ping()
            logger.info(f"Connected to Redis at {self.url}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {str(e)}")
            raise DatabaseError(f"Redis connection failed: {str(e)}")

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("Disconnected from Redis")

    # ==================== CACHING ====================

    async def cache_ticker(self, exchange: str, symbol: str, ticker: Ticker, ttl: int = 10) -> None:
        """
        Cache ticker data with TTL.

        Args:
            exchange: Exchange name
            symbol: Trading pair symbol
            ticker: Ticker data
            ttl: Time to live in seconds (default: 10)
        """
        if not self._client:
            raise DatabaseError("Not connected to Redis")

        try:
            key = f"ticker:{exchange}:{symbol}"
            data = {
                'symbol': ticker['symbol'],
                'last_price': ticker['last_price'],
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'volume': ticker['volume'],
                'timestamp': ticker['timestamp'].isoformat()
            }

            await self._client.setex(key, ttl, json.dumps(data))
            logger.debug(f"Cached ticker for {symbol}")
        except Exception as e:
            logger.error(f"Failed to cache ticker: {str(e)}")
            raise DatabaseError(f"Ticker cache failed: {str(e)}")

    async def get_cached_ticker(self, exchange: str, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get cached ticker data.

        Args:
            exchange: Exchange name
            symbol: Trading pair symbol

        Returns:
            Cached ticker data or None if not found
        """
        if not self._client:
            raise DatabaseError("Not connected to Redis")

        try:
            key = f"ticker:{exchange}:{symbol}"
            data = await self._client.get(key)

            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Failed to get cached ticker: {str(e)}")
            raise DatabaseError(f"Cached ticker fetch failed: {str(e)}")

    async def cache_ohlcv(
        self,
        exchange: str,
        symbol: str,
        timeframe: str,
        ohlcv: OHLCV,
        ttl: int = 3600
    ) -> None:
        """
        Cache OHLCV data with TTL.

        Args:
            exchange: Exchange name
            symbol: Trading pair symbol
            timeframe: Timeframe (1h, 4h, 1d)
            ohlcv: OHLCV data
            ttl: Time to live in seconds (default: 3600)
        """
        if not self._client:
            raise DatabaseError("Not connected to Redis")

        try:
            key = f"ohlcv:{exchange}:{symbol}:{timeframe}"
            data = {
                'timestamp': ohlcv['timestamp'].isoformat(),
                'open': ohlcv['open'],
                'high': ohlcv['high'],
                'low': ohlcv['low'],
                'close': ohlcv['close'],
                'volume': ohlcv['volume']
            }

            await self._client.setex(key, ttl, json.dumps(data))
            logger.debug(f"Cached OHLCV for {symbol}")
        except Exception as e:
            logger.error(f"Failed to cache OHLCV: {str(e)}")
            raise DatabaseError(f"OHLCV cache failed: {str(e)}")

    async def get_cached_ohlcv(
        self,
        exchange: str,
        symbol: str,
        timeframe: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached OHLCV data.

        Args:
            exchange: Exchange name
            symbol: Trading pair symbol
            timeframe: Timeframe

        Returns:
            Cached OHLCV data or None if not found
        """
        if not self._client:
            raise DatabaseError("Not connected to Redis")

        try:
            key = f"ohlcv:{exchange}:{symbol}:{timeframe}"
            data = await self._client.get(key)

            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Failed to get cached OHLCV: {str(e)}")
            raise DatabaseError(f"Cached OHLCV fetch failed: {str(e)}")

    # ==================== PUB/SUB ====================

    async def publish_price_update(self, channel: str, data: Dict[str, Any]) -> None:
        """
        Publish price update to channel.

        Args:
            channel: Channel name
            data: Price data to publish
        """
        if not self._client:
            raise DatabaseError("Not connected to Redis")

        try:
            await self._client.publish(channel, json.dumps(data))
            logger.debug(f"Published price update to {channel}")
        except Exception as e:
            logger.error(f"Failed to publish price update: {str(e)}")
            raise DatabaseError(f"Price update publish failed: {str(e)}")

    async def subscribe_price_updates(self, channel: str) -> None:
        """
        Subscribe to price update channel.

        Args:
            channel: Channel name
        """
        if not self._client:
            raise DatabaseError("Not connected to Redis")

        try:
            pubsub = self._client.pubsub()
            await pubsub.subscribe(channel)
            logger.info(f"Subscribed to price updates on {channel}")
            return pubsub
        except Exception as e:
            logger.error(f"Failed to subscribe to price updates: {str(e)}")
            raise DatabaseError(f"Price update subscription failed: {str(e)}")

    # ==================== MESSAGE QUEUE ====================

    async def push_trade_signal(self, signal: Dict[str, Any]) -> None:
        """
        Push trade signal to queue.

        Args:
            signal: Trade signal data
        """
        if not self._client:
            raise DatabaseError("Not connected to Redis")

        try:
            await self._client.lpush('trade_signals', json.dumps(signal))
            logger.debug(f"Pushed trade signal to queue")
        except Exception as e:
            logger.error(f"Failed to push trade signal: {str(e)}")
            raise DatabaseError(f"Trade signal push failed: {str(e)}")

    async def pop_trade_signal(self, timeout: int = 5) -> Optional[Dict[str, Any]]:
        """
        Pop trade signal from queue (blocking).

        Args:
            timeout: Timeout in seconds

        Returns:
            Trade signal or None if timeout
        """
        if not self._client:
            raise DatabaseError("Not connected to Redis")

        try:
            result = await self._client.brpop('trade_signals', timeout=timeout)
            if result:
                _, data = result
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Failed to pop trade signal: {str(e)}")
            raise DatabaseError(f"Trade signal pop failed: {str(e)}")

    async def get_queue_length(self, queue_name: str = 'trade_signals') -> int:
        """
        Get length of queue.

        Args:
            queue_name: Queue name

        Returns:
            Queue length
        """
        if not self._client:
            raise DatabaseError("Not connected to Redis")

        try:
            return await self._client.llen(queue_name)
        except Exception as e:
            logger.error(f"Failed to get queue length: {str(e)}")
            raise DatabaseError(f"Queue length check failed: {str(e)}")
