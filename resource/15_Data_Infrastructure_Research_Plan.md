# DATA INFRASTRUCTURE MODULE - RESEARCH PLAN
## Complete Architecture for Market Data Pipeline

**Document Version:** 1.0  
**Last Updated:** 2026-02-10  
**Priority:** CRITICAL - Phase 1 Foundation  
**Estimated Development:** 2-3 Weeks

---

## Executive Summary

The Data Infrastructure Module is the foundation of the entire trading bot system. Without reliable, low-latency data, no strategy can succeed. This research plan draws from industry best practices, cryptocurrency exchange APIs, and time-series database implementations to create a production-ready data pipeline.

**Key Sources:**
1. CCXT Official Documentation - https://docs.ccxt.com/
2. InfluxDB 3 Documentation - https://docs.influxdata.com/
3. Redis Best Practices - https://redis.io/docs/
4. Pandas Performance Guide - https://pandas.pydata.org/docs/

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                         DATA INFRASTRUCTURE ARCHITECTURE                             │
└─────────────────────────────────────────────────────────────────────────────────────┘

EXCHANGE LAYER (CCXT - MIT License)
├── Binance API
├── Coinbase API  
├── Hyperliquid API
└── WebSocket feeds for real-time
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  DATA PIPELINE LAYER                                                                 │
│  ┌─────────────────┐  ┌──────────────────┐  ┌──────────────────┐                   │
│  │ Ingestion       │  │ Processing       │  │ Distribution     │                   │
│  │ • CCXT Adapter  │  │ • Validation     │  │ • Strategy Feed  │                   │
│  │ • Rate Limiting │  │ • Normalization  │  │ • Backfill API   │                   │
│  │ • Error Retry   │  │ • Aggregation    │  │ • Alert Stream   │                   │
│  └─────────────────┘  └──────────────────┘  └──────────────────┘                   │
└─────────────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
STORAGE LAYER
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐            │
│  │ InfluxDB 3         │  │ PostgreSQL         │  │ Redis              │            │
│  │ (Time-Series)      │  │ (Metadata)         │  │ (Cache/State)      │            │
│  │ • OHLCV            │  │ • Trades           │  │ • Latest Prices    │            │
│  │ • Tick Data        │  │ • Positions        │  │ • Session State    │            │
│  │ • Indicators       │  │ • Strategy Config  │  │ • Pub/Sub          │            │
│  └────────────────────┘  └────────────────────┘  └────────────────────┘            │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Exchange Integration Research

### 1.1 CCXT Library Deep Dive

