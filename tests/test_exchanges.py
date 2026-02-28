"""Tests for exchange integrations."""

import pytest
from datetime import datetime

from app.exchanges.binance import BinanceExchange
from app.core.exceptions import ExchangeError, RateLimitError


@pytest.mark.asyncio
async def test_binance_connection():
    """Test Binance connection initialization."""
    exchange = BinanceExchange(
        api_key="test_key",
        secret="test_secret",
        sandbox=True
    )

    await exchange.connect()
    assert exchange._exchange is not None

    await exchange.disconnect()
    assert exchange._exchange is None


@pytest.mark.asyncio
async def test_binance_no_credentials_error():
    """Test that missing credentials raise appropriate error."""
    exchange = BinanceExchange(api_key=None, secret=None)

    with pytest.raises(ExchangeError):
        await exchange.get_balance()


@pytest.mark.asyncio
async def test_binance_ticker_mock(mocker):
    """Test ticker fetch with mocked exchange."""
    # Mock the CCXT exchange
    mock_exchange = mocker.MagicMock()
    mock_exchange.fetch_ticker.return_value = {
        'symbol': 'BTC/USDT',
        'last': 50000.0,
        'bid': 49999.0,
        'ask': 50001.0,
        'quoteVolume': 1000.5,
        'timestamp': 1704067200000  # 2024-01-01
    }

    exchange = BinanceExchange(sandbox=True)
    exchange._exchange = mock_exchange

    ticker = await exchange.get_ticker('BTC/USDT')

    assert ticker['symbol'] == 'BTC/USDT'
    assert ticker['last_price'] == 50000.0
    assert ticker['bid'] == 49999.0
    assert ticker['ask'] == 50001.0
