"""Tests for data pipeline."""

import pytest
from datetime import datetime

from app.data.pipeline import DataPipeline
from app.core.types import Ticker, OHLCV


@pytest.fixture
def mock_exchange(mocker):
    """Create a mock exchange."""
    exchange = mocker.MagicMock()

    exchange.get_ticker.return_value = Ticker(
        symbol='BTC/USDT',
        last_price=50000.0,
        bid=49999.0,
        ask=50001.0,
        volume=1000.5,
        timestamp=datetime.utcnow()
    )

    exchange.get_ohlcv.return_value = [
        OHLCV(
            timestamp=datetime.utcnow(),
            open=49500.0,
            high=50500.0,
            low=49000.0,
            close=50000.0,
            volume=100.0
        )
    ]

    return exchange


@pytest.fixture
def mock_influxdb(mocker):
    """Create a mock InfluxDB client."""
    influxdb = mocker.MagicMock()
    influxdb.write_ticker.return_value = None
    influxdb.write_ohlcv_batch.return_value = None
    return influxdb


@pytest.fixture
def mock_redis(mocker):
    """Create a mock Redis client."""
    redis = mocker.MagicMock()
    redis.cache_ticker.return_value = None
    redis.cache_ohlcv.return_value = None
    redis.publish_price_update.return_value = None
    redis.get_cached_ticker.return_value = None
    redis.get_cached_ohlcv.return_value = None
    return redis


@pytest.mark.asyncio
async def test_pipeline_ingest_ticker(mock_exchange, mock_influxdb, mock_redis):
    """Test ticker ingestion."""
    pipeline = DataPipeline(mock_exchange, mock_influxdb, mock_redis)

    ticker = await pipeline.ingest_ticker('binance', 'BTC/USDT')

    assert ticker['symbol'] == 'BTC/USDT'
    assert ticker['last_price'] == 50000.0

    # Verify cache was called
    mock_redis.cache_ticker.assert_called_once()

    # Verify InfluxDB write was called
    mock_influxdb.write_ticker.assert_called_once()

    # Verify pub/sub was called
    mock_redis.publish_price_update.assert_called_once()


@pytest.mark.asyncio
async def test_pipeline_ingest_ohlcv(mock_exchange, mock_influxdb, mock_redis):
    """Test OHLCV ingestion."""
    pipeline = DataPipeline(mock_exchange, mock_influxdb, mock_redis)

    ohlcv_list = await pipeline.ingest_ohlcv('binance', 'BTC/USDT')

    assert len(ohlcv_list) == 1
    assert ohlcv_list[0]['close'] == 50000.0

    # Verify cache was called
    mock_redis.cache_ohlcv.assert_called_once()

    # Verify InfluxDB write was called
    mock_influxdb.write_ohlcv_batch.assert_called_once()


@pytest.mark.asyncio
async def test_pipeline_get_cached_or_fetch_ticker(mock_exchange, mock_influxdb, mock_redis):
    """Test get ticker from cache or fetch."""
    pipeline = DataPipeline(mock_exchange, mock_influxdb, mock_redis)

    # First call - no cache, should fetch
    result1 = await pipeline.get_cached_or_fetch_ticker('binance', 'BTC/USDT')
    assert result1 is not None
    assert result1['last_price'] == 50000.0

    # Second call with cache hit
    mock_redis.get_cached_ticker.return_value = {
        'symbol': 'BTC/USDT',
        'last_price': 51000.0,
        'bid': 50999.0,
        'ask': 51001.0,
        'volume': 1100.0,
        'timestamp': datetime.utcnow().isoformat()
    }

    result2 = await pipeline.get_cached_or_fetch_ticker('binance', 'BTC/USDT')
    assert result2 is not None
    assert result2['last_price'] == 51000.0