**Source:** CCXT Official Documentation (https://docs.ccxt.com/)

**Key Findings:**

```python
# CCXT Architecture Benefits
"""
1. Unified API across 100+ exchanges
2. Async/await support for concurrent operations
3. Built-in rate limiting and retry logic
4. WebSocket support for real-time data
5. Comprehensive error handling
"""

# Implementation Pattern
import ccxt.async_support as ccxt
import asyncio

class ExchangeManager:
    """
    Manages connections to multiple exchanges using CCXT.
    Based on: CCXT Documentation + Best Practices
    """
    
    def __init__(self, config):
        self.exchanges = {}
        self.config = config
        
    async def initialize_exchanges(self):
        """
        Initialize exchange connections with rate limiting.
        Source: https://docs.ccxt.com/#/README?id=rate-limit
        """
        for exchange_id, api_config in self.config.items():
            exchange_class = getattr(ccxt, exchange_id)
            
            exchange = exchange_class({
                'apiKey': api_config['api_key'],
                'secret': api_config['secret'],
                'enableRateLimit': True,  # Critical - prevents bans
                'options': {
                    'defaultType': 'spot',  # or 'future'
                }
            })
            
            # Test connection
            await exchange.load_markets()
            self.exchanges[exchange_id] = exchange
            
    async def fetch_ohlcv(self, exchange_id, symbol, timeframe, since=None, limit=500):
        """
        Fetch OHLCV data with error handling and retry.
        
        Source: https://docs.ccxt.com/#/README?id=ohlcv-candlestick-charts
        """
        exchange = self.exchanges[exchange_id]
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                ohlcv = await exchange.fetch_ohlcv(
                    symbol, 
                    timeframe, 
                    since=since, 
                    limit=limit
                )
                return ohlcv
                
            except ccxt.NetworkError as e:
                # Network error - retry with backoff
                wait_time = 2 ** attempt
                await asyncio.sleep(wait_time)
                continue
                
            except ccxt.ExchangeError as e:
                # Exchange error - log and skip
                print(f"Exchange error: {e}")
                return None
                
        return None
```

### 1.2 Exchange-Specific Considerations

**Source:** CCXT Exchange Documentation + Exchange API Docs

**Binance (Primary Exchange):**
```python
# Binance Specific Configuration
binance_config = {
    'apiKey': 'YOUR_API_KEY',
    'secret': 'YOUR_SECRET',
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future',  # Use futures for leverage
        'adjustForTimeDifference': True,
    },
    # Rate limits: 1200 request weight per minute for most endpoints
    # https://binance-docs.github.io/apidocs/futures/en/#limits
}

# Binance Data Limits
"""
- REST API: 1200 request weight per minute
- WebSocket: 5 connections per IP
- Historical klines: 1000 candles per request
- Rate limit headers: X-MBX-USED-WEIGHT-1M
"""
```

**Coinbase (Secondary):**
```python
# Coinbase Configuration
coinbase_config = {
    'apiKey': 'YOUR_API_KEY',
    'secret': 'YOUR_SECRET',
    'enableRateLimit': True,
    'options': {
        'fetchCurrencies': False,  # Optimization
    }
}

# Coinbase Rate Limits
"""
- 10 requests per second for public endpoints
- 15 requests per second for private endpoints
- More conservative than Binance
"""
```

**Hyperliquid (Futures):**
```python
# Hyperliquid Configuration
"""
Hyperliquid uses custom API, not directly in CCXT yet.
Requires custom implementation.

API Docs: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api

Key Features:
- Low fees (0.01% taker, 0% maker)
- High leverage (up to 50x)
- Real-time WebSocket feeds
"""
```

### 1.3 WebSocket Real-Time Data

**Source:** CCXT WebSocket Documentation

```python
# WebSocket Implementation for Real-Time Data
import ccxt.pro as ccxt_pro

class WebSocketDataFeed:
    """
    Real-time data feed using WebSocket.
    Lower latency than REST polling.
    
    Source: https://docs.ccxt.com/#/ccxt.pro.manual
    """
    
    def __init__(self, exchange_id, symbols, on_tick_callback):
        self.exchange_id = exchange_id
        self.symbols = symbols
        self.on_tick = on_tick_callback
        self.exchange = None
        
    async def start(self):
        """Start WebSocket connection"""
        exchange_class = getattr(ccxt_pro, self.exchange_id)
        self.exchange = exchange_class({'enableRateLimit': True})
        
        # Subscribe to tickers
        await self.exchange.load_markets()
        
        # Start receiving data
        while True:
            try:
                for symbol in self.symbols:
                    ticker = await self.exchange.watch_ticker(symbol)
                    self.on_tick(symbol, ticker)
                    
            except Exception as e:
                print(f"WebSocket error: {e}")
                await asyncio.sleep(5)  # Reconnect delay
```

---

## Phase 2: Data Processing Pipeline

### 2.1 Data Validation & Cleaning

**Source:** Pandas Data Cleaning Best Practices + Financial Data Research

```python
# data/validation.py
"""
Data validation and cleaning pipeline.
Ensures data integrity before storage.
"""

import pandas as pd
import numpy as np

class DataValidator:
    """
    Validates OHLCV data for quality and consistency.
    
    Based on: Pandas docs + Academic research on financial data quality
    """
    
    @staticmethod
    def validate_ohlcv(df: pd.DataFrame) -> tuple:
        """
        Validate OHLCV DataFrame.
        
        Returns: (is_valid, issues_list)
        """
        issues = []
        
        # 1. Check required columns
        required = ['open', 'high', 'low', 'close', 'volume']
        missing = [c for c in required if c not in df.columns]
        if missing:
            issues.append(f"Missing columns: {missing}")
        
        # 2. Check for nulls
        null_counts = df[required].isnull().sum()
        if null_counts.any():
            issues.append(f"Null values found: {null_counts[null_counts > 0].to_dict()}")
        
        # 3. Check OHLC logic
        # High should be >= Low, Open, Close
        invalid_high = (df['high'] < df[['open', 'low', 'close']].max(axis=1)).sum()
        if invalid_high > 0:
            issues.append(f"{invalid_high} rows where high < max(open, low, close)")
        
        # Low should be <= High, Open, Close
        invalid_low = (df['low'] > df[['open', 'high', 'close']].min(axis=1)).sum()
        if invalid_low > 0:
            issues.append(f"{invalid_low} rows where low > min(open, high, close)")
        
        # 4. Check for zero or negative prices
        for col in ['open', 'high', 'low', 'close']:
            invalid = (df[col] <= 0).sum()
            if invalid > 0:
                issues.append(f"{invalid} rows with invalid {col} (<= 0)")
        
        # 5. Check for outliers (5 standard deviations)
        for col in ['open', 'high', 'low', 'close']:
            mean = df[col].mean()
            std = df[col].std()
            outliers = (abs(df[col] - mean) > 5 * std).sum()
            if outliers > 0:
                issues.append(f"{outliers} outliers in {col} (> 5 std dev)")
        
        # 6. Check timestamp continuity
        if isinstance(df.index, pd.DatetimeIndex):
            freq = pd.infer_freq(df.index)
            if freq is None:
                # Check for gaps
                gaps = df.index.to_series().diff() > pd.Timedelta(hours=2)
                n_gaps = gaps.sum()
                if n_gaps > 0:
                    issues.append(f"{n_gaps} gaps > 2 hours detected")
        
        is_valid = len(issues) == 0
        return is_valid, issues
    
    @staticmethod
    def clean_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean OHLCV data by fixing common issues.
        """
        df = df.copy()
        
        # Remove duplicates
        df = df[~df.index.duplicated(keep='first')]
        
        # Sort by timestamp
        df.sort_index(inplace=True)
        
        # Forward fill small gaps (up to 3 periods)
        df = df.fillna(method='ffill', limit=3)
        
        # Fix OHLC consistency
        df['high'] = df[['open', 'high', 'low', 'close']].max(axis=1)
        df['low'] = df[['open', 'high', 'low', 'close']].min(axis=1)
        
        # Remove rows with zero volume
        df = df[df['volume'] > 0]
        
        return df
```

### 2.2 Data Normalization

```python
# data/normalization.py
"""
Normalize data from different exchanges to common format.
"""

class DataNormalizer:
    """
    Normalizes data from various exchanges to consistent format.
    """
    
    COLUMN_MAPPING = {
        'binance': {
            'Open': 'open',
            'High': 'high', 
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        },
        'coinbase': {
            'open': 'open',
            'high': 'high',
            'low': 'low',
            'close': 'close',
            'volume': 'volume'
        }
    }
    
    @staticmethod
    def normalize(exchange_id: str, df: pd.DataFrame) -> pd.DataFrame:
        """
        Normalize data to standard format.
        """
        df = df.copy()
        
        # Apply column mapping
        if exchange_id in DataNormalizer.COLUMN_MAPPING:
            mapping = DataNormalizer.COLUMN_MAPPING[exchange_id]
            df = df.rename(columns=mapping)
        
        # Ensure lowercase columns
        df.columns = [c.lower() for c in df.columns]
        
        # Ensure datetime index
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        
        return df
```

---

## Phase 3: Time-Series Database (InfluxDB)

### 3.1 InfluxDB 3 Schema Design

**Source:** InfluxDB Documentation (https://docs.influxdata.com/)

```python
# storage/influxdb_schema.py
"""
InfluxDB 3 schema design for trading data.
Optimized for time-series queries.

Source: https://docs.influxdata.com/influxdb/v2/write-data/best-practices/
"""

"""
BUCKET: market_data

MEASUREMENT: ohlcv
TAGS:
  - symbol (e.g., "BTC/USDT")
  - exchange (e.g., "binance")
  - timeframe (e.g., "1h", "4h")
FIELDS:
  - open (float)
  - high (float)
  - low (float)
  - close (float)
  - volume (float)
TIMESTAMP: candle close time

Example Query:
FROM(bucket: "market_data")
  |> range(start: -7d)
  |> filter(fn: (r) => r._measurement == "ohlcv")
  |> filter(fn: (r) => r.symbol == "BTC/USDT")
  |> filter(fn: (r) => r.exchange == "binance")
  |> filter(fn: (r) => r._field == "close")
"""

# Python Implementation
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

class InfluxDBManager:
    """
    Manages InfluxDB connection and operations.
    """
    
    def __init__(self, url, token, org, bucket):
        self.client = InfluxDBClient(url=url, token=token, org=org)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.query_api = self.client.query_api()
        self.bucket = bucket
        self.org = org
        
    def write_ohlcv(self, symbol, exchange, timeframe, df):
        """
        Write OHLCV data to InfluxDB.
        
        Source: https://docs.influxdata.com/influxdb/v2/write-data/
        """
        points = []
        
        for timestamp, row in df.iterrows():
            point = Point("ohlcv") \
                .tag("symbol", symbol) \
                .tag("exchange", exchange) \
                .tag("timeframe", timeframe) \
                .field("open", float(row['open'])) \
                .field("high", float(row['high'])) \
                .field("low", float(row['low'])) \
                .field("close", float(row['close'])) \
                .field("volume", float(row['volume'])) \
                .time(timestamp)
            
            points.append(point)
        
        # Batch write for efficiency
        self.write_api.write(bucket=self.bucket, record=points)
        
    def query_ohlcv(self, symbol, exchange, timeframe, start, stop=None):
        """
        Query OHLCV data from InfluxDB.
        
        Source: https://docs.influxdata.com/influxdb/v2/query-data/
        """
        if stop is None:
            stop = "now()"
        
        query = f'''
        from(bucket: "{self.bucket}")
          |> range(start: {start}, stop: {stop})
          |> filter(fn: (r) => r._measurement == "ohlcv")
          |> filter(fn: (r) => r.symbol == "{symbol}")
          |> filter(fn: (r) => r.exchange == "{exchange}")
          |> filter(fn: (r) => r.timeframe == "{timeframe}")
          |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
        '''
        
        result = self.query_api.query_data_frame(query, org=self.org)
        return result
```

### 3.2 Retention Policies

```python
# Data Retention Strategy
"""
InfluxDB Retention Policies:

1. Raw Tick Data (if collected)
   - Duration: 7 days
   - Precision: Millisecond
   - Use: Real-time strategies only

2. OHLCV 1-Minute
   - Duration: 90 days
   - Precision: Minute
   - Use: Backtesting, microstructure

3. OHLCV 1-Hour (Primary)
   - Duration: 2 years
   - Precision: Hour
   - Use: Strategy signals, backtesting

4. OHLCV 1-Day
   - Duration: 5 years (infinite)
   - Precision: Day
   - Use: Long-term analysis, regime detection
"""

# Implementation
class RetentionManager:
    """
    Manages data retention policies.
    """
    
    POLICIES = {
        'raw_ticks': {'duration': '7d', 'replication': 1},
        'ohlcv_1m': {'duration': '90d', 'replication': 1},
        'ohlcv_1h': {'duration': '2y', 'replication': 1},
        'ohlcv_1d': {'duration': 'INF', 'replication': 1}
    }
```

---

## Phase 4: Redis Cache Layer

### 4.1 Redis Architecture

**Source:** Redis Documentation (https://redis.io/docs/)

```python
# storage/redis_manager.py
"""
Redis cache for high-speed data access.
Used for latest prices, session state, and pub/sub.

Source: https://redis.io/docs/data-types/
"""

import redis
import json
from datetime import datetime, timedelta

class RedisManager:
    """
    Manages Redis connections and operations.
    """
    
    def __init__(self, host='localhost', port=6379, db=0):
        self.client = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True
        )
        
    def cache_latest_price(self, symbol, exchange, price_data):
        """
        Cache latest price with TTL.
        
        Source: https://redis.io/commands/set/
        """
        key = f"price:{exchange}:{symbol}"
        
        # Set with 5 minute TTL
        self.client.setex(
            key,
            timedelta(minutes=5),
            json.dumps(price_data)
        )
        
    def get_latest_price(self, symbol, exchange):
        """Retrieve latest cached price"""
        key = f"price:{exchange}:{symbol}"
        data = self.client.get(key)
        
        if data:
            return json.loads(data)
        return None
        
    def publish_tick(self, channel, tick_data):
        """
        Publish tick to subscribers.
        Used for real-time strategy updates.
        
        Source: https://redis.io/topics/pubsub
        """
        self.client.publish(channel, json.dumps(tick_data))
        
    def cache_indicator(self, symbol, indicator_name, value, ttl=300):
        """Cache calculated indicator value"""
        key = f"indicator:{symbol}:{indicator_name}"
        self.client.setex(key, ttl, str(value))
```

### 4.2 Redis Data Structures

```python
# Redis Usage Patterns

"""
1. Latest Prices (String with TTL)
   Key: price:binance:BTC/USDT
   Value: {"price": 45000.50, "timestamp": "2026-01-15T10:30:00Z"}
   TTL: 300 seconds

2. Order Book Snapshots (Hash)
   Key: orderbook:binance:BTC/USDT
   Fields: bids, asks, timestamp
   TTL: 60 seconds

3. Trade Log (List)
   Key: trades:mean_reversion
   Values: List of recent trades
   Max Length: 1000 (LRU eviction)

4. Session State (Hash)
   Key: session:strategy_id
   Fields: position, P&L, status
   TTL: Session-based

5. Pub/Sub Channels
   Channel: ticks:BTC/USDT
   Subscribers: Strategy modules
"""
```

---

## Phase 5: PostgreSQL Metadata Store

### 5.1 Schema Design

```python
# storage/postgres_schema.py
"""
PostgreSQL schema for metadata and relational data.
Not for time-series (use InfluxDB for that).

Source: https://www.postgresql.org/docs/current/
"""

"""
TABLES:

1. trades
   - id (PK)
   - strategy_id (FK)
   - symbol
   - side (buy/sell)
   - entry_price
   - exit_price
   - quantity
   - pnl
   - entry_time
   - exit_time
   - status

2. positions
   - id (PK)
   - strategy_id (FK)
   - symbol
   - side
   - quantity
   - avg_price
   - unrealized_pnl
   - opened_at
   - status

3. strategies
   - id (PK)
   - name
   - type
   - parameters (JSON)
   - enabled
   - created_at

4. performance_metrics
   - id (PK)
   - strategy_id (FK)
   - date
   - sharpe_ratio
   - total_return
   - max_drawdown
   - win_rate
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Trade(Base):
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True)
    strategy_id = Column(Integer, ForeignKey('strategies.id'))
    symbol = Column(String)
    side = Column(String)  # buy/sell
    entry_price = Column(Float)
    exit_price = Column(Float)
    quantity = Column(Float)
    pnl = Column(Float)
    entry_time = Column(DateTime)
    exit_time = Column(DateTime)
    status = Column(String)  # open/closed
```

---

## Phase 6: Implementation Timeline

### Week 1: CCXT Integration & Data Download
- Day 1-2: Set up CCXT connections
- Day 3-4: Implement data download scripts
- Day 5-7: Download 2 years historical data

### Week 2: Database Setup
- Day 1-2: Install and configure InfluxDB
- Day 3-4: Set up PostgreSQL
- Day 5-7: Configure Redis

### Week 3: Pipeline Implementation
- Day 1-3: Data validation and normalization
- Day 4-5: Write pipeline (exchange → databases)
- Day 6-7: Query APIs for strategies

### Week 4: Testing & Optimization
- Day 1-3: Performance testing
- Day 4-5: Latency optimization
- Day 6-7: Documentation and monitoring

---

## Performance Targets

| Metric | Target | Acceptable |
|--------|--------|------------|
| Data Latency (REST) | < 500ms | < 1s |
| Data Latency (WebSocket) | < 100ms | < 200ms |
| Query Speed (recent data) | < 50ms | < 100ms |
| Query Speed (historical) | < 500ms | < 1s |
| Storage Efficiency | 1GB/month | 2GB/month |
| Uptime | 99.9% | 99.5% |

---

## Success Criteria

- [ ] Can fetch real-time data from 2+ exchanges
- [ ] Historical data backfill working (2 years)
- [ ] All three databases operational (InfluxDB, PostgreSQL, Redis)
- [ ] Data validation catches > 95% of quality issues
- [ ] Query latency < 100ms for recent data
- [ ] No data gaps > 1 hour in production

---

*Data Infrastructure Research Plan Complete*
*Ready for Implementation Phase*
