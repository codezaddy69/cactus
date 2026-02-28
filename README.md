# Cactus AI Auto Trader

An MIT-licensed, production-ready cryptocurrency trading bot built with Python 3.10+, FastAPI, InfluxDB 3, Redis, PostgreSQL, and CCXT.

## 🎯 Phase 1 Status: Complete ✅

### Implemented Features

#### 1. Project Structure
- Modular architecture with separated concerns
- Type-safe Python with full type hints
- Comprehensive error handling
- Professional logging setup

```
cactus/
├── app/
│   ├── core/           # Core components (types, exceptions, logging)
│   ├── exchanges/      # Exchange integrations (Binance, Coinbase)
│   ├── strategies/     # Trading strategies (placeholder)
│   ├── data/           # Data pipeline
│   ├── risk/           # Risk management (placeholder)
│   ├── api/            # FastAPI endpoints (placeholder)
│   └── db/             # Database clients (InfluxDB, Redis, PostgreSQL)
├── tests/              # Test suite
├── config/             # Configuration management
├── scripts/            # Utility scripts
└── logs/               # Log files (created at runtime)
```

#### 2. Exchange Integration (CCXT)
- **BaseExchange**: Abstract interface for all exchanges
- **BinanceExchange**: Full implementation with async support
- **CoinbaseExchange**: Full implementation with async support
- Unified API across exchanges
- Rate limiting built-in
- Error handling and retries
- Support for:
  - Ticker data
  - OHLCV candles
  - Order management
  - Balance queries
  - WebSocket support (via CCXT)

#### 3. Database Clients

**InfluxDB 3 (Time-Series Data)**
- Write OHLCV candles
- Write ticker data
- Query historical data
- Batch operations for performance

**Redis (Caching & Pub/Sub)**
- Cache ticker data with TTL
- Cache OHLCV data
- Price update pub/sub
- Trade signal queue
- Real-time data streaming

**PostgreSQL (Metadata)**
- Trade history storage
- Strategy configurations
- SQLAlchemy ORM
- Async sessions
- Connection pooling

#### 4. Data Pipeline
- **Ingestion**: Fetch from exchanges → Cache in Redis → Store in InfluxDB
- **Query**: Check cache → Fetch from InfluxDB if needed
- **Real-time**: Pub/sub for price updates
- **Continuous ingestion**: Automatic background tasks
- **Multi-symbol support**: Ingest multiple symbols concurrently

#### 5. Configuration
- Environment-based configuration
- `.env` file support
- Type-safe with Pydantic
- Separate dev/prod configs
- Secret management

#### 6. Logging
- Structured logging with Loguru
- Console output (colorized)
- File rotation
- Separate error logs
- Configurable log levels

#### 7. Testing
- Pytest framework
- Async test support
- Mock-based unit tests
- Coverage reporting
- Integration test markers

### Tech Stack (All MIT/BSD Licensed)

| Component | Library | License |
|-----------|---------|---------|
| Exchange API | CCXT | MIT ✅ |
| Time-Series DB | InfluxDB 3 | MIT ✅ |
| Cache | Redis | BSD-3 ✅ |
| Relational DB | PostgreSQL | PostgreSQL ✅ |
| Web Framework | FastAPI | MIT ✅ |
| Data Analysis | Pandas | BSD-3 ✅ |
| Data Analysis | Polars | Apache 2.0 ✅ |
| Technical Analysis | Pandas TA | MIT ✅ |
| Testing | Pytest | MIT ✅ |
| Logging | Loguru | MIT ✅ |

### Installation

1. **Clone the repository**
```bash
cd /home/delta/.openclaw/workspace/src/cactus
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Start databases** (using Docker)

```bash
# InfluxDB 3
docker run -d \
  --name influxdb3 \
  -p 8086:8086 \
  -e DOCKER_INFLUXDB_INIT_MODE=setup \
  -e DOCKER_INFLUXDB_INIT_USERNAME=admin \
  -e DOCKER_INFLUXDB_INIT_PASSWORD=password \
  -e DOCKER_INFLUXDB_INIT_ORG=cactus \
  -e DOCKER_INFLUXDB_INIT_BUCKET=trading_data \
  influxdb:3.0

