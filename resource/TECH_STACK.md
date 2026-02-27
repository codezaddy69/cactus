# Trading Bot Tech Stack
## MIT-Licensed Components Only
## Commercial Use Allowed

**Project:** Automated Trading Bot  
**License Requirement:** MIT or more permissive (Apache 2.0, BSD, etc.)  
**Goal:** Build sellable trading bot product  
**Exchanges:** Binance, Robinhood, Coinbase  
**Date:** February 2026

---

# TABLE OF CONTENTS

1. [Core Architecture Overview](#1-core-architecture-overview)
2. [Exchange Connectivity](#2-exchange-connectivity)
3. [Data Storage](#3-data-storage)
4. [Back Testing Engine](#4-back-testing-engine)
5. [API & Web Framework](#5-api--web-framework)
6. [Message Queue](#6-message-queue)
7. [Monitoring & Observability](#7-monitoring--observability)
8. [Testing Framework](#8-testing-framework)
9. [Deployment & Infrastructure](#9-deployment--infrastructure)
10. [Additional Libraries](#10-additional-libraries)
11. [License Compliance Matrix](#11-license-compliance-matrix)
12. [Research Plan](#12-research-plan)

---

# 1. CORE ARCHITECTURE OVERVIEW

## System Design

```
┌─────────────────────────────────────────────────────────────┐
│                    TRADING BOT SYSTEM                       │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Binance    │    │  Robinhood   │    │   Coinbase   │
│    API       │    │    API       │    │    API       │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                    │                    │
       └────────────────────┼────────────────────┘
                            │
                   ┌────────▼────────┐
                   │  CCXT Library   │  ← MIT License
                   │  (Unified API)  │
                   └────────┬────────┘
                            │
       ┌────────────────────┼────────────────────┐
       │                    │                    │
┌──────▼──────┐    ┌────────▼────────┐    ┌─────▼──────┐
│   Strategy  │    │   Risk Manager  │    │  Position  │
│   Engine    │    │                 │    │  Tracker   │
└──────┬──────┘    └────────┬────────┘    └─────┬──────┘
       │                    │                    │
       └────────────────────┼────────────────────┘
                            │
                   ┌────────▼────────┐
                   │  Message Queue  │  ← Redis (BSD)
                   │    (Redis)      │
                   └────────┬────────┘
                            │
       ┌────────────────────┼────────────────────┐
       │                    │                    │
┌──────▼──────┐    ┌────────▼────────┐    ┌─────▼──────┐
│  Time-Series│    │   PostgreSQL    │    │   Cache    │
│   Database  │    │   (Metadata)    │    │   (Redis)  │
│ (InfluxDB)  │    └─────────────────┘    └────────────┘
└─────────────┘
       │
       │         ┌──────────────────────┐
       │         │   Monitoring Stack   │
       └────────►│  Prometheus/Grafana  │ ← MIT/Apache
                 └──────────────────────┘
```

## Why MIT License Only?

**Benefits:**
- ✅ Can sell the product commercially
- ✅ No obligation to open-source your code
- ✅ Can modify and redistribute
- ✅ Simple, clear legal terms
- ✅ Compatible with other MIT components

**Avoid:**
- ❌ GPL/LGPL (copyleft - must open source)
- ❌ AGPL (network use triggers copyleft)
- ❌ Custom/commercial licenses
- ❌ Source-available (not truly open)

---

# 2. EXCHANGE CONNECTIVITY

## Primary: CCXT Library

**Name:** CCXT (CryptoCurrency eXchange Trading Library)  
**License:** MIT License ✅  
**GitHub:** https://github.com/ccxt/ccxt  
**Stars:** 40,000+  
**Language:** Python, JavaScript, Go, C#, PHP

**What It Does:**
- Unified API for 100+ exchanges
- Market data, trading, account management
- REST and WebSocket support
- Built-in rate limiting
- Error handling and retries

**Supported Exchanges:**
- ✅ Binance (full support)
- ✅ Coinbase Pro / Coinbase Exchange
- ⚠️ Robinhood (limited - see below)

**Installation:**
```bash
pip install ccxt
```

**Basic Usage:**
```python
import ccxt

# Initialize exchange
exchange = ccxt.binance({
    'apiKey': 'YOUR_API_KEY',
    'secret': 'YOUR_SECRET',
    'enableRateLimit': True,
})

# Fetch market data
ticker = exchange.fetch_ticker('BTC/USDT')
order_book = exchange.fetch_order_book('BTC/USDT')

# Place order
order = exchange.create_market_buy_order('BTC/USDT', 0.001)
```

**Pros:**
- Battle-tested (40k+ stars)
- Massive community
- Handles exchange quirks
- Built-in rate limiting
- Async support

**Cons:**
- Large dependency
- Some exchanges need workarounds

## Alternative: Custom Exchange Clients

For Robinhood (not well supported by CCXT):

**Option 1:** Robin-Stocks
- **License:** MIT ✅
- **GitHub:** https://github.com/jmfernandes/robin_stocks
- **Purpose:** Robinhood-specific API

**Option 2:** Build Custom
Use `requests` library to directly call Robinhood API

## Exchange-Specific Libraries

### Binance
```python
# Official Python SDK
pip install python-binance  # MIT License

# Or use CCXT (recommended)
```

### Coinbase
```python
# Official SDK
pip install coinbase-advanced-py  # MIT License

# Or use CCXT
```

### Robinhood
```python
# Community library
pip install robin-stocks  # MIT License

# Or build custom with requests
```

---

# 3. DATA STORAGE

## Time-Series Database: InfluxDB 3

**Name:** InfluxDB 3 Core  
**License:** MIT/Apache 2.0 ✅ (Dual licensed)  
**GitHub:** https://github.com/influxdata/influxdb  
**Website:** https://www.influxdata.com/

**What It Does:**
- Optimized for time-series data (prices, trades, metrics)
- High write throughput (200k+ rows/sec)
- SQL-like query language (InfluxQL)
- Built-in retention policies
- Compression and downsampling

**Why For Trading:**
- Perfect for OHLCV data
- Fast queries for backtesting
- Handles high-frequency data
- Built for financial data

**Installation:**
```bash
# Docker (recommended)
docker run -d \
  --name influxdb3 \
  -p 8086:8086 \
  influxdb:3.0

# Or download binary
```

**Python Client:**
```python
pip install influxdb-client  # MIT License
```

**Usage Example:**
```python
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

client = InfluxDBClient(url="http://localhost:8086", token="my-token")
write_api = client.write_api(write_options=SYNCHRONOUS)

# Write price data
point = Point("crypto_prices") \
    .tag("exchange", "binance") \
    .tag("symbol", "BTCUSDT") \
    .field("price", 50000.0) \
    .field("volume", 100.5) \
    .time(datetime.utcnow())

write_api.write(bucket="trading_data", record=point)
```

## Alternative: QuestDB

**Name:** QuestDB  
**License:** Apache 2.0 ✅  
**GitHub:** https://github.com/questdb/questdb  
**Website:** https://questdb.io/

**Pros:**
- PostgreSQL wire protocol (use any SQL client)
- Faster than InfluxDB in benchmarks
- SQL native (no new query language)
- MIT-compatible (Apache 2.0)

## Relational Database: PostgreSQL

**Name:** PostgreSQL  
**License:** PostgreSQL License (MIT-like) ✅  
**Website:** https://www.postgresql.org/

**What It Stores:**
- User accounts
- Strategy configurations
- Trade history (aggregated)
- Account balances
- System metadata

**Installation:**
```bash
# Docker
docker run -d \
  --name postgres \
  -e POSTGRES_PASSWORD=mysecret \
  -p 5432:5432 \
  postgres:15
```

**Python Client:**
```python
pip install asyncpg  # MIT License
# or
pip install psycopg2-binary  # LGPL (avoid) → use psycopg 3 (MIT)
pip install psycopg[binary]  # MIT License
```

**Schema Example:**
```sql
-- Strategies table
CREATE TABLE strategies (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    config JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Trades table
CREATE TABLE trades (
    id SERIAL PRIMARY KEY,
    strategy_id INTEGER REFERENCES strategies(id),
    exchange VARCHAR(50),
    symbol VARCHAR(20),
    side VARCHAR(10),  -- 'buy' or 'sell'
    amount DECIMAL(18, 8),
    price DECIMAL(18, 8),
    executed_at TIMESTAMP
);
```

## Cache: Redis

**Name:** Redis  
**License:** BSD 3-Clause ✅  
**GitHub:** https://github.com/redis/redis  
**Website:** https://redis.io/

**What It Does:**
- In-memory key-value store
- Lightning fast (< 1ms latency)
- Pub/sub for real-time updates
- Data structures (lists, sets, sorted sets)

**Use Cases:**
- Real-time price cache
- Session management
- Rate limiting
- Message queue (see below)

**Installation:**
```bash
# Docker
docker run -d \
  --name redis \
  -p 6379:6379 \
  redis:7-alpine
```

**Python Client:**
```python
pip install redis  # MIT License
```

**Usage:**
```python
import redis

r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# Cache price
r.setex('BTC:price', 10, '50000')  # Expire in 10 seconds

# Get cached price
price = r.get('BTC:price')

# Pub/sub for real-time updates
pubsub = r.pubsub()
pubsub.subscribe('price_updates')
for message in pubsub.listen():
    print(message)
```

---

# 4. BACK TESTING ENGINE

## Primary: Backtesting.py

**Name:** backtesting.py  
**License:** MIT License ✅  
**GitHub:** https://github.com/kernc/backtesting.py  
**Stars:** 4,000+  
**Documentation:** https://kernc.github.io/backtesting.py/

**What It Does:**
- Backtest trading strategies on historical data
- Built-in indicators
- Performance metrics (Sharpe, drawdown, etc.)
- Interactive web-based charts
- Optimization (grid search)

**Why It's Great:**
- Simple API
- Fast execution (Cython under hood)
- Great visualizations
- MIT licensed

**Installation:**
```bash
pip install backtesting
```

**Basic Strategy:**
```python
from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import pandas as pd

class SmaCross(Strategy):
    def init(self):
        price = self.data.Close
        self.ma1 = self.I(pd.Series.rolling, price, 10).mean()
        self.ma2 = self.I(pd.Series.rolling, price, 20).mean()
    
    def next(self):
        if crossover(self.ma1, self.ma2):
            self.buy()
        elif crossover(self.ma2, self.ma1):
            self.sell()

# Load data
data = pd.read_csv('BTCUSDT.csv', parse_dates=['date'], index_col='date')

# Run backtest
bt = Backtest(data, SmaCross, cash=10000, commission=0.001)
stats = bt.run()
print(stats)

# Plot results
bt.plot()
```

## Alternative: BTester

**Name:** btester  
**License:** MIT License ✅  
**GitHub:** https://github.com/pawelkn/btester

**Pros:**
- Multi-asset portfolio backtesting
- Optimized for performance
- MIT licensed

## Alternative: Fast Trade

**Name:** fast-trade  
**License:** AGPL ❌ (Avoid - copyleft)
**Note:** AGPL requires open-sourcing network use

---

# 5. API & WEB FRAMEWORK

## Primary: FastAPI

**Name:** FastAPI  
**License:** MIT License ✅  
**GitHub:** https://github.com/tiangolo/fastapi  
**Stars:** 80,000+  
**Documentation:** https://fastapi.tiangolo.com/

**What It Does:**
- Modern, fast web framework
- Automatic API documentation
- Async support (high performance)
- Type hints with Pydantic validation
- WebSocket support for real-time data

**Why For Trading Bot:**
- REST API for bot control
- WebSocket for real-time price feeds
- Dashboard backend
- High performance (async)

**Installation:**
```bash
pip install fastapi uvicorn
```

**Basic API:**
```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class TradeRequest(BaseModel):
    symbol: str
    side: str  # 'buy' or 'sell'
    amount: float

@app.post("/trade")
async def execute_trade(trade: TradeRequest):
    # Execute trade logic
    return {"status": "success", "trade": trade}

@app.get("/portfolio")
async def get_portfolio():
    return {"balance": 10000, "positions": []}

@app.websocket("/ws/prices")
async def price_stream(websocket):
    await websocket.accept()
    while True:
        price = await get_latest_price()
        await websocket.send_json({"price": price})
```

**Run Server:**
```bash
uvicorn main:app --reload
```

**Auto-Generated Docs:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Alternative: Flask

**Name:** Flask  
**License:** BSD 3-Clause ✅  
**GitHub:** https://github.com/pallets/flask  
**Website:** https://flask.palletsprojects.com/

**Pros:**
- Simpler than FastAPI
- Huge ecosystem
- BSD licensed

**Cons:**
- Synchronous (less performant)
- Older design patterns

**Installation:**
```bash
pip install flask
```

## Dashboard UI: Dash (Plotly)

**Name:** Dash  
**License:** MIT License ✅  
**GitHub:** https://github.com/plotly/dash  
**Stars:** 24,000+  
**Website:** https://dash.plotly.com/

**What It Does:**
- Python-based web dashboard framework
- React.js under the hood (no JavaScript needed)
- Real-time updates via WebSocket
- Great for financial visualizations

**Why For Trading Bot:**
- Performance charts
- P&L tracking
- Position monitoring
- Strategy controls

**Installation:**
```bash
pip install dash plotly
```

**Basic Dashboard:**
```python
import dash
from dash import dcc, html
import plotly.graph_objs as go

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Trading Bot Dashboard"),
    
    dcc.Graph(
        id='portfolio-chart',
        figure={
            'data': [go.Scatter(x=dates, y=values)],
            'layout': go.Layout(title='Portfolio Value')
        }
    ),
    
    html.Div(id='live-price', children="BTC: $50,000"),
    
    dcc.Interval(id='interval', interval=5000)  # Update every 5s
])

if __name__ == '__main__':
    app.run_server(debug=True)
```

---

# 6. MESSAGE QUEUE

## Primary: Redis (as Message Queue)

**Name:** Redis  
**License:** BSD 3-Clause ✅  
**Already covered above**

**Use as Message Queue:**
```python
import redis
import json

r = redis.Redis()

# Producer - Send trade signal
signal = {
    'strategy': 'mean_reversion',
    'symbol': 'BTC/USDT',
    'action': 'buy',
    'timestamp': '2026-02-10T12:00:00'
}
r.lpush('trade_queue', json.dumps(signal))

# Consumer - Process signals
while True:
    _, message = r.brpop('trade_queue')
    signal = json.loads(message)
    execute_trade(signal)
```

## Alternative: Redis Streams (More Advanced)

**For complex event sourcing:**
```python
# Producer
r.xadd('market_events', {
    'exchange': 'binance',
    'symbol': 'BTC/USDT',
    'price': '50000',
    'volume': '100'
})

# Consumer Group
r.xreadgroup('traders', 'bot1', {'market_events': '>'})
```

## Alternative: Simple Python Queue

For single-process bots:
```python
from queue import Queue
import threading

trade_queue = Queue()

def worker():
    while True:
        trade = trade_queue.get()
        execute_trade(trade)
        trade_queue.task_done()

threading.Thread(target=worker, daemon=True).start()

# Add trades
trade_queue.put({'symbol': 'BTC/USDT', 'action': 'buy'})
```

---

# 7. MONITORING & OBSERVABILITY

## Metrics: Prometheus

**Name:** Prometheus  
**License:** Apache 2.0 ✅  
**GitHub:** https://github.com/prometheus/prometheus  
**Website:** https://prometheus.io/

**What It Does:**
- Time-series metrics collection
- Pull-based monitoring
- Powerful query language (PromQL)
- Alerting rules

**Metrics to Track:**
- Trade count
- P&L (Profit & Loss)
- Latency
- Error rates
- Position sizes

**Installation:**
```bash
# Docker
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  prom/prometheus
```

**Python Client:**
```python
pip install prometheus-client  # MIT License
```

**Usage:**
```python
from prometheus_client import Counter, Histogram, start_http_server

# Define metrics
trade_counter = Counter('trades_executed', 'Number of trades executed', ['symbol', 'side'])
trade_latency = Histogram('trade_latency_seconds', 'Trade execution latency')
pnl_gauge = Counter('total_pnl', 'Total P&L in USD')

# Start metrics server
start_http_server(8000)

# Record metrics
trade_counter.labels(symbol='BTC/USDT', side='buy').inc()

with trade_latency.time():
    execute_trade()

pnl_gauge.inc(profit)
```

## Visualization: Grafana

**Name:** Grafana  
**License:** AGPL ❌ (Server-side)  
**Wait:** Grafana is AGPL but you're not modifying it

**Actually:** Using Grafana as end-user is fine
**Alternative:** Use Prometheus + custom dashboard

**Better Alternative: Metabase**

**Name:** Metabase  
**License:** AGPL ❌  

**Actually Best: Build Custom Dashboard with Dash**

See section 5 above (Dash by Plotly - MIT License)

## Logging: Loguru

**Name:** Loguru  
**License:** MIT License ✅  
**GitHub:** https://github.com/Delgan/loguru  
**Stars:** 20,000+

**What It Does:**
- Simple, powerful logging
- Structured logging (JSON)
- Rotation and retention
- Async support

**Installation:**
```bash
pip install loguru
```

**Usage:**
```python
from loguru import logger
import sys

# Configure logging
logger.remove()
logger.add(sys.stdout, level="INFO")
logger.add("trading_bot.log", rotation="500 MB", retention="10 days")

# Log events
logger.info("Bot started")
logger.debug("Price update: {}", price)
logger.warning("High volatility detected")
logger.error("Trade failed: {}", error)

# Structured logging
logger.bind(strategy="mean_reversion").info("Signal generated")
```

## Alternative: Python Standard Logging

Already MIT-licensed (part of Python)

---

# 8. TESTING FRAMEWORK

## Primary: Pytest

**Name:** pytest  
**License:** MIT License ✅  
**GitHub:** https://github.com/pytest-dev/pytest  
**Stars:** 13,000+  
**Website:** https://docs.pytest.org/

**What It Does:**
- Unit testing framework
- Fixtures for setup/teardown
- Parametrized tests
- Async testing support
- Plugins ecosystem

**Installation:**
```bash
pip install pytest pytest-asyncio
```

**Example Tests:**
```python
# test_strategy.py
import pytest
from my_strategy import MeanReversionStrategy

@pytest.fixture
def strategy():
    return MeanReversionStrategy()

@pytest.fixture
def sample_data():
    return pd.read_csv('test_data.csv')

def test_strategy_initialization(strategy):
    assert strategy is not None
    assert strategy.name == "MeanReversion"

def test_signal_generation(strategy, sample_data):
    signal = strategy.generate_signal(sample_data)
    assert signal in ['buy', 'sell', 'hold']

@pytest.mark.parametrize("price,expected", [
    (45000, 'buy'),
    (55000, 'sell'),
    (50000, 'hold'),
])
def test_signal_conditions(strategy, price, expected):
    result = strategy.check_price(price)
    assert result == expected

# Async test
@pytest.mark.asyncio
async def test_trade_execution():
    result = await execute_trade('BTC/USDT', 'buy', 0.1)
    assert result['status'] == 'success'
```

**Run Tests:**
```bash
pytest -v                    # Verbose
pytest -s                    # Show print statements
pytest --cov=mybot          # With coverage
pytest -k "test_signal"     # Run specific tests
```

## Coverage: pytest-cov

**Name:** pytest-cov  
**License:** MIT License ✅

**Installation:**
```bash
pip install pytest-cov
```

**Usage:**
```bash
pytest --cov=mybot --cov-report=html
```

---

# 9. DEPLOYMENT & INFRASTRUCTURE

## Containerization: Docker

**Name:** Docker  
**License:** Apache 2.0 ✅  
**Website:** https://www.docker.com/

**Dockerfile Example:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY . .

# Run bot
CMD ["python", "main.py"]
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  trading-bot:
    build: .
    environment:
      - API_KEY=${API_KEY}
      - API_SECRET=${API_SECRET}
    depends_on:
      - redis
      - postgres
      - influxdb
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
  
  postgres:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  influxdb:
    image: influxdb:3.0
    ports:
      - "8086:8086"
    volumes:
      - influxdb_data:/var/lib/influxdb2
  
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    depends_on:
      - influxdb

volumes:
  postgres_data:
  influxdb_data:
```

## Orchestration: Docker Compose

**License:** Apache 2.0 ✅  
**Built into Docker Desktop**

For single-server deployment, Docker Compose is sufficient.

## Alternative: Kubernetes (For Scale)

**Name:** Kubernetes  
**License:** Apache 2.0 ✅

Only needed if deploying multiple bot instances across multiple servers.

---

# 10. ADDITIONAL LIBRARIES

## Data Analysis: Pandas

**Name:** pandas  
**License:** BSD 3-Clause ✅

```bash
pip install pandas
```

## Numerical Computing: NumPy

**Name:** NumPy  
**License:** BSD 3-Clause ✅

```bash
pip install numpy
```

## Technical Indicators: TA-Lib or Tulipy

**Option 1: TA-Lib (Wrapper)**
```bash
pip install TA-Lib  # MIT License (wrapper)
```
Note: Underlying C library is BSD

**Option 2: Pure Python (pandas-ta)**
```bash
pip install pandas-ta  # MIT License
```

## HTTP Client: httpx

**Name:** httpx  
**License:** BSD 3-Clause ✅

```bash
pip install httpx
```

**Why:** Async HTTP client (better than requests for trading)

## Configuration: python-dotenv

**Name:** python-dotenv  
**License:** BSD 3-Clause ✅

```bash
pip install python-dotenv
```

**Usage:**
```python
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv('API_KEY')
```

## Scheduling: APScheduler

**Name:** APScheduler  
**License:** MIT License ✅

```bash
pip install apscheduler
```

**Usage:**
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()
scheduler.add_job(check_signals, 'interval', seconds=60)
scheduler.start()
```

---

# 11. LICENSE COMPLIANCE MATRIX

| Component | License | Commercial Use | Modification | Distribution | Notes |
|-----------|---------|---------------|--------------|--------------|-------|
| **CCXT** | MIT | ✅ Yes | ✅ Yes | ✅ Yes | Perfect for exchanges |
| **InfluxDB 3** | MIT/Apache 2.0 | ✅ Yes | ✅ Yes | ✅ Yes | Time-series data |
| **PostgreSQL** | PostgreSQL License | ✅ Yes | ✅ Yes | ✅ Yes | MIT-like |
| **Redis** | BSD-3 | ✅ Yes | ✅ Yes | ✅ Yes | Cache & queue |
| **FastAPI** | MIT | ✅ Yes | ✅ Yes | ✅ Yes | Web framework |
| **Dash** | MIT | ✅ Yes | ✅ Yes | ✅ Yes | Dashboards |
| **Backtesting.py** | MIT | ✅ Yes | ✅ Yes | ✅ Yes | Back testing |
| **Pytest** | MIT | ✅ Yes | ✅ Yes | ✅ Yes | Testing |
| **Loguru** | MIT | ✅ Yes | ✅ Yes | ✅ Yes | Logging |
| **Pandas** | BSD-3 | ✅ Yes | ✅ Yes | ✅ Yes | Data analysis |
| **NumPy** | BSD-3 | ✅ Yes | ✅ Yes | ✅ Yes | Numerical computing |
| **Docker** | Apache 2.0 | ✅ Yes | ✅ Yes | ✅ Yes | Deployment |
| **Prometheus** | Apache 2.0 | ✅ Yes | ✅ Yes | ✅ Yes | Monitoring |
| **Python** | PSF License | ✅ Yes | ✅ Yes | ✅ Yes | MIT-compatible |

**All Green! ✅**

## Licenses to AVOID

| License | Why Avoid |
|---------|-----------|
| GPL-2/3 | Copyleft - must open-source your code |
| LGPL | Weak copyleft - still problematic |
| AGPL | Network copyleft - triggers on use |
| SSPL | MongoDB license - controversial |
| Custom/Commercial | Restrictive terms |

---

# 12. RESEARCH PLAN

## Phase 1: Validate Tech Stack (Week 1)

### Day 1-2: Exchange API Research
**Goal:** Confirm CCXT supports all required exchanges

**Tasks:**
- [ ] Test CCXT with Binance API (read-only keys)
- [ ] Test CCXT with Coinbase API
- [ ] Research Robinhood integration options
  - [ ] Check if CCXT supports Robinhood
  - [ ] Evaluate robin-stocks library
  - [ ] Consider building custom Robinhood client

**Deliverable:** Document which exchanges work out-of-box vs need custom code

### Day 3-4: Database Setup
**Goal:** Validate InfluxDB + PostgreSQL combo

**Tasks:**
- [ ] Install InfluxDB 3 via Docker
- [ ] Write test data (1M rows)
- [ ] Query performance test (< 100ms target)
- [ ] Install PostgreSQL
- [ ] Create schema for trades, strategies
- [ ] Test connection pooling

**Deliverable:** Working database setup with test data

### Day 5: Back Testing Validation
**Goal:** Confirm backtesting.py meets needs

**Tasks:**
- [ ] Install backtesting.py
- [ ] Run sample strategy
- [ ] Test with 1 year of BTC data
- [ ] Verify metrics calculation
- [ ] Check if custom metrics can be added

**Deliverable:** Working back test with performance metrics

## Phase 2: Architecture Design (Week 2)

### Day 1-2: Component Architecture
**Goal:** Design system components

**Tasks:**
- [ ] Define data flow diagram
- [ ] Design strategy engine interface
- [ ] Plan risk management module
- [ ] Design position tracker
- [ ] Plan message queue architecture

**Deliverable:** Architecture diagram + component specifications

### Day 3-4: API Design
**Goal:** Design REST API + WebSocket endpoints

**Tasks:**
- [ ] Design strategy management endpoints
- [ ] Design trade execution endpoints
- [ ] Design portfolio monitoring endpoints
- [ ] Plan WebSocket for real-time data
- [ ] Define authentication (JWT)

**Deliverable:** OpenAPI specification (Swagger)

### Day 5: Data Model Design
**Goal:** Design database schemas

**Tasks:**
- [ ] Design PostgreSQL schema (strategies, trades, users)
- [ ] Design InfluxDB schema (prices, metrics)
- [ ] Plan Redis key structure
- [ ] Define data retention policies

**Deliverable:** SQL schema files + InfluxDB bucket design

## Phase 3: Prototype Development (Week 3-4)

### Week 3: Core Components

**Day 1-2: Exchange Connector**
- [ ] Build CCXT wrapper class
- [ ] Implement unified API interface
- [ ] Add error handling & retries
- [ ] Add rate limiting

**Day 3-4: Data Pipeline**
- [ ] Build price feeder (WebSocket)
- [ ] Store to InfluxDB
- [ ] Cache recent prices in Redis
- [ ] Build OHLCV aggregator

**Day 5: Strategy Engine**
- [ ] Create strategy base class
- [ ] Implement mean reversion strategy
- [ ] Add signal generation
- [ ] Connect to data pipeline

### Week 4: Execution & API

**Day 1-2: Trade Execution**
- [ ] Build order manager
- [ ] Implement position tracking
- [ ] Add risk checks
- [ ] Build trade logger

**Day 3-4: FastAPI Backend**
- [ ] Set up FastAPI project
- [ ] Implement strategy endpoints
- [ ] Add trade execution endpoints
- [ ] Add WebSocket for prices

**Day 5: Dashboard**
- [ ] Build Dash dashboard
- [ ] Add portfolio chart
- [ ] Add strategy controls
- [ ] Add real-time price display

## Phase 4: Testing & Validation (Week 5)

### Day 1-2: Unit Testing
**Goal:** Write comprehensive tests

**Tasks:**
- [ ] Test strategy logic
- [ ] Test exchange connector
- [ ] Test risk manager
- [ ] Mock exchange for testing

**Target:** 80%+ code coverage

### Day 3-4: Integration Testing
**Goal:** Test full system

**Tasks:**
- [ ] Test data flow end-to-end
- [ ] Test trade execution flow
- [ ] Test error scenarios
- [ ] Load testing (100 trades/min)

### Day 5: Paper Trading
**Goal:** Test with fake money

**Tasks:**
- [ ] Deploy to testnet
- [ ] Run for 48 hours
- [ ] Verify all components work
- [ ] Fix any issues

## Phase 5: Documentation & Deployment (Week 6)

### Day 1-2: Documentation
**Tasks:**
- [ ] Write API documentation
- [ ] Write deployment guide
- [ ] Document configuration options
- [ ] Write strategy development guide

### Day 3-4: Docker Setup
**Tasks:**
- [ ] Create Dockerfile
- [ ] Create docker-compose.yml
- [ ] Add environment configuration
- [ ] Test on clean machine

### Day 5: Final Review
**Tasks:**
- [ ] Review all licenses one more time
- [ ] Ensure no GPL/AGPL dependencies
- [ ] Create LICENSE file for your code
- [ ] Add copyright headers

## Research Resources Needed

### API Documentation:
- [ ] Binance API docs
- [ ] Coinbase API docs
- [ ] Robinhood API docs (unofficial)

### Libraries to Study:
- [ ] CCXT documentation
- [ ] FastAPI tutorials
- [ ] Backtesting.py examples
- [ ] InfluxDB client docs

### Infrastructure:
- [ ] Docker best practices
- [ ] Redis data structures
- [ ] Prometheus metrics design

## Success Criteria

✅ **Week 1:** All core technologies validated  
✅ **Week 2:** Architecture designed & documented  
✅ **Week 3-4:** Working prototype with one strategy  
✅ **Week 5:** 80%+ test coverage, paper trading working  
✅ **Week 6:** Production-ready deployment  

**Final Deliverable:** MIT-licensed trading bot ready for commercial use

---

**Document Version:** 1.0  
**Last Updated:** February 2026  
**License:** MIT (for this document)  
**Next Steps:** Begin Phase 1 - Validate Exchange APIs
