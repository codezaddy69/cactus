# Strategy Component Tech Stack
## MIT-Licensed Libraries + Custom Components
## For Commercial Trading Bot Product

**Document Version:** 1.0  
**Last Updated:** February 2026  
**License:** MIT (This Document)  
**Scope:** Strategy Engine, Technical Analysis, Machine Learning, Signal Processing

---

# TABLE OF CONTENTS

1. [Executive Summary](#1-executive-summary)
2. [Strategy Engine Architecture](#2-strategy-engine-architecture)
3. [Technical Analysis Libraries](#3-technical-analysis-libraries)
4. [Machine Learning Stack](#4-machine-learning-stack)
5. [Statistical Analysis Tools](#5-statistical-analysis-tools)
6. [Signal Processing Layer](#6-signal-processing-layer)
7. [Feature Engineering Pipeline](#7-feature-engineering-pipeline)
8. [Custom Components to Build](#8-custom-components-to-build)
9. [Integration Architecture](#9-integration-architecture)
10. [Research Plan](#10-research-plan)
11. [Implementation Roadmap](#11-implementation-roadmap)

---

# 1. EXECUTIVE SUMMARY

## Strategy Component Overview

The strategy component is the "brain" of your trading bot. It needs to:
- Process market data in real-time
- Calculate technical indicators
- Generate trading signals
- Manage multiple strategies simultaneously
- Learn from historical performance
- Adapt to changing market conditions

## Tech Stack Philosophy

**Use Existing Libraries For:**
- Technical indicators (well-established math)
- Standard ML algorithms (scikit-learn)
- Statistical tests (statsmodels)

**Build Custom For:**
- Strategy orchestration layer
- Signal combination logic
- Risk integration
- Performance attribution

## Key Decisions

✅ **Use pandas-ta** (MIT) - Primary technical analysis library  
✅ **Use scikit-learn** (BSD) - Primary ML library (commercial-friendly)  
✅ **Use statsmodels** (BSD) - Statistical analysis  
⚠️ **Build custom** - Strategy engine (no good MIT alternative)  
⚠️ **Build custom** - Signal processing pipeline (proprietary advantage)  

---

# 2. STRATEGY ENGINE ARCHITECTURE

## Why Build Custom?

**Problem:** No MIT-licensed strategy orchestration frameworks exist
- FreqTrade: GPL-3 (copyleft - can't sell)
- HummingBot: Apache 2.0 but very complex
- Backtrader: GPL-3 (copyleft)

**Solution:** Build lightweight custom strategy engine

## Proposed Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    STRATEGY ENGINE                          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  STRATEGY REGISTRY (Factory Pattern)                        │
│  - Register strategies dynamically                          │
│  - Load/unload at runtime                                   │
│  - Version management                                       │
└──────────────┬──────────────────────────────────────────────┘
               │
    ┌──────────┼──────────┐
    │          │          │
┌───▼───┐ ┌───▼───┐ ┌───▼───┐
│Strategy│ │Strategy│ │Strategy│
│   A    │ │   B    │ │   C    │
└───┬───┘ └───┬───┘ └───┬───┘
    │          │          │
    └──────────┼──────────┘
               │
        ┌──────▼──────┐
        │ SIGNAL      │
        │ COMBINER    │
        │ (Custom)    │
        └──────┬──────┘
               │
        ┌──────▼──────┐
        │  RISK       │
        │  FILTER     │
        └──────┬──────┘
               │
        ┌──────▼──────┐
        │  TRADE      │
        │  EXECUTION  │
        └─────────────┘
```

## Core Components to Build

### 2.1 Strategy Base Class
```python
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import pandas as pd

class Strategy(ABC):
    """
    Abstract base class for all trading strategies.
    All strategies must inherit from this class.
    """
    
    def __init__(self, name: str, config: Dict):
        self.name = name
        self.config = config
        self.is_active = True
        self.signals: List[Signal] = []
        
    @abstractmethod
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators for the strategy.
        
        Args:
            data: DataFrame with OHLCV data
            
        Returns:
            DataFrame with indicators added
        """
        pass
    
    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> List[Signal]:
        """
        Generate trading signals based on indicators.
        
        Args:
            data: DataFrame with indicators
            
        Returns:
            List of Signal objects
        """
        pass
    
    @abstractmethod
    def should_enter_long(self, data: pd.DataFrame) -> bool:
        """Check if strategy suggests long entry"""
        pass
    
    @abstractmethod
    def should_exit_long(self, data: pd.DataFrame) -> bool:
        """Check if strategy suggests exiting long"""
        pass
    
    def get_required_data(self) -> Dict:
        """
        Return data requirements for this strategy.
        
        Returns:
            Dict with keys like:
            - timeframe: str (e.g., '1h', '1d')
            - history_bars: int (e.g., 100)
            - indicators: List[str]
        """
        return {
            'timeframe': self.config.get('timeframe', '1h'),
            'history_bars': self.config.get('history_bars', 100),
            'indicators': []
        }
```

### 2.2 Signal Class
```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

class SignalType(Enum):
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"
    CLOSE = "close"

class SignalStrength(Enum):
    WEAK = 0.3
    MODERATE = 0.6
    STRONG = 0.9

@dataclass
class Signal:
    """
    Represents a trading signal from a strategy.
    """
    strategy_name: str
    symbol: str
    signal_type: SignalType
    strength: SignalStrength
    timestamp: datetime
    price: float
    metadata: Optional[dict] = None
    
    def to_dict(self) -> dict:
        return {
            'strategy': self.strategy_name,
            'symbol': self.symbol,
            'type': self.signal_type.value,
            'strength': self.strength.value,
            'timestamp': self.timestamp.isoformat(),
            'price': self.price,
            'metadata': self.metadata or {}
        }
```

### 2.3 Strategy Registry
```python
from typing import Dict, Type

class StrategyRegistry:
    """
    Central registry for all available strategies.
    Implements factory pattern for strategy instantiation.
    """
    
    _strategies: Dict[str, Type[Strategy]] = {}
    
    @classmethod
    def register(cls, name: str, strategy_class: Type[Strategy]):
        """Register a strategy class"""
        if not issubclass(strategy_class, Strategy):
            raise ValueError("Strategy must inherit from Strategy base class")
        cls._strategies[name] = strategy_class
    
    @classmethod
    def create(cls, name: str, config: Dict) -> Strategy:
        """Create strategy instance"""
        if name not in cls._strategies:
            raise KeyError(f"Strategy '{name}' not found in registry")
        return cls._strategies[name](name, config)
    
    @classmethod
    def list_strategies(cls) -> list:
        """List all registered strategies"""
        return list(cls._strategies.keys())

# Decorator for easy registration
def register_strategy(name: str):
    def decorator(cls: Type[Strategy]):
        StrategyRegistry.register(name, cls)
        return cls
    return decorator
```

---

# 3. TECHNICAL ANALYSIS LIBRARIES

## Primary: pandas-ta

**Library:** pandas-ta  
**License:** MIT ✅  
**GitHub:** https://github.com/twopirllc/pandas-ta  
**Stars:** 6,100+  
**Indicators:** 150+  
**Last Updated:** Active

**Why This One:**
- ✅ Pure Python (no C dependencies)
- ✅ Pandas-native (works with DataFrames)
- ✅ 150+ indicators
- ✅ MIT license (commercial use OK)
- ✅ Actively maintained
- ✅ Easy to extend

**Installation:**
```bash
pip install pandas_ta
```

**Usage Examples:**

```python
import pandas as pd
import pandas_ta as ta

# Load data
df = pd.read_csv('btc_prices.csv', parse_dates=['date'], index_col='date')

# Add single indicator
df.ta.rsi(length=14, append=True)

# Add multiple indicators
df.ta.macd(append=True)  # MACD
df.ta.bbands(length=20, append=True)  # Bollinger Bands
df.ta.ema(length=50, append=True)  # EMA
df.ta.atr(length=14, append=True)  # ATR

# Add all indicators at once (be careful - slow)
# df.ta.strategy('all')

# Custom strategy
my_strategy = ta.Strategy(
    name="My Strategy",
    description="RSI and MACD",
    ta=[
        {"kind": "rsi", "length": 14},
        {"kind": "macd", "fast": 12, "slow": 26},
        {"kind": "bbands", "length": 20},
    ]
)
df.ta.strategy(my_strategy)

print(df.columns)
# Output: ['open', 'high', 'low', 'close', 'volume', 
#          'RSI_14', 'MACD_12_26_9', 'MACDh_12_26_9', 'MACDs_12_26_9',
#          'BBL_20_2.0', 'BBM_20_2.0', 'BBU_20_2.0']
```

## Alternative: ta (Technical Analysis Library)

**Library:** ta  
**License:** MIT ✅  
**GitHub:** https://github.com/bukosabino/ta  
**Stars:** 3,800+

**Simpler alternative if pandas-ta is too heavy:**
```bash
pip install ta
```

```python
from ta import add_all_ta_features
from ta.trend import MACD
from ta.momentum import RSIIndicator

# Add all features
df = add_all_ta_features(df, open="open", high="high", low="low", close="close", volume="volume")

# Or individual indicators
rsi = RSIIndicator(close=df['close'], window=14)
df['rsi'] = rsi.rsi()
```

## Custom Indicators to Build

While pandas-ta covers most needs, build custom for:

### 3.1 Liquidation Cascade Detector
```python
import pandas as pd
import numpy as np

class LiquidationCascadeDetector:
    """
    Custom indicator to detect liquidation cascades.
    Based on research from TradingView QuantAlgo.
    """
    
    def __init__(self, 
                 volume_threshold: float = 2.0,
                 acceleration_threshold: float = 1.5,
                 volatility_threshold: float = 1.3):
        self.volume_threshold = volume_threshold
        self.acceleration_threshold = acceleration_threshold
        self.volatility_threshold = volatility_threshold
    
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Detect liquidation cascades.
        
        Returns DataFrame with columns:
        - cascade_detected: bool
        - cascade_direction: str ('bullish' or 'bearish')
        - cascade_strength: float (0-1)
        """
        df = df.copy()
        
        # Tier 1: Volume Spike
        df['volume_ratio'] = df['volume'] / df['volume'].shift(1)
        df['volume_spike'] = df['volume_ratio'] > self.volume_threshold
        
        # Tier 2: Price Acceleration
        df['price_change'] = abs(df['close'] - df['open'])
        df['acceleration'] = df['price_change'] / df['price_change'].shift(1)
        df['price_acceleration'] = df['acceleration'] > self.acceleration_threshold
        
        # Tier 3: Volatility Expansion
        df['bar_range'] = df['high'] - df['low']
        df['range_expansion'] = df['bar_range'] / df['bar_range'].shift(1)
        df['volatility_spike'] = df['range_expansion'] > self.volatility_threshold
        
        # Candle Strength
        df['body_size'] = abs(df['close'] - df['open'])
        df['candle_strength'] = df['body_size'] / df['bar_range']
        df['strong_candle'] = df['candle_strength'] > 0.6
        
        # Cascade Detection
        df['cascade_detected'] = (
            df['volume_spike'] & 
            df['price_acceleration'] & 
            df['volatility_spike']
        )
        
        # Direction
        df['cascade_direction'] = np.where(
            df['cascade_detected'],
            np.where(df['close'] > df['open'], 'bullish', 'bearish'),
            'none'
        )
        
        # Strength
        df['cascade_strength'] = (
            df['volume_ratio'].fillna(0) * 0.4 +
            df['acceleration'].fillna(0) * 0.3 +
            df['range_expansion'].fillna(0) * 0.3
        ).clip(0, 1)
        
        return df
```

### 3.2 VWAP Bands
```python
class VWAPBands:
    """
    Volume-Weighted Average Price with standard deviation bands.
    """
    
    def __init__(self, std_multiplier: float = 2.0):
        self.std_multiplier = std_multiplier
    
    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate VWAP and bands.
        
        Returns DataFrame with:
        - vwap: Volume-weighted average price
        - vwap_upper: Upper band
        - vwap_lower: Lower band
        """
        df = df.copy()
        
        # Typical price
        typical_price = (df['high'] + df['low'] + df['close']) / 3
        
        # VWAP (cumulative)
        df['tp_volume'] = typical_price * df['volume']
        df['vwap'] = df['tp_volume'].cumsum() / df['volume'].cumsum()
        
        # Standard deviation
        df['deviation'] = typical_price - df['vwap']
        df['variance'] = (df['deviation'] ** 2 * df['volume']).cumsum() / df['volume'].cumsum()
        df['std'] = np.sqrt(df['variance'])
        
        # Bands
        df['vwap_upper'] = df['vwap'] + self.std_multiplier * df['std']
        df['vwap_lower'] = df['vwap'] - self.std_multiplier * df['std']
        
        return df
```

---

# 4. MACHINE LEARNING STACK

## Primary: scikit-learn

**Library:** scikit-learn  
**License:** BSD 3-Clause ✅ (Commercial-friendly)  
**GitHub:** https://github.com/scikit-learn/scikit-learn  
**Stars:** 60,000+  
**Website:** https://scikit-learn.org/

**Why BSD is OK:**
- ✅ Can sell products using it
- ✅ No requirement to open-source your code
- ✅ Just need to include license notice

**Installation:**
```bash
pip install scikit-learn
```

**Key Algorithms for Trading:**

```python
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression, RidgeClassifier
from sklearn.svm import SVC
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

# Example: Predicting price direction
import pandas as pd
import numpy as np

# Prepare features
X = df[['rsi', 'macd', 'bb_position', 'volume_ratio']].values
y = np.where(df['close'].shift(-1) > df['close'], 1, 0)  # 1 if price goes up

# Remove last row (NaN in target)
X, y = X[:-1], y[:-1]

# Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

# Scale
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Train model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train_scaled, y_train)

# Predict
predictions = model.predict(X_test_scaled)
probabilities = model.predict_proba(X_test_scaled)

# Evaluate
print(classification_report(y_test, predictions))
print(f"Accuracy: {accuracy_score(y_test, predictions)}")

# Feature importance
feature_importance = pd.DataFrame({
    'feature': ['rsi', 'macd', 'bb_position', 'volume_ratio'],
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)
```

## For Deep Learning: PyTorch

**Library:** PyTorch  
**License:** BSD 3-Clause ✅  
**GitHub:** https://github.com/pytorch/pytorch  
**Website:** https://pytorch.org/

**When to Use:**
- LSTM/GRU for time series prediction
- Transformers for pattern recognition
- Reinforcement learning

**Installation:**
```bash
pip install torch
```

**Example LSTM for Price Prediction:**
```python
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

class LSTMPricePredictor(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers, output_size):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, 
                           batch_first=True, dropout=0.2)
        self.fc = nn.Linear(hidden_size, output_size)
    
    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_size)
        
        out, _ = self.lstm(x, (h0, c0))
        out = self.fc(out[:, -1, :])
        return out

# Training loop would go here
```

## Alternative: XGBoost

**Library:** XGBoost  
**License:** Apache 2.0 ✅  
**GitHub:** https://github.com/dmlc/xgboost

**Best for:**
- Tabular data prediction
- Often outperforms Random Forest
- Built-in feature importance

```python
import xgboost as xgb

model = xgb.XGBClassifier(
    n_estimators=100,
    max_depth=5,
    learning_rate=0.1
)
model.fit(X_train, y_train)
```

## Custom ML Pipeline to Build

```python
from typing import Dict, Any
import joblib

class MLPipeline:
    """
    Custom ML pipeline for trading strategies.
    Wraps scikit-learn for strategy integration.
    """
    
    def __init__(self, model_name: str, model_config: Dict):
        self.model_name = model_name
        self.model_config = model_config
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        
    def create_model(self):
        """Factory method to create model"""
        model_type = self.model_config.get('type', 'random_forest')
        
        if model_type == 'random_forest':
            self.model = RandomForestClassifier(**self.model_config.get('params', {}))
        elif model_type == 'gradient_boosting':
            self.model = GradientBoostingClassifier(**self.model_config.get('params', {}))
        elif model_type == 'logistic_regression':
            self.model = LogisticRegression(**self.model_config.get('params', {}))
        else:
            raise ValueError(f"Unknown model type: {model_type}")
    
    def prepare_features(self, df: pd.DataFrame, feature_columns: list) -> np.ndarray:
        """Extract and scale features"""
        X = df[feature_columns].values
        if self.is_trained:
            X = self.scaler.transform(X)
        else:
            X = self.scaler.fit_transform(X)
        return X
    
    def train(self, df: pd.DataFrame, feature_columns: list, target_column: str):
        """Train the model"""
        self.create_model()
        
        X = self.prepare_features(df, feature_columns)
        y = df[target_column].values
        
        self.model.fit(X, y)
        self.is_trained = True
        
        # Log training metrics
        train_score = self.model.score(X, y)
        print(f"Training accuracy: {train_score:.4f}")
        
    def predict(self, df: pd.DataFrame, feature_columns: list) -> np.ndarray:
        """Make predictions"""
        if not self.is_trained:
            raise ValueError("Model not trained yet")
        
        X = self.prepare_features(df, feature_columns)
        return self.model.predict(X)
    
    def predict_proba(self, df: pd.DataFrame, feature_columns: list) -> np.ndarray:
        """Get prediction probabilities"""
        if not self.is_trained:
            raise ValueError("Model not trained yet")
        
        X = self.prepare_features(df, feature_columns)
        return self.model.predict_proba(X)
    
    def save(self, path: str):
        """Save model and scaler"""
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'config': self.model_config,
            'is_trained': self.is_trained
        }, path)
    
    def load(self, path: str):
        """Load model and scaler"""
        data = joblib.load(path)
        self.model = data['model']
        self.scaler = data['scaler']
        self.model_config = data['config']
        self.is_trained = data['is_trained']
```

---

# 5. STATISTICAL ANALYSIS TOOLS

## Primary: statsmodels

**Library:** statsmodels  
**License:** BSD 3-Clause ✅  
**GitHub:** https://github.com/statsmodels/statsmodels  
**Website:** https://www.statsmodels.org/

**Use For:**
- Time series analysis
- Cointegration tests (pairs trading)
- ARIMA models
- Hypothesis testing

**Installation:**
```bash
pip install statsmodels
```

**Key Examples:**

### 5.1 Cointegration Test (Pairs Trading)
```python
from statsmodels.tsa.stattools import coint, adfuller

# Test if two price series are cointegrated
score, p_value, _ = coint(df['BTC'], df['ETH'])

print(f"Cointegration test p-value: {p_value}")
if p_value < 0.05:
    print("Series are cointegrated - good for pairs trading")
else:
    print("Series are not cointegrated")

# Calculate spread
spread = df['BTC'] - df['ETH'] * hedge_ratio

# Test if spread is stationary
adf_result = adfuller(spread)
print(f"ADF test p-value: {adf_result[1]}")
```

### 5.2 Augmented Dickey-Fuller Test
```python
from statsmodels.tsa.stattools import adfuller

# Test if price series is stationary
result = adfuller(df['close'])
print(f"ADF Statistic: {result[0]}")
print(f"p-value: {result[1]}")

if result[1] < 0.05:
    print("Series is stationary")
else:
    print("Series is non-stationary (has trend)")
```

### 5.3 ARIMA Model
```python
from statsmodels.tsa.arima.model import ARIMA

# Fit ARIMA model
model = ARIMA(df['close'], order=(5, 1, 0))  # (p,d,q)
results = model.fit()

# Forecast
forecast = results.forecast(steps=10)
print(forecast)
```

## Hurst Exponent: hurst library

**Library:** hurst  
**License:** MIT ✅  
**GitHub:** https://github.com/Mottl/hurst

**Purpose:** Measure long-term memory of time series

```python
from hurst import compute_Hc

# Calculate Hurst exponent
H, c, data = compute_Hc(df['close'], kind='price', simplified=True)

print(f"Hurst Exponent: {H}")
if H < 0.5:
    print("Mean-reverting series")
elif H == 0.5:
    print("Random walk (Brownian motion)")
else:
    print("Trending series")
```

## Fractional Differentiation: fracdiff

**Library:** fracdiff  
**License:** BSD 3-Clause ✅  
**GitHub:** https://github.com/fracdiff/fracdiff

**Purpose:** Make time series stationary while preserving memory

```python
from fracdiff import Fracdiff

# Apply fractional differentiation
fd = Fracdiff(d=0.5)  # d between 0 and 1
df['close_stationary'] = fd.fit_transform(df[['close']])
```

---

# 6. SIGNAL PROCESSING LAYER

## Custom Signal Processor

```python
from typing import List, Dict
from dataclasses import dataclass
from enum import Enum

class SignalQuality(Enum):
    LOW = 0.3
    MEDIUM = 0.6
    HIGH = 0.9

@dataclass
class ProcessedSignal:
    symbol: str
    action: str  # 'buy', 'sell', 'hold'
    confidence: float
    strategy_signals: Dict[str, Signal]
    risk_score: float
    metadata: Dict

class SignalProcessor:
    """
    Process and combine signals from multiple strategies.
    Custom component - no good MIT alternative exists.
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.min_confidence = config.get('min_confidence', 0.6)
        self.agreement_threshold = config.get('agreement_threshold', 0.7)
        
    def combine_signals(self, 
                       signals: List[Signal], 
                       symbol: str,
                       current_price: float) -> ProcessedSignal:
        """
        Combine multiple strategy signals into one actionable signal.
        
        Methods supported:
        - 'unanimous': All strategies must agree
        - 'majority': >50% agreement
        - 'weighted': Weight by strategy performance
        - 'confidence': Use highest confidence signal
        """
        if not signals:
            return ProcessedSignal(
                symbol=symbol,
                action='hold',
                confidence=0.0,
                strategy_signals={},
                risk_score=0.0,
                metadata={'reason': 'no_signals'}
            )
        
        method = self.config.get('combination_method', 'weighted')
        
        if method == 'unanimous':
            return self._unanimous_consensus(signals, symbol, current_price)
        elif method == 'majority':
            return self._majority_vote(signals, symbol, current_price)
        elif method == 'weighted':
            return self._weighted_average(signals, symbol, current_price)
        else:
            return self._confidence_based(signals, symbol, current_price)
    
    def _weighted_average(self, signals, symbol, price) -> ProcessedSignal:
        """Weight signals by strategy performance"""
        
        buy_weight = 0.0
        sell_weight = 0.0
        total_weight = 0.0
        
        strategy_signals = {}
        
        for signal in signals:
            weight = self._get_strategy_weight(signal.strategy_name)
            strategy_signals[signal.strategy_name] = signal
            
            if signal.signal_type == SignalType.BUY:
                buy_weight += weight * signal.strength.value
            elif signal.signal_type == SignalType.SELL:
                sell_weight += weight * signal.strength.value
            
            total_weight += weight
        
        # Normalize
        if total_weight > 0:
            buy_score = buy_weight / total_weight
            sell_score = sell_weight / total_weight
        else:
            buy_score = sell_score = 0
        
        # Determine action
        if buy_score > sell_score and buy_score > self.min_confidence:
            action = 'buy'
            confidence = buy_score
        elif sell_score > buy_score and sell_score > self.min_confidence:
            action = 'sell'
            confidence = sell_score
        else:
            action = 'hold'
            confidence = max(buy_score, sell_score)
        
        # Calculate risk score
        risk_score = self._calculate_risk(signals)
        
        return ProcessedSignal(
            symbol=symbol,
            action=action,
            confidence=confidence,
            strategy_signals=strategy_signals,
            risk_score=risk_score,
            metadata={
                'buy_score': buy_score,
                'sell_score': sell_score,
                'signal_count': len(signals)
            }
        )
    
    def _get_strategy_weight(self, strategy_name: str) -> float:
        """Get weight based on strategy's historical performance"""
        # This would query strategy performance database
        # For now, return equal weights
        return 1.0
    
    def _calculate_risk(self, signals: List[Signal]) -> float:
        """Calculate risk score based on signal disagreement"""
        if len(signals) < 2:
            return 0.0
        
        # Count buy vs sell signals
        buys = sum(1 for s in signals if s.signal_type == SignalType.BUY)
        sells = sum(1 for s in signals if s.signal_type == SignalType.SELL)
        
        # High disagreement = high risk
        total = buys + sells
        if total == 0:
            return 0.0
        
        disagreement = abs(buys - sells) / total
        return 1.0 - disagreement  # Higher risk when disagreement is high
    
    def filter_by_risk(self, signal: ProcessedSignal) -> bool:
        """Check if signal passes risk filters"""
        
        # Minimum confidence
        if signal.confidence < self.min_confidence:
            return False
        
        # Maximum risk
        if signal.risk_score > self.config.get('max_risk', 0.5):
            return False
        
        return True
```

---

# 7. FEATURE ENGINEERING PIPELINE

## Custom Feature Engineering

```python
class FeatureEngineer:
    """
    Custom feature engineering for trading strategies.
    """
    
    def __init__(self):
        self.ta_lib = pandas_ta  # Use pandas-ta for indicators
    
    def create_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create comprehensive feature set.
        
        Categories:
        - Price-based features
        - Volume-based features
        - Technical indicators
        - Statistical features
        - Time-based features
        """
        df = df.copy()
        
        # 1. Price-based features
        df = self._add_price_features(df)
        
        # 2. Volume features
        df = self._add_volume_features(df)
        
        # 3. Technical indicators (using pandas-ta)
        df = self._add_technical_indicators(df)
        
        # 4. Statistical features
        df = self._add_statistical_features(df)
        
        # 5. Time features
        df = self._add_time_features(df)
        
        return df
    
    def _add_price_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Price-based features"""
        # Returns
        df['returns'] = df['close'].pct_change()
        df['log_returns'] = np.log(df['close'] / df['close'].shift(1))
        
        # Price position within candle
        df['body_size'] = abs(df['close'] - df['open'])
        df['upper_wick'] = df['high'] - df[['open', 'close']].max(axis=1)
        df['lower_wick'] = df[['open', 'close']].min(axis=1) - df['low']
        
        # Price changes over different periods
        for period in [1, 3, 5, 10]:
            df[f'price_change_{period}d'] = df['close'].pct_change(period)
        
        return df
    
    def _add_volume_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Volume-based features"""
        # Volume moving averages
        df['volume_sma_20'] = df['volume'].rolling(20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_sma_20']
        
        # On-balance volume
        df['obv'] = (np.sign(df['close'].diff()) * df['volume']).cumsum()
        
        # Volume-price trend
        df['vpt'] = (df['volume'] * df['returns']).cumsum()
        
        return df
    
    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Technical indicators using pandas-ta"""
        
        # Trend indicators
        df.ta.ema(length=12, append=True)
        df.ta.ema(length=26, append=True)
        df.ta.macd(append=True)
        
        # Momentum indicators
        df.ta.rsi(length=14, append=True)
        df.ta.stoch(append=True)
        
        # Volatility indicators
        df.ta.bbands(length=20, append=True)
        df.ta.atr(length=14, append=True)
        
        # Volume indicators
        df.ta.obv(append=True)
        df.ta.mfi(length=14, append=True)
        
        return df
    
    def _add_statistical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Statistical features"""
        # Rolling statistics
        for window in [10, 20, 50]:
            df[f'rolling_mean_{window}'] = df['close'].rolling(window).mean()
            df[f'rolling_std_{window}'] = df['close'].rolling(window).std()
            df[f'rolling_skew_{window}'] = df['returns'].rolling(window).skew()
            df[f'rolling_kurt_{window}'] = df['returns'].rolling(window).kurt()
        
        # Z-score
        df['zscore_20'] = (df['close'] - df['rolling_mean_20']) / df['rolling_std_20']
        
        return df
    
    def _add_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Time-based features"""
        df['hour'] = df.index.hour
        df['day_of_week'] = df.index.dayofweek
        df['month'] = df.index.month
        
        # Cyclical encoding
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        df['dow_sin'] = np.sin(2 * np.pi * df['day_of_week'] / 7)
        df['dow_cos'] = np.cos(2 * np.pi * df['day_of_week'] / 7)
        
        return df
```

---

# 8. CUSTOM COMPONENTS TO BUILD

## Priority 1: Strategy Engine
**Why:** No MIT-licensed strategy orchestration framework exists  
**Complexity:** High  
**Value:** Core differentiator  
**Timeline:** 2-3 weeks

## Priority 2: Signal Processor
**Why:** Need custom signal combination logic  
**Complexity:** Medium  
**Value:** Competitive advantage  
**Timeline:** 1 week

## Priority 3: Feature Engineering Pipeline
**Why:** Domain-specific features  
**Complexity:** Medium  
**Value:** Better predictions  
**Timeline:** 1 week

## Priority 4: ML Pipeline Wrapper
**Why:** Integrate scikit-learn with strategy engine  
**Complexity:** Medium  
**Value:** Easy model deployment  
**Timeline:** 1 week

---

# 9. INTEGRATION ARCHITECTURE

```python
# Example: Complete strategy integration

from strategy_engine import StrategyRegistry, Strategy
from signal_processor import SignalProcessor
from feature_engineer import FeatureEngineer
from ml_pipeline import MLPipeline

class IntegratedStrategy(Strategy):
    """
    Example strategy using all components.
    """
    
    def __init__(self, name, config):
        super().__init__(name, config)
        self.feature_engineer = FeatureEngineer()
        self.ml_pipeline = None
        if config.get('use_ml'):
            self.ml_pipeline = MLPipeline(
                config['model_name'],
                config['model_config']
            )
    
    def calculate_indicators(self, df):
        # Engineer features
        df = self.feature_engineer.create_features(df)
        return df
    
    def generate_signals(self, df):
        signals = []
        
        # Method 1: Rule-based
        if self.config.get('use_rules'):
            if self._rule_based_long(df):
                signals.append(Signal(
                    strategy_name=self.name,
                    symbol=self.config['symbol'],
                    signal_type=SignalType.BUY,
                    strength=SignalStrength.MODERATE,
                    timestamp=df.index[-1],
                    price=df['close'].iloc[-1]
                ))
        
        # Method 2: ML-based
        if self.ml_pipeline and self.ml_pipeline.is_trained:
            prediction = self.ml_pipeline.predict(
                df, 
                self.config['feature_columns']
            )
            if prediction[-1] == 1:
                signals.append(Signal(
                    strategy_name=self.name,
                    symbol=self.config['symbol'],
                    signal_type=SignalType.BUY,
                    strength=SignalStrength.STRONG,
                    timestamp=df.index[-1],
                    price=df['close'].iloc[-1],
                    metadata={'ml_confidence': prediction[-1]}
                ))
        
        return signals
```

---

# 10. RESEARCH PLAN

## Week 1: Library Validation

### Day 1-2: pandas-ta Deep Dive
- [ ] Install pandas-ta
- [ ] Test all 150+ indicators
- [ ] Benchmark performance on 1M rows
- [ ] Document which indicators are useful
- [ ] Test extension capabilities

### Day 3-4: scikit-learn Integration
- [ ] Test classification models
- [ ] Test regression models
- [ ] Benchmark training time
- [ ] Test model persistence (joblib)
- [ ] Document best algorithms for trading

### Day 5: statsmodels Validation
- [ ] Test cointegration functions
- [ ] Test ADF test
- [ ] Test ARIMA models
- [ ] Benchmark on price data

## Week 2: Custom Component Design

### Day 1-2: Strategy Engine Design
- [ ] Design base classes
- [ ] Design registry pattern
- [ ] Document strategy lifecycle
- [ ] Create UML diagrams

### Day 3-4: Signal Processor Design
- [ ] Design signal combination methods
- [ ] Design risk scoring
- [ ] Document filter logic
- [ ] Create test cases

### Day 5: Feature Engineering Design
- [ ] Categorize features
- [ ] Design pipeline architecture
- [ ] Document feature importance
- [ ] Create feature catalog

## Week 3: Prototype Implementation

### Day 1-2: Strategy Engine Prototype
- [ ] Implement base classes
- [ ] Implement registry
- [ ] Create 2 example strategies
- [ ] Unit tests

### Day 3-4: Signal Processor Prototype
- [ ] Implement combination methods
- [ ] Implement risk filters
- [ ] Integration tests
- [ ] Performance benchmarks

### Day 5: Feature Engineering Prototype
- [ ] Implement feature categories
- [ ] Test on historical data
- [ ] Validate features
- [ ] Documentation

## Week 4: Integration & Testing

### Day 1-2: Integration
- [ ] Connect all components
- [ ] End-to-end testing
- [ ] Performance optimization
- [ ] Bug fixes

### Day 3-4: Back Testing
- [ ] Test on 1 year of data
- [ ] Compare against benchmarks
- [ ] Analyze results
- [ ] Document findings

### Day 5: Documentation
- [ ] Write API docs
- [ ] Create usage examples
- [ ] Write strategy development guide
- [ ] Final review

---

# 11. IMPLEMENTATION ROADMAP

## Phase 1: Foundation (Weeks 1-2)
- [ ] Validate all libraries
- [ ] Design architecture
- [ ] Set up project structure

## Phase 2: Core Components (Weeks 3-5)
- [ ] Build strategy engine
- [ ] Build signal processor
- [ ] Build feature engineering pipeline
- [ ] Integrate with existing tech stack

## Phase 3: Strategy Development (Weeks 6-8)
- [ ] Implement mean reversion strategy
- [ ] Implement momentum strategy
- [ ] Implement ML-based strategy
- [ ] Implement pairs trading strategy

## Phase 4: Testing & Optimization (Weeks 9-10)
- [ ] Comprehensive back testing
- [ ] Performance optimization
- [ ] Stress testing
- [ ] Documentation

## Phase 5: Deployment (Week 11+)
- [ ] Deploy to production
- [ ] Monitor performance
- [ ] Iterate based on results

---

# LICENSE COMPLIANCE SUMMARY

## Libraries Used

| Component | Library | License | Status |
|-----------|---------|---------|--------|
| Technical Analysis | pandas-ta | MIT ✅ | Approved |
| ML Framework | scikit-learn | BSD ✅ | Approved |
| Deep Learning | PyTorch | BSD ✅ | Approved |
| Statistical Analysis | statsmodels | BSD ✅ | Approved |
| Hurst Exponent | hurst | MIT ✅ | Approved |
| Fractional Diff | fracdiff | BSD ✅ | Approved |
| Boosting | XGBoost | Apache ✅ | Approved |
| Time Series DB | InfluxDB | MIT ✅ | Approved |

## Custom Components

| Component | License | Notes |
|-----------|---------|-------|
| Strategy Engine | MIT (Your Code) | Core IP |
| Signal Processor | MIT (Your Code) | Competitive Advantage |
| Feature Engineering | MIT (Your Code) | Proprietary Features |
| ML Pipeline | MIT (Your Code) | Integration Layer |

## All Green! ✅

Everything is commercially viable. You can:
- ✅ Sell the product
- ✅ Keep code private
- ✅ Modify libraries
- ✅ Distribute freely

---

**Document Version:** 1.0  
**Next Steps:** Begin Week 1 - Library Validation  
**Estimated Timeline:** 11 weeks to production-ready strategies  
**Commercial Viability:** ✅ APPROVED