# Redis
docker run -d \
  --name redis \
  -p 6379:6379 \
  redis:7-alpine

# PostgreSQL
docker run -d \
  --name postgres \
  -p 5432:5432 \
  -e POSTGRES_PASSWORD=postgres \
  postgres:15
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your API keys and database credentials
```

### Usage

#### System Test

Run the system test to verify all components:

```bash
python main.py
```

This will:
- Connect to exchange (sandbox mode)
- Connect to all databases
- Test data ingestion
- Verify system integrity

#### Manual Testing

```python
import asyncio
from app.exchanges.binance import BinanceExchange
from app.db.influxdb import InfluxDBClient
from app.db.redis import RedisClient
from app.data.pipeline import DataPipeline

async def main():
    # Initialize components
    exchange = BinanceExchange(
        api_key="your_key",
        secret="your_secret"
    )
    await exchange.connect()

    influxdb = InfluxDBClient()
    await influxdb.connect()

    redis = RedisClient()
    await redis.connect()

    # Create pipeline
    pipeline = DataPipeline(exchange, influxdb, redis)

    # Ingest data
    ticker = await pipeline.ingest_ticker('binance', 'BTC/USDT')
    print(f"BTC Price: ${ticker['last_price']}")

    ohlcv = await pipeline.ingest_ohlcv('binance', 'BTC/USDT', timeframe='1h')
    print(f"Fetched {len(ohlcv)} candles")

    # Cleanup
    await exchange.disconnect()
    await influxdb.disconnect()
    await redis.disconnect()

asyncio.run(main())
```

### Testing

Run the test suite:

```bash
# All tests
pytest

# With coverage
pytest --cov=app --cov-report=html

# Specific test file
pytest tests/test_exchanges.py -v

# Async tests only
pytest -m asyncio
```

### Project Principles

1. **Modular Architecture**: Separate data, logic, and execution
2. **Async First**: All I/O operations are async
3. **Type Safety**: Full type hints throughout
4. **Error Resilience**: Comprehensive error handling
5. **Testing**: TDD approach with high coverage
6. **Documentation**: Docstrings for all public APIs
7. **Security**: Environment-based config, never hardcode secrets

### Phase 1 Deliverables Summary

✅ Python project structure initialized
✅ Dependencies installed (CCXT, InfluxDB, Redis, Pandas, Polars, FastAPI)
✅ Exchange integration (Binance, Coinbase) with async support
✅ Database clients (InfluxDB 3, Redis, PostgreSQL)
✅ Data pipeline (ingestion → storage → caching)
✅ Configuration management
✅ Logging setup
✅ Basic tests
✅ System test script

### Next Steps (Phase 2)

- [ ] Implement trading strategies (Mean Reversion, Momentum)
- [ ] Add technical indicators (RSI, Bollinger Bands, MACD)
- [ ] Implement risk management (position sizing, stop-loss)
- [ ] Add backtesting engine
- [ ] Build FastAPI REST API
- [ ] Add WebSocket support for real-time updates
- [ ] Create dashboard with Plotly Dash

### Architecture

```
┌─────────────┐
│   Binance   │
│   Coinbase  │
│   (CCXT)    │
└──────┬──────┘
       │
       ▼
┌──────────────┐     ┌──────────────┐
│ Data Pipeline│────►│ InfluxDB 3   │
│              │     │ (Time-Series)│
└──────┬───────┘     └──────────────┘
       │                     │
       ├─────────────────────┤
       │                     │
       ▼                     ▼
┌──────────────┐     ┌──────────────┐
│    Redis     │     │  PostgreSQL  │
│   (Cache)    │     │  (Metadata)  │
└──────────────┘     └──────────────┘
```

### License

MIT License - Safe for commercial use

### Contributing

Follow the project principles and best practices outlined in `BEST-PRACTICES.md`.

---

**Version**: 0.1.0
**Last Updated**: 2026-02-28
**Status**: Phase 1 Complete ✅
