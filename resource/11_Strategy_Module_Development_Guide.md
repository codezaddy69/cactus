# Strategy Module - Complete Development Guide

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Core Components](#core-components)
4. [Implementation Guide](#implementation-guide)
5. [Development Workflow](#development-workflow)
6. [Testing & Validation](#testing--validation)
7. [Integration Patterns](#integration-patterns)
8. [Best Practices](#best-practices)

---

## Overview

### What is the Strategy Module?
The Strategy Module is the brain of the trading bot system. It handles:
- **Signal Generation**: Converting market data into buy/sell signals
- **Indicator Calculation**: Computing technical indicators (RSI, Bollinger Bands, etc.)
- **Strategy Logic**: Implementing trading rules and conditions
- **Risk Integration**: Working with position sizing and risk management
- **Multi-Strategy Support**: Running multiple strategies simultaneously

### Key Design Principles
1. **Modularity**: Each strategy is self-contained and interchangeable
2. **Testability**: Easy to unit test and backtest in isolation
3. **Composability**: Strategies can be combined and weighted
4. **Configuration-Driven**: Strategies defined via config, not hardcoded
5. **MIT-Licensed**: Only MIT/BSD/Apache dependencies

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         STRATEGY MODULE ARCHITECTURE                         │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│  STRATEGY ORCHESTRATOR (strategy_orchestrator.py)                           │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Responsibilities:                                                  │    │
│  │  • Load and manage multiple strategies                              │    │
│  │  • Coordinate signal aggregation                                    │    │
│  │  • Handle strategy lifecycle (start, stop, pause)                   │    │
│  │  • Route market data to strategies                                  │    │
│  │  • Manage strategy weights in portfolio                             │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
            ┌──────────────────────────┼──────────────────────────┐
            │                          │                          │
            ▼                          ▼                          ▼
┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐
│  STRATEGY 1         │  │  STRATEGY 2         │  │  STRATEGY 3         │
│  (Mean Reversion)   │  │  (Momentum)         │  │  (Arbitrage)        │
│                     │  │                     │  │                     │
│  ┌───────────────┐  │  │  ┌───────────────┐  │  │  ┌───────────────┐  │
│  │ BaseStrategy  │  │  │  │ BaseStrategy  │  │  │  │ BaseStrategy  │  │
│  │   (abstract)  │  │  │  │   (abstract)  │  │  │  │   (abstract)  │  │
│  └───────┬───────┘  │  │  └───────┬───────┘  │  │  └───────┬───────┘  │
│          │          │  │          │          │  │          │          │
│  ┌───────▼───────┐  │  │  ┌───────▼───────┐  │  │  ┌───────▼───────┐  │
│  │ MeanReversion │  │  │  │   Momentum    │  │  │  │   Arbitrage   │  │
│  │   Strategy    │  │  │  │   Strategy    │  │  │  │   Strategy    │  │
│  └───────────────┘  │  │  └───────────────┘  │  │  └───────────────┘  │
└─────────────────────┘  └─────────────────────┘  └─────────────────────┘
            │                          │                          │
            └──────────────────────────┼──────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  SIGNAL PROCESSOR (signal_processor.py)                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Responsibilities:                                                  │    │
│  │  • Aggregate signals from multiple strategies                       │    │
│  │  • Apply signal weights                                             │    │
│  │  • Resolve conflicting signals                                      │    │
│  │  • Generate final trading decisions                                 │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  RISK MANAGER (integration with risk module)                                │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  • Validate signals against risk limits                             │    │
│  │  • Calculate position sizes                                         │    │
│  │  • Check portfolio heat                                             │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
1. MARKET DATA INPUT
   ↓
   Exchange → CCXT → Data Pipeline → OHLCV DataFrame

2. INDICATOR CALCULATION
   ↓
   Pandas TA → Calculate RSI, Bollinger Bands, etc.

3. SIGNAL GENERATION
   ↓
   Strategy.on_data() → Generate raw signals

4. SIGNAL AGGREGATION
   ↓
   Signal Processor → Combine multiple strategy signals

5. RISK VALIDATION
   ↓
   Risk Manager → Validate against limits

6. TRADING DECISION
   ↓
   Final Signal → Executor Module
```

---

## Core Components

### 1. Base Strategy Class

**File**: `strategies/base_strategy.py`

```python
"""
Base Strategy Class
All trading strategies must inherit from this class.
Provides common functionality and enforces interface compliance.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
import numpy as np
from enum import Enum

class SignalType(Enum):
    """Types of trading signals"""
    BUY = 1
    SELL = -1
    HOLD = 0
    STRONG_BUY = 2
    STRONG_SELL = -2

@dataclass
class Signal:
    """
    Represents a trading signal from a strategy.
    
    Attributes:
        timestamp: When the signal was generated
        strategy_name: Name of the strategy that generated the signal
        symbol: Trading pair (e.g., 'BTC/USDT')
        signal_type: Type of signal (BUY, SELL, HOLD, etc.)
        strength: Signal strength 0.0 to 1.0
        price: Current price when signal generated
        metadata: Additional strategy-specific data
    """
    timestamp: datetime
    strategy_name: str
    symbol: str
    signal_type: SignalType
    strength: float
    price: float
    metadata: Dict[str, Any]

@dataclass
class StrategyConfig:
    """
    Configuration for a strategy.
    
    Attributes:
        name: Unique strategy identifier
        symbols: List of trading pairs to trade
        timeframe: Data timeframe (e.g., '1h', '4h', '1d')
        enabled: Whether strategy is active
        weight: Portfolio weight (0.0 to 1.0)
        max_position_size: Maximum position size in base currency
        risk_per_trade: Risk percentage per trade (0.0 to 1.0)
        params: Strategy-specific parameters
    """
    name: str
    symbols: List[str]
    timeframe: str
    enabled: bool = True
    weight: float = 1.0
    max_position_size: float = 1000.0
    risk_per_trade: float = 0.02
    params: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.params is None:
            self.params = {}

class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies.
    
    Subclasses must implement:
    - initialize(): Set up indicators
    - on_data(): Process new data and generate signals
    - get_parameters(): Return tunable parameters
    """
    
    def __init__(self, config: StrategyConfig):
        """
        Initialize strategy with configuration.
        
        Args:
            config: StrategyConfig with parameters
        """
        self.config = config
        self.name = config.name
        self.symbols = config.symbols
        self.timeframe = config.timeframe
        self.enabled = config.enabled
        self.weight = config.weight
        
        # Storage for calculated indicators
        self.indicators: Dict[str, pd.DataFrame] = {}
        
        # Signal history for analysis
        self.signals_history: List[Signal] = []
        
        # Strategy state
        self.is_initialized = False
        self.last_signal: Optional[Signal] = None
        
    @abstractmethod
    def initialize(self, data: Dict[str, pd.DataFrame]) -> None:
        """
        Initialize strategy with historical data.
        Calculate indicators that need initial history.
        
        Args:
            data: Dictionary mapping symbols to OHLCV DataFrames
        """
        pass
    
    @abstractmethod
    def on_data(self, data: Dict[str, pd.DataFrame]) -> List[Signal]:
        """
        Process new market data and generate trading signals.
        Called on each new candle/bar.
        
        Args:
            data: Dictionary mapping symbols to OHLCV DataFrames
            
        Returns:
            List of Signal objects
        """
        pass
    
    @abstractmethod
    def get_parameters(self) -> Dict[str, Tuple[float, float, float]]:
        """
        Get tunable parameters for optimization.
        
        Returns:
            Dictionary mapping parameter names to (min, max, default) tuples
        """
        pass
    
    def validate_data(self, data: Dict[str, pd.DataFrame]) -> bool:
        """
        Validate that data meets strategy requirements.
        
        Args:
            data: Data dictionary to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not data:
            return False
            
        for symbol in self.symbols:
            if symbol not in data:
                return False
            df = data[symbol]
            required_columns = ['open', 'high', 'low', 'close', 'volume']
            if not all(col in df.columns for col in required_columns):
                return False
                
        return True
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate technical indicators for a symbol.
        Override to add custom indicators.
        
        Args:
            df: OHLCV DataFrame
            
        Returns:
            DataFrame with added indicator columns
        """
        return df
    
    def create_signal(self, 
                      symbol: str, 
                      signal_type: SignalType, 
                      price: float,
                      strength: float = 1.0,
                      metadata: Dict[str, Any] = None) -> Signal:
        """
        Helper to create a Signal object.
        
        Args:
            symbol: Trading pair
            signal_type: Type of signal
            price: Current price
            strength: Signal strength 0.0 to 1.0
            metadata: Additional data
            
        Returns:
            Signal object
        """
        signal = Signal(
            timestamp=datetime.utcnow(),
            strategy_name=self.name,
            symbol=symbol,
            signal_type=signal_type,
            strength=strength,
            price=price,
            metadata=metadata or {}
        )
        
        self.signals_history.append(signal)
        self.last_signal = signal
        
        return signal
    
    def get_signal_history(self, n: int = None) -> List[Signal]:
        """
        Get recent signal history.
        
        Args:
            n: Number of recent signals to return (None for all)
            
        Returns:
            List of Signal objects
        """
        if n is None:
            return self.signals_history
        return self.signals_history[-n:]
    
    def reset(self) -> None:
        """
        Reset strategy state. Used for backtesting multiple runs.
        """
        self.indicators = {}
        self.signals_history = []
        self.last_signal = None
        self.is_initialized = False
    
    def enable(self) -> None:
        """Enable strategy"""
        self.enabled = True
    
    def disable(self) -> None:
        """Disable strategy"""
        self.enabled = False
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', enabled={self.enabled})"
```

### 2. Strategy Orchestrator

**File**: `strategies/strategy_orchestrator.py`

```python
"""
Strategy Orchestrator
Manages multiple strategies, coordinates signal aggregation,
and handles strategy lifecycle.
"""

from typing import Dict, List, Optional, Type
import pandas as pd
import logging
from .base_strategy import BaseStrategy, StrategyConfig, Signal

logger = logging.getLogger(__name__)

class StrategyOrchestrator:
    """
    Orchestrates multiple trading strategies.
    
    Responsibilities:
    - Register and manage strategies
    - Route market data to strategies
    - Aggregate signals from multiple sources
    - Handle strategy lifecycle events
    """
    
    def __init__(self):
        """Initialize orchestrator"""
        self.strategies: Dict[str, BaseStrategy] = {}
        self.signal_callbacks: List[callable] = []
        self.is_running = False
        
    def register_strategy(self, strategy: BaseStrategy) -> None:
        """
        Register a strategy with the orchestrator.
        
        Args:
            strategy: Strategy instance to register
        """
        if strategy.name in self.strategies:
            logger.warning(f"Strategy '{strategy.name}' already registered. Overwriting.")
        
        self.strategies[strategy.name] = strategy
        logger.info(f"Registered strategy: {strategy.name}")
    
    def unregister_strategy(self, name: str) -> None:
        """
        Unregister a strategy.
        
        Args:
            name: Strategy name to remove
        """
        if name in self.strategies:
            del self.strategies[name]
            logger.info(f"Unregistered strategy: {name}")
    
    def get_strategy(self, name: str) -> Optional[BaseStrategy]:
        """
        Get a strategy by name.
        
        Args:
            name: Strategy name
            
        Returns:
            Strategy instance or None
        """
        return self.strategies.get(name)
    
    def get_all_strategies(self) -> List[BaseStrategy]:
        """
        Get all registered strategies.
        
        Returns:
            List of strategy instances
        """
        return list(self.strategies.values())
    
    def get_active_strategies(self) -> List[BaseStrategy]:
        """
        Get only enabled strategies.
        
        Returns:
            List of active strategy instances
        """
        return [s for s in self.strategies.values() if s.enabled]
    
    def initialize_all(self, data: Dict[str, pd.DataFrame]) -> None:
        """
        Initialize all registered strategies with historical data.
        
        Args:
            data: Dictionary of symbol -> OHLCV DataFrames
        """
        for name, strategy in self.strategies.items():
            try:
                logger.info(f"Initializing strategy: {name}")
                strategy.initialize(data)
                strategy.is_initialized = True
                logger.info(f"Successfully initialized: {name}")
            except Exception as e:
                logger.error(f"Failed to initialize strategy {name}: {e}")
                strategy.enabled = False
    
    def process_data(self, data: Dict[str, pd.DataFrame]) -> Dict[str, List[Signal]]:
        """
        Process market data through all active strategies.
        
        Args:
            data: Dictionary of symbol -> OHLCV DataFrames
            
        Returns:
            Dictionary mapping strategy names to lists of signals
        """
        all_signals = {}
        
        for name, strategy in self.strategies.items():
            if not strategy.enabled:
                continue
                
            try:
                # Validate data
                if not strategy.validate_data(data):
                    logger.warning(f"Invalid data for strategy {name}")
                    continue
                
                # Generate signals
                signals = strategy.on_data(data)
                all_signals[name] = signals
                
                # Notify callbacks
                for signal in signals:
                    self._notify_callbacks(signal)
                    
            except Exception as e:
                logger.error(f"Error processing data for strategy {name}: {e}")
                all_signals[name] = []
        
        return all_signals
    
    def add_signal_callback(self, callback: callable) -> None:
        """
        Add a callback to be called when signals are generated.
        
        Args:
            callback: Function accepting a Signal parameter
        """
        self.signal_callbacks.append(callback)
    
    def _notify_callbacks(self, signal: Signal) -> None:
        """Notify all registered callbacks of a new signal"""
        for callback in self.signal_callbacks:
            try:
                callback(signal)
            except Exception as e:
                logger.error(f"Error in signal callback: {e}")
    
    def enable_strategy(self, name: str) -> bool:
        """
        Enable a specific strategy.
        
        Args:
            name: Strategy name
            
        Returns:
            True if successful, False if strategy not found
        """
        if name in self.strategies:
            self.strategies[name].enable()
            logger.info(f"Enabled strategy: {name}")
            return True
        return False
    
    def disable_strategy(self, name: str) -> bool:
        """
        Disable a specific strategy.
        
        Args:
            name: Strategy name
            
        Returns:
            True if successful, False if strategy not found
        """
        if name in self.strategies:
            self.strategies[name].disable()
            logger.info(f"Disabled strategy: {name}")
            return True
        return False
    
    def reset_all(self) -> None:
        """Reset all strategies to initial state"""
        for strategy in self.strategies.values():
            strategy.reset()
        logger.info("Reset all strategies")
    
    def get_strategy_status(self) -> Dict[str, dict]:
        """
        Get status of all strategies.
        
        Returns:
            Dictionary with strategy status info
        """
        return {
            name: {
                'enabled': strategy.enabled,
                'initialized': strategy.is_initialized,
                'weight': strategy.weight,
                'symbols': strategy.symbols,
                'last_signal': strategy.last_signal.signal_type.name if strategy.last_signal else None
            }
            for name, strategy in self.strategies.items()
        }
```

### 3. Signal Processor

**File**: `strategies/signal_processor.py`

```python
"""
Signal Processor
Aggregates signals from multiple strategies and resolves conflicts.
Generates final trading decisions with position sizing.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from .base_strategy import Signal, SignalType
import logging

logger = logging.getLogger(__name__)

class AggregationMethod(Enum):
    """Methods for aggregating multiple signals"""
    MAJORITY_VOTE = "majority_vote"  # Most common signal wins
    WEIGHTED_AVERAGE = "weighted_average"  # Average weighted by strategy weight
    CONFIDENCE_THRESHOLD = "confidence_threshold"  # Only high-confidence signals
    PRIORITY = "priority"  # First strategy in priority list wins

@dataclass
class TradingDecision:
    """
    Final trading decision after processing all signals.
    
    Attributes:
        symbol: Trading pair
        action: BUY, SELL, or HOLD
        confidence: Confidence level 0.0 to 1.0
        size: Position size to trade
        stop_loss: Stop loss price
        take_profit: Take profit price
        source_signals: Original signals that contributed
    """
    symbol: str
    action: SignalType
    confidence: float
    size: float
    stop_loss: Optional[float]
    take_profit: Optional[float]
    source_signals: List[Signal]

class SignalProcessor:
    """
    Processes and aggregates signals from multiple strategies.
    
    Features:
    - Multiple aggregation methods
    - Conflict resolution
    - Confidence scoring
    - Position sizing integration
    """
    
    def __init__(self, method: AggregationMethod = AggregationMethod.WEIGHTED_AVERAGE):
        """
        Initialize signal processor.
        
        Args:
            method: Aggregation method to use
        """
        self.method = method
        self.min_confidence = 0.6  # Minimum confidence to act
        
    def process_signals(self, 
                       signals_by_strategy: Dict[str, List[Signal]],
                       account_size: float,
                       risk_per_trade: float = 0.02) -> List[TradingDecision]:
        """
        Process signals from all strategies and generate trading decisions.
        
        Args:
            signals_by_strategy: Dict mapping strategy names to their signals
            account_size: Current account size for position sizing
            risk_per_trade: Risk percentage per trade
            
        Returns:
            List of TradingDecision objects
        """
        # Group signals by symbol
        signals_by_symbol = self._group_by_symbol(signals_by_strategy)
        
        decisions = []
        for symbol, signals in signals_by_symbol.items():
            decision = self._aggregate_symbol_signals(
                symbol, signals, account_size, risk_per_trade
            )
            if decision:
                decisions.append(decision)
        
        return decisions
    
    def _group_by_symbol(self, 
                        signals_by_strategy: Dict[str, List[Signal]]) -> Dict[str, List[Signal]]:
        """Group all signals by symbol"""
        grouped = {}
        for strategy_name, signals in signals_by_strategy.items():
            for signal in signals:
                if signal.symbol not in grouped:
                    grouped[signal.symbol] = []
                grouped[signal.symbol].append(signal)
        return grouped
    
    def _aggregate_symbol_signals(self,
                                  symbol: str,
                                  signals: List[Signal],
                                  account_size: float,
                                  risk_per_trade: float) -> Optional[TradingDecision]:
        """
        Aggregate signals for a single symbol.
        
        Args:
            symbol: Trading pair
            signals: List of signals for this symbol
            account_size: Account size
            risk_per_trade: Risk percentage
            
        Returns:
            TradingDecision or None if no action
        """
        if not signals:
            return None
        
        # Apply aggregation method
        if self.method == AggregationMethod.WEIGHTED_AVERAGE:
            return self._weighted_average(symbol, signals, account_size, risk_per_trade)
        elif self.method == AggregationMethod.MAJORITY_VOTE:
            return self._majority_vote(symbol, signals, account_size, risk_per_trade)
        elif self.method == AggregationMethod.CONFIDENCE_THRESHOLD:
            return self._confidence_threshold(symbol, signals, account_size, risk_per_trade)
        else:
            return self._priority_based(symbol, signals, account_size, risk_per_trade)
    
    def _weighted_average(self, symbol: str, signals: List[Signal], 
                         account_size: float, risk_per_trade: float) -> Optional[TradingDecision]:
        """
        Aggregate signals using weighted average.
        Weights come from strategy weights and signal strength.
        """
        total_weight = 0
        weighted_signal_value = 0
        
        for signal in signals:
            # Weight = strategy weight * signal strength
            weight = 1.0 * signal.strength  # Could integrate strategy weight here
            total_weight += weight
            weighted_signal_value += signal.signal_type.value * weight
        
        if total_weight == 0:
            return None
        
        avg_signal = weighted_signal_value / total_weight
        confidence = min(abs(avg_signal) / 2.0, 1.0)  # Normalize to 0-1
        
        if confidence < self.min_confidence:
            return None
        
        # Determine action
        if avg_signal > 0.5:
            action = SignalType.BUY
        elif avg_signal < -0.5:
            action = SignalType.SELL
        else:
            return None
        
        # Calculate position size
        size = self._calculate_position_size(account_size, risk_per_trade, confidence)
        
        return TradingDecision(
            symbol=symbol,
            action=action,
            confidence=confidence,
            size=size,
            stop_loss=None,  # Would come from risk manager
            take_profit=None,
            source_signals=signals
        )
    
    def _majority_vote(self, symbol: str, signals: List[Signal],
                      account_size: float, risk_per_trade: float) -> Optional[TradingDecision]:
        """Simple majority vote aggregation"""
        buy_count = sum(1 for s in signals if s.signal_type in [SignalType.BUY, SignalType.STRONG_BUY])
        sell_count = sum(1 for s in signals if s.signal_type in [SignalType.SELL, SignalType.STRONG_SELL])
        
        total = len(signals)
        if total == 0:
            return None
        
        buy_ratio = buy_count / total
        sell_ratio = sell_count / total
        
        if buy_ratio > 0.5 and buy_ratio > sell_ratio:
            action = SignalType.BUY
            confidence = buy_ratio
        elif sell_ratio > 0.5 and sell_ratio > buy_ratio:
            action = SignalType.SELL
            confidence = sell_ratio
        else:
            return None
        
        if confidence < self.min_confidence:
            return None
        
        size = self._calculate_position_size(account_size, risk_per_trade, confidence)
        
        return TradingDecision(
            symbol=symbol,
            action=action,
            confidence=confidence,
            size=size,
            stop_loss=None,
            take_profit=None,
            source_signals=signals
        )
    
    def _confidence_threshold(self, symbol: str, signals: List[Signal],
                             account_size: float, risk_per_trade: float) -> Optional[TradingDecision]:
        """Only accept signals with high individual confidence"""
        high_conf_signals = [s for s in signals if s.strength >= self.min_confidence]
        
        if not high_conf_signals:
            return None
        
        # Take the highest confidence signal
        best_signal = max(high_conf_signals, key=lambda s: s.strength)
        
        if best_signal.signal_type == SignalType.HOLD:
            return None
        
        size = self._calculate_position_size(account_size, risk_per_trade, best_signal.strength)
        
        return TradingDecision(
            symbol=symbol,
            action=best_signal.signal_type,
            confidence=best_signal.strength,
            size=size,
            stop_loss=None,
            take_profit=None,
            source_signals=[best_signal]
        )
    
    def _priority_based(self, symbol: str, signals: List[Signal],
                       account_size: float, risk_per_trade: float) -> Optional[TradingDecision]:
        """Use first signal in priority order"""
        # Sort by priority (implementation-specific)
        # For now, just take the first non-HOLD signal
        for signal in signals:
            if signal.signal_type != SignalType.HOLD:
                size = self._calculate_position_size(account_size, risk_per_trade, signal.strength)
                return TradingDecision(
                    symbol=symbol,
                    action=signal.signal_type,
                    confidence=signal.strength,
                    size=size,
                    stop_loss=None,
                    take_profit=None,
                    source_signals=[signal]
                )
        return None
    
    def _calculate_position_size(self, account_size: float, risk_per_trade: float, 
                                confidence: float) -> float:
        """
        Calculate position size based on account and confidence.
        
        Args:
            account_size: Total account size
            risk_per_trade: Risk percentage per trade
            confidence: Signal confidence 0-1
            
        Returns:
            Position size in currency
        """
        base_size = account_size * risk_per_trade
        # Scale by confidence
        return base_size * confidence
```

---

## Implementation Guide

### Step 1: Create Your First Strategy

**File**: `strategies/mean_reversion.py`

```python
"""
Mean Reversion Strategy
Uses RSI and Bollinger Bands to identify oversold/overbought conditions.

Entry: RSI < 30 AND Price < Lower Bollinger Band
Exit: RSI > 70 OR Price > Upper Bollinger Band

Based on research: A Mean Reversion Strategy with 2.11 Sharpe
URL: https://www.quantitativo.com/p/a-mean-reversion-strategy-with-211
"""

import pandas as pd
import pandas_ta as ta
from typing import Dict, List, Tuple
from .base_strategy import BaseStrategy, StrategyConfig, Signal, SignalType

class MeanReversionStrategy(BaseStrategy):
    """
    Mean Reversion Strategy using RSI and Bollinger Bands.
    
    Parameters:
        rsi_period: Period for RSI calculation (default: 14)
        rsi_oversold: RSI level considered oversold (default: 30)
        rsi_overbought: RSI level considered overbought (default: 70)
        bb_period: Period for Bollinger Bands (default: 20)
        bb_std: Number of standard deviations for bands (default: 2.0)
        use_var_filter: Whether to use VaR volatility filter (default: True)
        var_threshold: VaR threshold for trading (default: -0.02)
    """
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        
        # Extract parameters from config with defaults
        self.rsi_period = self.config.params.get('rsi_period', 14)
        self.rsi_oversold = self.config.params.get('rsi_oversold', 30)
        self.rsi_overbought = self.config.params.get('rsi_overbought', 70)
        self.bb_period = self.config.params.get('bb_period', 20)
        self.bb_std = self.config.params.get('bb_std', 2.0)
        self.use_var_filter = self.config.params.get('use_var_filter', True)
        self.var_threshold = self.config.params.get('var_threshold', -0.02)
        
    def get_parameters(self) -> Dict[str, Tuple[float, float, float]]:
        """
        Get tunable parameters for optimization.
        Returns: {param_name: (min_value, max_value, default_value)}
        """
        return {
            'rsi_period': (5, 30, 14),
            'rsi_oversold': (15, 40, 30),
            'rsi_overbought': (60, 85, 70),
            'bb_period': (10, 50, 20),
            'bb_std': (1.5, 3.0, 2.0),
            'var_threshold': (-0.05, -0.01, -0.02)
        }
    
    def initialize(self, data: Dict[str, pd.DataFrame]) -> None:
        """
        Initialize strategy by calculating indicators for all symbols.
        """
        for symbol in self.symbols:
            if symbol in data:
                self.indicators[symbol] = self._calculate_indicators(data[symbol])
                
        self.is_initialized = True
        
    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate RSI and Bollinger Bands indicators.
        
        Args:
            df: OHLCV DataFrame
            
        Returns:
            DataFrame with indicator columns added
        """
        df = df.copy()
        
        # Calculate RSI
        df['rsi'] = ta.rsi(df['close'], length=self.rsi_period)
        
        # Calculate Bollinger Bands
        bb = ta.bbands(df['close'], length=self.bb_period, std=self.bb_std)
        df['bb_upper'] = bb[f'BBU_{self.bb_period}_{self.bb_std}.0']
        df['bb_middle'] = bb[f'BBM_{self.bb_period}_{self.bb_std}.0']
        df['bb_lower'] = bb[f'BBL_{self.bb_period}_{self.bb_std}.0']
        
        # Calculate VaR (Value at Risk) for volatility filtering
        if self.use_var_filter:
            df['returns'] = df['close'].pct_change()
            df['var_95'] = df['returns'].rolling(window=20).quantile(0.05)
        
        return df
    
    def on_data(self, data: Dict[str, pd.DataFrame]) -> List[Signal]:
        """
        Process new market data and generate signals.
        
        Args:
            data: Dictionary of symbol -> OHLCV DataFrames
            
        Returns:
            List of Signal objects
        """
        signals = []
        
        for symbol in self.symbols:
            if symbol not in data:
                continue
                
            df = data[symbol]
            if len(df) == 0:
                continue
            
            # Get latest data point
            current = df.iloc[-1]
            price = current['close']
            
            # Calculate indicators
            indicators = self._calculate_indicators(df)
            latest = indicators.iloc[-1]
            
            # Check VaR filter
            if self.use_var_filter:
                var_value = latest.get('var_95', 0)
                if var_value < self.var_threshold:
                    # Too volatile, skip signal
                    continue
            
            rsi = latest['rsi']
            bb_lower = latest['bb_lower']
            bb_upper = latest['bb_upper']
            
            # Generate signals
            signal_type = SignalType.HOLD
            strength = 0.0
            
            # BUY condition: RSI oversold AND price below lower band
            if rsi < self.rsi_oversold and price < bb_lower:
                signal_type = SignalType.BUY
                # Calculate strength based on how oversold
                strength = min((self.rsi_oversold - rsi) / self.rsi_oversold + 
                              (bb_lower - price) / price, 1.0)
            
            # SELL condition: RSI overbought OR price above upper band
            elif rsi > self.rsi_overbought or price > bb_upper:
                signal_type = SignalType.SELL
                # Calculate strength
                if rsi > self.rsi_overbought:
                    strength = min((rsi - self.rsi_overbought) / (100 - self.rsi_overbought), 1.0)
                else:
                    strength = min((price - bb_upper) / bb_upper, 1.0)
            
            # Create signal if not HOLD
            if signal_type != SignalType.HOLD:
                signal = self.create_signal(
                    symbol=symbol,
                    signal_type=signal_type,
                    price=price,
                    strength=strength,
                    metadata={
                        'rsi': rsi,
                        'bb_lower': bb_lower,
                        'bb_upper': bb_upper,
                        'var_95': latest.get('var_95', None)
                    }
                )
                signals.append(signal)
        
        return signals
```

### Step 2: Create Configuration

**File**: `config/strategies.yaml`

```yaml
# Strategy Configuration
# Define all strategies and their parameters here

strategies:
  # Mean Reversion Strategy
  - name: "mean_reversion_btc"
    class: "strategies.mean_reversion.MeanReversionStrategy"
    enabled: true
    weight: 0.4
    symbols:
      - "BTC/USDT"
    timeframe: "1h"
    max_position_size: 5000
    risk_per_trade: 0.02
    params:
      rsi_period: 14
      rsi_oversold: 30
      rsi_overbought: 70
      bb_period: 20
      bb_std: 2.0
      use_var_filter: true
      var_threshold: -0.02

  - name: "mean_reversion_eth"
    class: "strategies.mean_reversion.MeanReversionStrategy"
    enabled: true
    weight: 0.3
    symbols:
      - "ETH/USDT"
    timeframe: "1h"
    max_position_size: 3000
    risk_per_trade: 0.02
    params:
      rsi_period: 14
      rsi_oversold: 30
      rsi_overbought: 70
      bb_period: 20
      bb_std: 2.0
      use_var_filter: true
      var_threshold: -0.02

  # Momentum Strategy
  - name: "momentum_btc"
    class: "strategies.momentum.MomentumStrategy"
    enabled: false
    weight: 0.3
    symbols:
      - "BTC/USDT"
    timeframe: "4h"
    max_position_size: 2000
    risk_per_trade: 0.015
    params:
      macd_fast: 12
      macd_slow: 26
      macd_signal: 9
      adx_period: 14
      adx_threshold: 25

signal_aggregation:
  method: "weighted_average"
  min_confidence: 0.6
  
risk_management:
  max_portfolio_heat: 0.5
  max_correlated_positions: 3
  daily_loss_limit: 0.05
  weekly_loss_limit: 0.10
```

### Step 3: Create Strategy Factory

**File**: `strategies/strategy_factory.py`

```python
"""
Strategy Factory
Creates strategy instances from configuration.
"""

import importlib
from typing import Dict, Any
import yaml
from .base_strategy import BaseStrategy, StrategyConfig

class StrategyFactory:
    """
    Factory for creating strategy instances from configuration.
    """
    
    @staticmethod
    def load_config(config_path: str) -> Dict[str, Any]:
        """
        Load strategy configuration from YAML file.
        
        Args:
            config_path: Path to YAML config file
            
        Returns:
            Configuration dictionary
        """
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    @staticmethod
    def create_strategy(config_dict: Dict[str, Any]) -> BaseStrategy:
        """
        Create a strategy instance from configuration dictionary.
        
        Args:
            config_dict: Strategy configuration
            
        Returns:
            Strategy instance
        """
        # Parse class path
        class_path = config_dict['class']
        module_path, class_name = class_path.rsplit('.', 1)
        
        # Import module and get class
        module = importlib.import_module(module_path)
        strategy_class = getattr(module, class_name)
        
        # Create StrategyConfig
        strategy_config = StrategyConfig(
            name=config_dict['name'],
            symbols=config_dict['symbols'],
            timeframe=config_dict['timeframe'],
            enabled=config_dict.get('enabled', True),
            weight=config_dict.get('weight', 1.0),
            max_position_size=config_dict.get('max_position_size', 1000.0),
            risk_per_trade=config_dict.get('risk_per_trade', 0.02),
            params=config_dict.get('params', {})
        )
        
        # Instantiate strategy
        return strategy_class(strategy_config)
    
    @staticmethod
    def create_from_config_file(config_path: str) -> list:
        """
        Create all strategies from a configuration file.
        
        Args:
            config_path: Path to YAML config
            
        Returns:
            List of strategy instances
        """
        config = StrategyFactory.load_config(config_path)
        strategies = []
        
        for strategy_config in config.get('strategies', []):
            try:
                strategy = StrategyFactory.create_strategy(strategy_config)
                strategies.append(strategy)
            except Exception as e:
                print(f"Error creating strategy {strategy_config.get('name')}: {e}")
        
        return strategies
```

---

## Development Workflow

### Phase 1: Strategy Development

```bash
# 1. Create new strategy file
touch strategies/my_strategy.py

# 2. Implement strategy following BaseStrategy interface
# See mean_reversion.py as template

# 3. Add configuration to config/strategies.yaml

# 4. Create unit tests
touch tests/test_my_strategy.py
```

### Phase 2: Local Testing

```python
# test_strategy_locally.py
"""
Local testing script for strategy development.
"""

import pandas as pd
from strategies.mean_reversion import MeanReversionStrategy
from strategies.base_strategy import StrategyConfig

# Load test data
data = pd.read_csv('data/btc_usdt_1h.csv')
data['timestamp'] = pd.to_datetime(data['timestamp'])
data.set_index('timestamp', inplace=True)

# Rename columns to lowercase for consistency
data.columns = [c.lower() for c in data.columns]

# Create strategy config
config = StrategyConfig(
    name="test_mean_reversion",
    symbols=["BTC/USDT"],
    timeframe="1h",
    enabled=True,
    weight=1.0,
    params={
        'rsi_period': 14,
        'rsi_oversold': 30,
        'rsi_overbought': 70,
        'bb_period': 20,
        'bb_std': 2.0
    }
)

# Create strategy instance
strategy = MeanReversionStrategy(config)

# Test initialization
strategy.initialize({'BTC/USDT': data})

# Test signal generation
signals = strategy.on_data({'BTC/USDT': data})

# Analyze results
print(f"Generated {len(signals)} signals")
for signal in signals[:5]:
    print(f"{signal.timestamp}: {signal.signal_type.name} {signal.symbol} "
          f"at ${signal.price:.2f} (strength: {signal.strength:.2f})")
```

### Phase 3: Backtest Integration

```python
# backtest_strategy.py
"""
Backtest a strategy using Backtesting.py
"""

from backtesting import Backtest, Strategy as BTStrategy
from backtesting.lib import crossover
import pandas as pd

class MeanReversionBT(BTStrategy):
    """
    Backtesting.py wrapper for Mean Reversion strategy.
    """
    
    rsi_period = 14
    rsi_oversold = 30
    rsi_overbought = 70
    bb_period = 20
    bb_std = 2.0
    
    def init(self):
        # Calculate indicators
        close = self.data.Close
        
        # RSI
        import pandas_ta as ta
        self.rsi = self.I(ta.rsi, close, self.rsi_period)
        
        # Bollinger Bands
        bb = ta.bbands(close, length=self.bb_period, std=self.bb_std)
        self.bb_upper = self.I(lambda: bb.iloc[:, 0])
        self.bb_lower = self.I(lambda: bb.iloc[:, 2])
    
    def next(self):
        # Entry: RSI < 30 AND price < lower band
        if (self.rsi[-1] < self.rsi_oversold and 
            self.data.Close[-1] < self.bb_lower[-1]):
            if not self.position:
                self.buy()
        
        # Exit: RSI > 70 OR price > upper band
        elif (self.rsi[-1] > self.rsi_overbought or 
              self.data.Close[-1] > self.bb_upper[-1]):
            if self.position:
                self.position.close()

# Load data
data = pd.read_csv('data/btc_usdt_1h.csv')
data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']

# Run backtest
bt = Backtest(data, MeanReversionBT, cash=10000, commission=0.002)
stats = bt.run()

print(stats)
bt.plot()
```

---

## Testing & Validation

### Unit Tests

**File**: `tests/test_strategies.py`

```python
"""
Unit tests for strategy module.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from strategies.base_strategy import BaseStrategy, StrategyConfig, Signal, SignalType
from strategies.mean_reversion import MeanReversionStrategy

class TestBaseStrategy:
    """Test base strategy functionality"""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample OHLCV data"""
        dates = pd.date_range(start='2024-01-01', periods=100, freq='1h')
        np.random.seed(42)
        
        data = pd.DataFrame({
            'open': np.random.randn(100).cumsum() + 40000,
            'high': np.random.randn(100).cumsum() + 40500,
            'low': np.random.randn(100).cumsum() + 39500,
            'close': np.random.randn(100).cumsum() + 40000,
            'volume': np.random.randint(1000, 10000, 100)
        }, index=dates)
        
        return data
    
    @pytest.fixture
    def strategy_config(self):
        """Create sample strategy config"""
        return StrategyConfig(
            name="test_strategy",
            symbols=["BTC/USDT"],
            timeframe="1h",
            enabled=True,
            weight=1.0,
            params={'rsi_period': 14}
        )
    
    def test_signal_creation(self, strategy_config):
        """Test signal creation"""
        strategy = MeanReversionStrategy(strategy_config)
        
        signal = strategy.create_signal(
            symbol="BTC/USDT",
            signal_type=SignalType.BUY,
            price=40000.0,
            strength=0.8,
            metadata={'test': 'value'}
        )
        
        assert signal.symbol == "BTC/USDT"
        assert signal.signal_type == SignalType.BUY
        assert signal.strength == 0.8
        assert signal.price == 40000.0
        assert signal.metadata['test'] == 'value'
    
    def test_data_validation(self, strategy_config, sample_data):
        """Test data validation"""
        strategy = MeanReversionStrategy(strategy_config)
        
        # Valid data
        valid_data = {'BTC/USDT': sample_data}
        assert strategy.validate_data(valid_data) == True
        
        # Missing symbol
        invalid_data = {'ETH/USDT': sample_data}
        assert strategy.validate_data(invalid_data) == False
        
        # Missing columns
        bad_data = sample_data.drop(columns=['volume'])
        assert strategy.validate_data({'BTC/USDT': bad_data}) == False

class TestMeanReversionStrategy:
    """Test Mean Reversion strategy"""
    
    @pytest.fixture
    def oversold_data(self):
        """Create data that triggers oversold condition"""
        dates = pd.date_range(start='2024-01-01', periods=50, freq='1h')
        
        # Price declining to trigger oversold
        data = pd.DataFrame({
            'open': 40000 - np.arange(50) * 100,
            'high': 40100 - np.arange(50) * 100,
            'low': 39900 - np.arange(50) * 100,
            'close': 40000 - np.arange(50) * 100,
            'volume': np.random.randint(1000, 10000, 50)
        }, index=dates)
        
        return data
    
    def test_oversold_signal(self, oversold_data):
        """Test that oversold condition generates buy signal"""
        config = StrategyConfig(
            name="test",
            symbols=["BTC/USDT"],
            timeframe="1h",
            params={'rsi_period': 14, 'rsi_oversold': 30}
        )
        
        strategy = MeanReversionStrategy(config)
        strategy.initialize({'BTC/USDT': oversold_data})
        
        signals = strategy.on_data({'BTC/USDT': oversold_data})
        
        # Should generate at least one buy signal in oversold data
        buy_signals = [s for s in signals if s.signal_type == SignalType.BUY]
        assert len(buy_signals) > 0
```

### Integration Tests

```python
# tests/test_integration.py
"""
Integration tests for strategy module with orchestrator.
"""

import pytest
import pandas as pd
import numpy as np
from strategies.orchestrator import StrategyOrchestrator
from strategies.signal_processor import SignalProcessor
from strategies.mean_reversion import MeanReversionStrategy
from strategies.base_strategy import StrategyConfig

class TestStrategyIntegration:
    """Test strategy orchestration"""
    
    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator with test strategies"""
        orch = StrategyOrchestrator()
        
        # Add mean reversion strategy
        config1 = StrategyConfig(
            name="mr_btc",
            symbols=["BTC/USDT"],
            timeframe="1h",
            weight=0.6
        )
        orch.register_strategy(MeanReversionStrategy(config1))
        
        return orch
    
    @pytest.fixture
    def sample_market_data(self):
        """Create sample market data"""
        dates = pd.date_range(start='2024-01-01', periods=100, freq='1h')
        np.random.seed(42)
        
        return {
            'BTC/USDT': pd.DataFrame({
                'open': np.random.randn(100).cumsum() + 40000,
                'high': np.random.randn(100).cumsum() + 40500,
                'low': np.random.randn(100).cumsum() + 39500,
                'close': np.random.randn(100).cumsum() + 40000,
                'volume': np.random.randint(1000, 10000, 100)
            }, index=dates)
        }
    
    def test_multi_strategy_processing(self, orchestrator, sample_market_data):
        """Test processing data through multiple strategies"""
        orchestrator.initialize_all(sample_market_data)
        
        signals = orchestrator.process_data(sample_market_data)
        
        assert 'mr_btc' in signals
        assert isinstance(signals['mr_btc'], list)
    
    def test_signal_aggregation(self, sample_market_data):
        """Test signal processor aggregation"""
        processor = SignalProcessor()
        
        # Create sample signals
        from strategies.base_strategy import Signal, SignalType
        from datetime import datetime
        
        signals = {
            'strategy1': [
                Signal(
                    timestamp=datetime.now(),
                    strategy_name='s1',
                    symbol='BTC/USDT',
                    signal_type=SignalType.BUY,
                    strength=0.8,
                    price=40000,
                    metadata={}
                )
            ],
            'strategy2': [
                Signal(
                    timestamp=datetime.now(),
                    strategy_name='s2',
                    symbol='BTC/USDT',
                    signal_type=SignalType.BUY,
                    strength=0.7,
                    price=40000,
                    metadata={}
                )
            ]
        }
        
        decisions = processor.process_signals(signals, account_size=10000)
        
        assert len(decisions) > 0
        assert decisions[0].action == SignalType.BUY
```

---

## Integration Patterns

### With Data Pipeline

```python
# data/strategy_integration.py
"""
Integration between data pipeline and strategy module.
"""

from typing import Dict
import pandas as pd
from strategies.orchestrator import StrategyOrchestrator

class StrategyDataAdapter:
    """
    Adapts data from pipeline to strategy format.
    """
    
    def __init__(self, orchestrator: StrategyOrchestrator):
        self.orchestrator = orchestrator
    
    def on_new_data(self, symbol: str, data: pd.DataFrame):
        """
        Called when new market data arrives.
        
        Args:
            symbol: Trading pair
            data: OHLCV DataFrame
        """
        # Format data for strategies
        formatted_data = self._format_data(symbol, data)
        
        # Process through orchestrator
        signals = self.orchestrator.process_data(formatted_data)
        
        return signals
    
    def _format_data(self, symbol: str, data: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """Format data for strategy consumption"""
        # Ensure lowercase columns
        data = data.copy()
        data.columns = [c.lower() for c in data.columns]
        
        return {symbol: data}
```

### With Risk Manager

```python
# risk/strategy_integration.py
"""
Integration between strategy module and risk management.
"""

from strategies.signal_processor import TradingDecision
from typing import List, Optional

class RiskValidator:
    """
    Validates trading decisions against risk limits.
    Integrates with Risk Manager module.
    """
    
    def __init__(self, risk_manager):
        self.risk_manager = risk_manager
    
    def validate_decisions(self, decisions: List[TradingDecision]) -> List[TradingDecision]:
        """
        Validate and filter trading decisions.
        
        Args:
            decisions: List of proposed trading decisions
            
        Returns:
            List of approved decisions
        """
        approved = []
        
        for decision in decisions:
            # Check portfolio heat
            if not self.risk_manager.check_portfolio_heat(decision.size):
                continue
            
            # Check position limits
            if not self.risk_manager.check_position_limits(decision.symbol, decision.size):
                continue
            
            # Calculate stop loss and take profit
            decision.stop_loss = self.risk_manager.calculate_stop_loss(
                decision.symbol, decision.price, decision.action
            )
            decision.take_profit = self.risk_manager.calculate_take_profit(
                decision.symbol, decision.price, decision.action
            )
            
            approved.append(decision)
        
        return approved
```

### With Executor

```python
# executor/strategy_integration.py
"""
Integration between strategy module and order executor.
"""

from strategies.signal_processor import TradingDecision
from typing import List
import logging

logger = logging.getLogger(__name__)

class StrategyExecutor:
    """
    Executes trading decisions from strategy module.
    """
    
    def __init__(self, order_manager, paper_trading: bool = True):
        self.order_manager = order_manager
        self.paper_trading = paper_trading
    
    def execute_decisions(self, decisions: List[TradingDecision]):
        """
        Execute approved trading decisions.
        
        Args:
            decisions: List of validated TradingDecision objects
        """
        for decision in decisions:
            try:
                if decision.action.value > 0:  # BUY
                    self._execute_buy(decision)
                elif decision.action.value < 0:  # SELL
                    self._execute_sell(decision)
                    
            except Exception as e:
                logger.error(f"Error executing decision for {decision.symbol}: {e}")
    
    def _execute_buy(self, decision: TradingDecision):
        """Execute buy order"""
        order_type = "limit"  # Use limit orders for better fills
        
        order = self.order_manager.place_order(
            symbol=decision.symbol,
            side='buy',
            order_type=order_type,
            amount=decision.size / decision.price,  # Convert $ to units
            price=decision.price,
            stop_loss=decision.stop_loss,
            take_profit=decision.take_profit,
            paper=self.paper_trading
        )
        
        logger.info(f"Executed BUY order for {decision.symbol}: {order}")
    
    def _execute_sell(self, decision: TradingDecision):
        """Execute sell order"""
        order = self.order_manager.place_order(
            symbol=decision.symbol,
            side='sell',
            order_type='market',  # Use market for exits
            amount=None,  # Close entire position
            paper=self.paper_trading
        )
        
        logger.info(f"Executed SELL order for {decision.symbol}: {order}")
```

---

## Best Practices

### 1. Strategy Design Patterns

```python
# Pattern 1: Template Method Pattern
class BaseStrategy(ABC):
    def process(self, data):
        """Template method defining strategy workflow"""
        if not self.validate_data(data):
            return []
        
        indicators = self.calculate_indicators(data)
        signals = self.generate_signals(indicators)
        filtered = self.filter_signals(signals)
        
        return filtered
    
    @abstractmethod
    def generate_signals(self, indicators):
        pass

# Pattern 2: Strategy Composition
class CompositeStrategy(BaseStrategy):
    """Combines multiple strategies"""
    
    def __init__(self, strategies: List[BaseStrategy], weights: List[float]):
        self.strategies = strategies
        self.weights = weights
    
    def on_data(self, data):
        all_signals = []
        for strategy, weight in zip(self.strategies, self.weights):
            signals = strategy.on_data(data)
            # Apply weight to signal strength
            for signal in signals:
                signal.strength *= weight
            all_signals.extend(signals)
        return all_signals

# Pattern 3: Signal Decorators
class SignalFilter:
    """Decorator for filtering signals"""
    
    def __init__(self, strategy: BaseStrategy):
        self.strategy = strategy
    
    def on_data(self, data):
        signals = self.strategy.on_data(data)
        return [s for s in signals if self._filter(s)]
    
    def _filter(self, signal):
        # Custom filter logic
        return signal.strength > 0.5
```

### 2. Configuration Management

```python
# Use environment-specific configs
import os

config_path = os.getenv('STRATEGY_CONFIG', 'config/strategies.yaml')

# Override parameters via environment
override_params = {
    'rsi_period': int(os.getenv('RSI_PERIOD', 14)),
    'risk_per_trade': float(os.getenv('RISK_PER_TRADE', 0.02))
}
```

### 3. Error Handling

```python
class RobustStrategy(BaseStrategy):
    """Strategy with comprehensive error handling"""
    
    def on_data(self, data):
        try:
            # Validate inputs
            if not self._validate_inputs(data):
                return []
            
            # Calculate with error recovery
            try:
                indicators = self._calculate_indicators(data)
            except Exception as e:
                logger.error(f"Indicator calculation failed: {e}")
                return []
            
            # Generate signals
            signals = self._generate_signals(indicators)
            
            # Validate outputs
            signals = self._validate_signals(signals)
            
            return signals
            
        except Exception as e:
            logger.critical(f"Strategy {self.name} failed: {e}")
            # Disable strategy on critical error
            self.disable()
            return []
```

### 4. Performance Optimization

```python
# Cache indicator calculations
from functools import lru_cache

class OptimizedStrategy(BaseStrategy):
    def __init__(self, config):
        super().__init__(config)
        self._indicator_cache = {}
    
    def calculate_indicators(self, df):
        # Use cache key based on data hash
        cache_key = hash(df['close'].values.tobytes())
        
        if cache_key not in self._indicator_cache:
            self._indicator_cache[cache_key] = self._compute_indicators(df)
        
        return self._indicator_cache[cache_key]
    
    def _compute_indicators(self, df):
        # Actual computation
        pass

# Vectorized operations
import numpy as np

# BAD: Loop-based
def calculate_sma_slow(prices, period):
    result = []
    for i in range(len(prices)):
        if i < period:
            result.append(None)
        else:
            result.append(np.mean(prices[i-period:i]))
    return result

# GOOD: Vectorized
def calculate_sma_fast(prices, period):
    return pd.Series(prices).rolling(window=period).mean()
```

### 5. Logging & Monitoring

```python
import logging
import time
from functools import wraps

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Performance decorator
def log_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        
        logger.info(f"{func.__name__} executed in {elapsed:.3f}s")
        
        # Alert if slow
        if elapsed > 1.0:
            logger.warning(f"Slow execution: {func.__name__} took {elapsed:.3f}s")
        
        return result
    return wrapper

class MonitoredStrategy(BaseStrategy):
    @log_performance
    def on_data(self, data):
        signals = super().on_data(data)
        
        # Log signal metrics
        logger.info(f"Generated {len(signals)} signals")
        
        # Send metrics to monitoring
        self._record_metrics({
            'signals_generated': len(signals),
            'avg_signal_strength': np.mean([s.strength for s in signals]) if signals else 0
        })
        
        return signals
```

---

## File Structure

```
strategies/
├── __init__.py
├── base_strategy.py          # BaseStrategy, Signal, StrategyConfig
├── strategy_orchestrator.py  # StrategyOrchestrator
├── signal_processor.py       # SignalProcessor, TradingDecision
├── strategy_factory.py       # StrategyFactory
├── mean_reversion.py         # MeanReversionStrategy
├── momentum.py               # MomentumStrategy
├── arbitrage.py              # ArbitrageStrategy
├── vwap.py                   # VWAPStrategy
├── composite.py              # CompositeStrategy
└── utils/
    ├── indicators.py         # Custom indicator calculations
    ├── filters.py            # Signal filters
    └── validators.py         # Data validation utilities

tests/
├── test_base_strategy.py
├── test_mean_reversion.py
├── test_orchestrator.py
├── test_signal_processor.py
└── test_integration.py

config/
└── strategies.yaml           # Strategy configurations

examples/
├── backtest_example.py       # How to backtest a strategy
├── live_example.py           # How to run live
└── optimization_example.py   # How to optimize parameters
```

---

## Quick Start Commands

```bash
# Install dependencies
pip install pandas pandas-ta pyyaml backtesting

# Run strategy tests
pytest tests/test_strategies.py -v

# Backtest a strategy
python examples/backtest_example.py --config config/strategies.yaml --strategy mean_reversion

# Optimize strategy parameters
python examples/optimization_example.py --strategy mean_reversion --metric sharpe

# Run strategy with paper trading
python examples/live_example.py --mode paper --config config/strategies.yaml

# Generate strategy report
python -m strategies.report_generator --output report.html
```

---

## Summary

This development guide provides:

1. **Complete Architecture**: Base classes, orchestrator, and signal processor
2. **Production-Ready Code**: Error handling, logging, performance optimization
3. **Testing Framework**: Unit and integration tests
4. **Integration Patterns**: How to connect with other modules
5. **Best Practices**: Design patterns, configuration, monitoring

The strategy module is designed to be:
- **Modular**: Easy to add new strategies
- **Testable**: Comprehensive test coverage
- **Performant**: Vectorized operations and caching
- **Production-Ready**: Error handling and monitoring
- **MIT-Licensed**: Only commercial-safe dependencies

Next steps:
1. Implement BaseStrategy and test
2. Create MeanReversionStrategy as first working example
3. Build StrategyOrchestrator for multi-strategy support
4. Integrate with backtesting framework
5. Add SignalProcessor for decision aggregation
6. Connect with Risk Manager and Executor modules
