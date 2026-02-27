# RISK MANAGEMENT MODULE - RESEARCH PLAN
## Comprehensive Capital Protection & Position Sizing Framework

**Document Version:** 1.0  
**Last Updated:** 2026-02-10  
**Priority:** CRITICAL - All Phases  
**Estimated Development:** 2-3 Weeks

---

## Executive Summary

Risk management is the most critical module in the trading bot system. A strategy with positive expectancy can still fail catastrophically without proper risk controls. This research plan synthesizes academic research, industry best practices, and mathematical models to create a multi-layered risk management system.

**Key Sources:**
1. Kelly Criterion Research (https://www.litefinance.org/blog/for-beginners/best-technical-indicators/kelly-criterion-trading/)
2. Position Sizing Strategies (https://medium.com/@jpolec_72972/position-sizing-strategies-for-algo-traders-a-comprehensive-guide-c9a8fc2443c8)
3. Value at Risk (VaR) Literature (Research Source #7)
4. Backtesting.py Risk Metrics (https://kernc.github.io/backtesting.py/)

---

## Risk Management Philosophy

### The 5 Layers of Protection

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        RISK MANAGEMENT PYRAMID                                       │
│                      (Defense in Depth Strategy)                                     │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│  LAYER 5: CATASTROPHIC RISK                                                        │
│  ┌───────────────────────────────────────────────────────────────────────────────┐ │
│  │ • Exchange failure (withdrawal limits, insolvency)                            │ │
│  │ • API key compromise (emergency procedures)                                   │ │
│  │ • System failure (automatic circuit breakers)                                 │ │
│  │ • Market halt/black swan (max loss limits)                                    │ │
│  └───────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                     │
│  LAYER 4: PORTFOLIO RISK                                                           │
│  ┌───────────────────────────────────────────────────────────────────────────────┐ │
│  │ • Portfolio heat (max 50% exposure)                                           │ │
│  │ • Correlation limits (< 0.7 between strategies)                               │ │
│  │ • Daily loss limits (-5% account = stop)                                      │ │
│  │ • Weekly loss limits (-10% account = pause)                                   │ │
│  └───────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                     │
│  LAYER 3: STRATEGY RISK                                                            │
│  ┌───────────────────────────────────────────────────────────────────────────────┐ │
│  │ • Max position size (per strategy allocation)                                 │ │
│  │ • Consecutive loss limit (5 losses = pause)                                   │ │
│  │ • Strategy drawdown limit (-20% = disable)                                    │ │
│  │ • Signal quality filters (VaR, correlation)                                   │ │
│  └───────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                     │
│  LAYER 2: POSITION RISK                                                            │
│  ┌───────────────────────────────────────────────────────────────────────────────┐ │
│  │ • Kelly Criterion sizing (fractional)                                         │ │
│  │ • Stop losses (2x ATR or fixed %)                                             │ │
│  │ • Take profits (risk/reward ratio)                                            │ │
│  │ • Time exits (max hold time)                                                  │ │
│  └───────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                     │
│  LAYER 1: SIGNAL RISK                                                              │
│  ┌───────────────────────────────────────────────────────────────────────────────┐ │
│  │ • Minimum signal strength (confidence > 60%)                                  │ │
│  │ • Volatility filtering (VaR threshold)                                        │ │
│  │ • Market regime filters (trend/volatility)                                    │ │
│  │ • Liquidity checks (minimum volume)                                           │ │
│  └───────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Position Sizing Research

### 1.1 Kelly Criterion Implementation

**Source:** Kelly Criterion Trading Guide (https://www.litefinance.org/blog/for-beginners/best-technical-indicators/kelly-criterion-trading/)

**Mathematical Foundation:**

```python
# risk/kelly_criterion.py
"""
Kelly Criterion position sizing implementation.

Based on: Edward Thorp's Kelly Criterion
Source: https://www.litefinance.org/blog/for-beginners/best-technical-indicators/kelly-criterion-trading/
"""

import numpy as np
from typing import Dict, Tuple
from dataclasses import dataclass

@dataclass
class BacktestStats:
    """Statistics from backtest results"""
    win_rate: float
    avg_win: float
    avg_loss: float
    total_trades: int
    
class KellyCriterion:
    """
    Kelly Criterion position sizing calculator.
    
    Formula: f* = (bp - q) / b
    Where:
        f* = Kelly fraction (optimal bet size)
        b = win/loss ratio (average win / average loss)
        p = probability of win
        q = probability of loss (1 - p)
    
    Source: https://www.litefinance.org/blog/for-beginners/best-technical-indicators/kelly-criterion-trading/
    """
    
    def __init__(self, kelly_fraction: float = 0.5):
        """
        Args:
            kelly_fraction: Fraction of Kelly to use (0.5 = Half Kelly)
                            Lower = safer, higher = more aggressive
        """
        self.kelly_fraction = kelly_fraction
        
    def calculate_kelly_fraction(self, stats: BacktestStats) -> float:
        """
        Calculate optimal Kelly fraction.
        
        Args:
            stats: Backtest statistics
            
        Returns:
            Optimal fraction of capital to allocate (0.0 to 1.0)
        """
        if stats.avg_loss == 0:
            return 0
        
        # Calculate components
        p = stats.win_rate  # Probability of win
        q = 1 - p  # Probability of loss
        b = stats.avg_win / abs(stats.avg_loss)  # Win/loss ratio
        
        # Kelly formula
        kelly = (b * p - q) / b
        
        # Apply safety fraction
        kelly = kelly * self.kelly_fraction
        
        # Bound between 0 and max allowed
        return max(0, min(kelly, 0.25))  # Cap at 25%
    
    def calculate_position_size(
        self,
        account_balance: float,
        entry_price: float,
        stop_price: float,
        stats: BacktestStats
    ) -> Dict[str, float]:
        """
        Calculate position size based on Kelly Criterion.
        
        Args:
            account_balance: Current account balance
            entry_price: Planned entry price
            stop_price: Stop loss price
            stats: Backtest statistics
            
        Returns:
            Dictionary with position sizing details
        """
        # Calculate Kelly fraction
        kelly_pct = self.calculate_kelly_fraction(stats)
        
        # Calculate position size
        risk_amount = account_balance * kelly_pct
        
        # Calculate distance to stop
        stop_distance = abs(entry_price - stop_price) / entry_price
        
        # Position value
        position_value = risk_amount / stop_distance if stop_distance > 0 else 0
        
        # Number of units
        quantity = position_value / entry_price
        
        return {
            'kelly_fraction': kelly_pct,
            'risk_amount': risk_amount,
            'position_value': position_value,
            'quantity': quantity,
            'stop_distance_pct': stop_distance * 100,
            'risk_reward_ratio': None  # Calculate if target known
        }

# Example Usage
"""
# Calculate Kelly from backtest results
stats = BacktestStats(
    win_rate=0.55,
    avg_win=200,
    avg_loss=-100,
    total_trades=150
)

kelly = KellyCriterion(kelly_fraction=0.5)
position = kelly.calculate_position_size(
    account_balance=10000,
    entry_price=45000,
    stop_price=44000,
    stats=stats
)

# Result:
# Kelly Fraction: 16.25% (Half of 32.5%)
# Risk Amount: $1,625
# Position Value: $16,250 (10x leverage implied)
# Quantity: 0.361 BTC
"""
```

### 1.2 Alternative Position Sizing Methods

**Source:** Position Sizing Strategies Guide (https://medium.com/@jpolec_72972/position-sizing-strategies-for-algo-traders-a-comprehensive-guide-c9a8fc2443c8)

```python
# risk/position_sizers.py
"""
Multiple position sizing strategies for comparison.

Source: https://medium.com/@jpolec_72972/position-sizing-strategies-for-algo-traders-a-comprehensive-guide-c9a8fc2443c8
"""

from abc import ABC, abstractmethod
import numpy as np

class PositionSizer(ABC):
    """Abstract base class for position sizing strategies"""
    
    @abstractmethod
    def calculate_position(
        self,
        account_balance: float,
        entry_price: float,
        stop_price: float,
        **kwargs
    ) -> float:
        """Calculate position quantity"""
        pass

class FixedFractionalSizer(PositionSizer):
    """
    Fixed fractional position sizing.
    Risk fixed percentage of account per trade.
    
    Source: Position Sizing Strategies Guide
    """
    
    def __init__(self, risk_pct: float = 0.02):
        """
        Args:
            risk_pct: Risk percentage per trade (0.02 = 2%)
        """
        self.risk_pct = risk_pct
        
    def calculate_position(
        self,
        account_balance: float,
        entry_price: float,
        stop_price: float,
        **kwargs
    ) -> float:
        """Calculate position using fixed fractional method"""
        risk_amount = account_balance * self.risk_pct
        stop_distance = abs(entry_price - stop_price)
        
        if stop_distance == 0:
            return 0
        
        position_value = risk_amount / (stop_distance / entry_price)
        quantity = position_value / entry_price
        
        return quantity

class ATRBasedSizer(PositionSizer):
    """
    ATR-based position sizing.
    Adjust position size based on market volatility.
    
    Source: https://medium.com/@jpolec_72972/position-sizing-strategies-for-algo-traders-a-comprehensive-guide-c9a8fc2443c8
    """
    
    def __init__(self, risk_pct: float = 0.02, atr_multiplier: float = 2.0):
        """
        Args:
            risk_pct: Risk percentage per trade
            atr_multiplier: ATR multiplier for stop distance
        """
        self.risk_pct = risk_pct
        self.atr_multiplier = atr_multiplier
        
    def calculate_position(
        self,
        account_balance: float,
        entry_price: float,
        atr: float,
        **kwargs
    ) -> float:
        """
        Calculate position using ATR-based stop.
        
        Args:
            atr: Current ATR value
        """
        risk_amount = account_balance * self.risk_pct
        stop_distance = atr * self.atr_multiplier
        
        position_value = risk_amount / (stop_distance / entry_price)
        quantity = position_value / entry_price
        
        return quantity

class VolatilityAdjustedSizer(PositionSizer):
    """
    Volatility-adjusted position sizing.
    Reduce size in high volatility, increase in low volatility.
    """
    
    def __init__(self, base_risk_pct: float = 0.02, lookback: int = 20):
        self.base_risk_pct = base_risk_pct
        self.lookback = lookback
        
    def calculate_position(
        self,
        account_balance: float,
        entry_price: float,
        stop_price: float,
        volatility: float,
        avg_volatility: float,
        **kwargs
    ) -> float:
        """
        Adjust position size based on relative volatility.
        
        Args:
            volatility: Current volatility (e.g., ATR or std dev)
            avg_volatility: Average volatility over lookback period
        """
        # Adjust risk based on volatility
        vol_ratio = volatility / avg_volatility if avg_volatility > 0 else 1.0
        adjusted_risk = self.base_risk_pct / vol_ratio
        
        # Bound the adjustment
        adjusted_risk = max(0.005, min(adjusted_risk, 0.05))
        
        # Calculate position
        risk_amount = account_balance * adjusted_risk
        stop_distance = abs(entry_price - stop_price)
        
        if stop_distance == 0:
            return 0
        
        position_value = risk_amount / (stop_distance / entry_price)
        quantity = position_value / entry_price
        
        return quantity

class OptimalFSizer(PositionSizer):
    """
    Optimal F position sizing (Ralph Vince).
    Maximizes geometric growth rate.
    
    Source: Position Sizing Strategies Guide
    """
    
    def __init__(self, max_risk_pct: float = 0.25):
        self.max_risk_pct = max_risk_pct
        
    def calculate_optimal_f(self, returns: list) -> float:
        """
        Calculate Optimal F from historical trade returns.
        
        Args:
            returns: List of trade returns (as decimals)
            
        Returns:
            Optimal F fraction
        """
        returns = np.array(returns)
        
        # Find f that maximizes Terminal Wealth Relative (TWR)
        best_f = 0
        best_twr = 0
        
        for f in np.linspace(0.01, 0.99, 100):
            # Calculate Holding Period Returns (HPR)
            hprs = 1 + (-returns.min() / returns) * f
            
            # Calculate Terminal Wealth Relative
            twr = np.prod(hprs)
            
            if twr > best_twr:
                best_twr = twr
                best_f = f
        
        return min(best_f, self.max_risk_pct)
```

### 1.3 Position Sizing Comparison Matrix

| Method | Pros | Cons | Best For |
|--------|------|------|----------|
| **Kelly Criterion** | Optimal growth, accounts for edge | Requires accurate stats, can be volatile | Proven strategies with history |
| **Fixed Fractional** | Simple, consistent risk | Doesn't account for win rate | Beginners, consistent volatility |
| **ATR-Based** | Adapts to volatility | Requires ATR calculation | Trending markets, breakout strategies |
| **Volatility Adjusted** | Dynamic risk adjustment | Complex calculation | Multi-market portfolios |
| **Optimal F** | Maximizes geometric growth | Aggressive, high drawdowns | High tolerance for risk |

---

## Phase 2: Stop Loss & Exit Management

### 2.1 Stop Loss Strategies

```python
# risk/stop_loss_manager.py
"""
Stop loss calculation and management.
Multiple stop types for different market conditions.
"""

import pandas as pd
import numpy as np
from typing import Optional

class StopLossManager:
    """
    Manages stop loss calculations and trailing stops.
    """
    
    @staticmethod
    def calculate_atr_stop(
        data: pd.DataFrame,
        entry_price: float,
        atr_period: int = 14,
        multiplier: float = 2.0,
        side: str = 'long'
    ) -> float:
        """
        Calculate ATR-based stop loss.
        
        Args:
            data: OHLCV DataFrame
            entry_price: Entry price
            atr_period: ATR lookback period
            multiplier: ATR multiplier (typically 2.0-3.0)
            side: 'long' or 'short'
            
        Returns:
            Stop loss price
        """
        import pandas_ta as ta
        
        # Calculate ATR
        atr = ta.atr(data['high'], data['low'], data['close'], length=atr_period)
        current_atr = atr.iloc[-1]
        
        # Calculate stop
        if side == 'long':
            stop = entry_price - (current_atr * multiplier)
        else:
            stop = entry_price + (current_atr * multiplier)
        
        return stop
    
    @staticmethod
    def calculate_support_resistance_stop(
        data: pd.DataFrame,
        entry_price: float,
        lookback: int = 20,
        side: str = 'long'
    ) -> float:
        """
        Calculate stop based on recent support/resistance.
        
        Args:
            data: OHLCV DataFrame
            entry_price: Entry price
            lookback: Period to look for S/R levels
            side: 'long' or 'short'
        """
        if side == 'long':
            # Use recent swing low as stop
            recent_lows = data['low'].rolling(lookback).min()
            stop = recent_lows.iloc[-1]
        else:
            # Use recent swing high as stop
            recent_highs = data['high'].rolling(lookback).max()
            stop = recent_highs.iloc[-1]
        
        return stop
    
    @staticmethod
    def calculate_trailing_stop(
        current_price: float,
        highest_price: float,
        trailing_pct: float = 0.05,
        side: str = 'long'
    ) -> float:
        """
        Calculate trailing stop price.
        
        Args:
            current_price: Current market price
            highest_price: Highest price since entry (for longs)
            trailing_pct: Trailing distance percentage
            side: 'long' or 'short'
        """
        if side == 'long':
            # Trail below highest price
            stop = highest_price * (1 - trailing_pct)
        else:
            # Trail above lowest price (would need lowest_price parameter)
            stop = highest_price * (1 + trailing_pct)
        
        return stop
    
    @staticmethod
    def calculate_time_stop(
        entry_time: pd.Timestamp,
        current_time: pd.Timestamp,
        max_hold_hours: int = 48
    ) -> bool:
        """
        Check if time-based exit should trigger.
        
        Args:
            entry_time: Position entry timestamp
            current_time: Current timestamp
            max_hold_hours: Maximum holding period
            
        Returns:
            True if time stop triggered
        """
        hold_time = current_time - entry_time
        return hold_time.total_seconds() > (max_hold_hours * 3600)

class TrailingStopTracker:
    """
    Tracks and updates trailing stops for open positions.
    """
    
    def __init__(self, trailing_pct: float = 0.05):
        self.trailing_pct = trailing_pct
        self.positions = {}  # position_id -> stop_data
        
    def add_position(
        self,
        position_id: str,
        entry_price: float,
        side: str,
        initial_stop: float
    ):
        """Add new position to tracker"""
        self.positions[position_id] = {
            'entry_price': entry_price,
            'side': side,
            'highest_price': entry_price if side == 'long' else entry_price,
            'lowest_price': entry_price if side == 'short' else entry_price,
            'current_stop': initial_stop
        }
        
    def update_price(self, position_id: str, current_price: float):
        """Update with new price and adjust stop if needed"""
        if position_id not in self.positions:
            return None
        
        pos = self.positions[position_id]
        
        if pos['side'] == 'long':
            # Update highest price
            if current_price > pos['highest_price']:
                pos['highest_price'] = current_price
                # Move stop up
                new_stop = pos['highest_price'] * (1 - self.trailing_pct)
                if new_stop > pos['current_stop']:
                    pos['current_stop'] = new_stop
                    return {'action': 'update_stop', 'new_stop': new_stop}
        else:
            # Update lowest price
            if current_price < pos['lowest_price']:
                pos['lowest_price'] = current_price
                # Move stop down
                new_stop = pos['lowest_price'] * (1 + self.trailing_pct)
                if new_stop < pos['current_stop']:
                    pos['current_stop'] = new_stop
                    return {'action': 'update_stop', 'new_stop': new_stop}
        
        # Check if stop hit
        if pos['side'] == 'long' and current_price <= pos['current_stop']:
            return {'action': 'stop_hit', 'stop_price': pos['current_stop']}
        elif pos['side'] == 'short' and current_price >= pos['current_stop']:
            return {'action': 'stop_hit', 'stop_price': pos['current_stop']}
        
        return None
```

### 2.2 Risk/Reward Ratio Management

```python
# risk/risk_reward.py
"""
Risk/Reward ratio calculation and validation.
"""

class RiskRewardManager:
    """
    Manages risk/reward ratios for trades.
    Ensures minimum profitability threshold.
    """
    
    MIN_RISK_REWARD = 1.5  # Minimum 1:1.5 risk/reward
    
    @staticmethod
    def calculate_risk_reward(
        entry_price: float,
        stop_price: float,
        target_price: float
    ) -> dict:
        """
        Calculate risk/reward ratio.
        
        Returns:
            Dictionary with risk, reward, and ratio
        """
        risk = abs(entry_price - stop_price)
        reward = abs(target_price - entry_price)
        
        ratio = reward / risk if risk > 0 else 0
        
        return {
            'risk': risk,
            'reward': reward,
            'ratio': ratio,
            'risk_pct': (risk / entry_price) * 100,
            'reward_pct': (reward / entry_price) * 100,
            'acceptable': ratio >= RiskRewardManager.MIN_RISK_REWARD
        }
    
    @staticmethod
    def validate_trade_setup(
        entry_price: float,
        stop_price: float,
        target_price: float,
        min_ratio: float = 1.5
    ) -> bool:
        """
        Validate if trade meets minimum risk/reward requirement.
        
        Returns:
            True if trade is acceptable
        """
        result = RiskRewardManager.calculate_risk_reward(
            entry_price, stop_price, target_price
        )
        return result['ratio'] >= min_ratio
```

---

## Phase 3: Portfolio-Level Risk Management

### 3.1 Portfolio Heat & Exposure

```python
# risk/portfolio_risk.py
"""
Portfolio-level risk management.
Controls total exposure and correlation.
"""

import pandas as pd
import numpy as np
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class Position:
    symbol: str
    side: str  # 'long' or 'short'
    quantity: float
    entry_price: float
    current_price: float
    strategy_id: str

class PortfolioRiskManager:
    """
    Manages portfolio-level risk.
    Controls heat, correlation, and drawdown.
    """
    
    def __init__(
        self,
        max_portfolio_heat: float = 0.50,
        max_correlation: float = 0.70,
        max_daily_loss: float = 0.05,
        max_drawdown: float = 0.20
    ):
        """
        Args:
            max_portfolio_heat: Maximum % of capital at risk (0.5 = 50%)
            max_correlation: Maximum correlation between positions
            max_daily_loss: Maximum daily loss before stop (0.05 = 5%)
            max_drawdown: Maximum drawdown before pause (0.20 = 20%)
        """
        self.max_portfolio_heat = max_portfolio_heat
        self.max_correlation = max_correlation
        self.max_daily_loss = max_daily_loss
        self.max_drawdown = max_drawdown
        
        self.positions: List[Position] = []
        self.daily_pnl = []
        self.peak_equity = 0
        self.current_drawdown = 0
        
    def calculate_portfolio_heat(self, account_balance: float) -> float:
        """
        Calculate total portfolio heat (exposure).
        
        Heat = Sum of position values / Account balance
        """
        if not self.positions or account_balance == 0:
            return 0
        
        total_exposure = sum(
            pos.quantity * pos.current_price 
            for pos in self.positions
        )
        
        return total_exposure / account_balance
    
    def calculate_correlation_matrix(
        self,
        price_history: Dict[str, pd.Series]
    ) -> pd.DataFrame:
        """
        Calculate correlation matrix between symbols.
        
        Args:
            price_history: Dict of symbol -> price series
            
        Returns:
            Correlation matrix DataFrame
        """
        # Create returns DataFrame
        returns_df = pd.DataFrame()
        
        for symbol, prices in price_history.items():
            returns_df[symbol] = prices.pct_change()
        
        return returns_df.corr()
    
    def check_correlation_limits(
        self,
        new_position: Position,
        price_history: Dict[str, pd.Series]
    ) -> bool:
        """
        Check if new position would violate correlation limits.
        
        Returns:
            True if acceptable
        """
        if not self.positions:
            return True
        
        # Get correlation matrix
        corr_matrix = self.calculate_correlation_matrix(price_history)
        
        # Check correlation with existing positions
        for pos in self.positions:
            if pos.symbol in corr_matrix.columns and new_position.symbol in corr_matrix.columns:
                corr = corr_matrix.loc[pos.symbol, new_position.symbol]
                
                if abs(corr) > self.max_correlation:
                    return False
        
        return True
    
    def calculate_drawdown(self, current_equity: float) -> float:
        """
        Calculate current drawdown from peak.
        
        Returns:
            Drawdown as decimal (0.10 = 10% drawdown)
        """
        # Update peak
        if current_equity > self.peak_equity:
            self.peak_equity = current_equity
            self.current_drawdown = 0
        else:
            self.current_drawdown = (self.peak_equity - current_equity) / self.peak_equity
        
        return self.current_drawdown
    
    def check_daily_loss(self, daily_pnl: float, account_balance: float) -> bool:
        """
        Check if daily loss exceeds limit.
        
        Returns:
            True if within limit
        """
        loss_pct = abs(daily_pnl) / account_balance
        return loss_pct < self.max_daily_loss
    
    def can_add_position(
        self,
        new_position: Position,
        account_balance: float,
        price_history: Dict[str, pd.Series]
    ) -> Dict:
        """
        Check if new position can be added.
        
        Returns:
            Dictionary with decision and reasons
        """
        result = {'can_add': True, 'reasons': []}
        
        # Check portfolio heat
        temp_positions = self.positions + [new_position]
        temp_heat = self.calculate_portfolio_heat_with_positions(
            temp_positions, account_balance
        )
        
        if temp_heat > self.max_portfolio_heat:
            result['can_add'] = False
            result['reasons'].append(
                f"Portfolio heat {temp_heat:.1%} exceeds limit {self.max_portfolio_heat:.1%}"
            )
        
        # Check correlation
        if not self.check_correlation_limits(new_position, price_history):
            result['can_add'] = False
            result['reasons'].append(
                f"Correlation with existing positions exceeds {self.max_correlation}"
            )
        
        return result
    
    @staticmethod
    def calculate_portfolio_heat_with_positions(
        positions: List[Position],
        account_balance: float
    ) -> float:
        """Helper to calculate heat with temporary position list"""
        if not positions or account_balance == 0:
            return 0
        
        total_exposure = sum(
            pos.quantity * pos.current_price 
            for pos in positions
        )
        
        return total_exposure / account_balance

class CircuitBreaker:
    """
    Emergency circuit breaker for catastrophic risk.
    """
    
    def __init__(
        self,
        max_daily_loss: float = 0.05,
        max_drawdown: float = 0.20,
        consecutive_losses: int = 5
    ):
        self.max_daily_loss = max_daily_loss
        self.max_drawdown = max_drawdown
        self.consecutive_losses = consecutive_losses
        
        self.is_triggered = False
        self.trigger_reason = None
        self.loss_streak = 0
        
    def check(self, daily_pnl: float, drawdown: float, account_balance: float):
        """
        Check if circuit breaker should trigger.
        
        Returns:
            True if trading should stop
        """
        if self.is_triggered:
            return True
        
        # Check daily loss
        daily_loss_pct = abs(daily_pnl) / account_balance
        if daily_loss_pct >= self.max_daily_loss:
            self.is_triggered = True
            self.trigger_reason = f"Daily loss {daily_loss_pct:.1%} exceeds {self.max_daily_loss:.1%}"
            return True
        
        # Check drawdown
        if drawdown >= self.max_drawdown:
            self.is_triggered = True
            self.trigger_reason = f"Drawdown {drawdown:.1%} exceeds {self.max_drawdown:.1%}"
            return True
        
        # Check consecutive losses
        if daily_pnl < 0:
            self.loss_streak += 1
            if self.loss_streak >= self.consecutive_losses:
                self.is_triggered = True
                self.trigger_reason = f"{self.consecutive_losses} consecutive losses"
                return True
        else:
            self.loss_streak = 0
        
        return False
    
    def reset(self):
        """Reset circuit breaker after review"""
        self.is_triggered = False
        self.trigger_reason = None
        self.loss_streak = 0
```

---

## Phase 4: Value at Risk (VaR) Implementation

### 4.1 VaR Calculation

**Source:** Research Source #7 (Mean Reversion with VaR Filter)

```python
# risk/var_calculator.py
"""
Value at Risk (VaR) calculations for volatility filtering.
Based on: Quantitativo Research (Source #7)
"""

import numpy as np
import pandas as pd
from typing import Literal

class VaRCalculator:
    """
    Calculate Value at Risk for volatility filtering.
    
    Source: https://www.quantitativo.com/p/a-mean-reversion-strategy-with-211
    """
    
    def __init__(self, confidence: float = 0.95, lookback: int = 20):
        """
        Args:
            confidence: Confidence level (0.95 = 95%)
            lookback: Historical lookback period
        """
        self.confidence = confidence
        self.lookback = lookback
    
    def calculate_historical_var(
        self,
        returns: pd.Series,
        method: Literal['simple', 'weighted'] = 'simple'
    ) -> float:
        """
        Calculate historical VaR.
        
        Args:
            returns: Series of returns
            method: 'simple' (equally weighted) or 'weighted' (recent weighted)
            
        Returns:
            VaR value (negative for loss)
        """
        if method == 'simple':
            # Simple historical VaR
            var = np.percentile(returns.dropna(), (1 - self.confidence) * 100)
        else:
            # Weighted historical VaR (more weight to recent data)
            weights = np.exp(np.linspace(-1., 0., len(returns)))
            weights /= weights.sum()
            
            sorted_returns = np.sort(returns.dropna())
            weighted_cdf = np.cumsum(weights)
            
            var_idx = np.searchsorted(weighted_cdf, 1 - self.confidence)
            var = sorted_returns[var_idx]
        
        return var
    
    def calculate_parametric_var(
        self,
        returns: pd.Series
    ) -> float:
        """
        Calculate parametric VaR assuming normal distribution.
        
        VaR = μ - z × σ
        Where z is the z-score for confidence level
        """
        mean = returns.mean()
        std = returns.std()
        
        # Z-score for confidence level
        from scipy import stats
        z_score = stats.norm.ppf(1 - self.confidence)
        
        var = mean + z_score * std
        return var
    
    def calculate_conditional_var(
        self,
        returns: pd.Series
    ) -> float:
        """
        Calculate Conditional VaR (Expected Shortfall).
        Average of losses beyond VaR threshold.
        """
        var = self.calculate_historical_var(returns)
        cvar = returns[returns <= var].mean()
        return cvar
    
    def should_trade(self, returns: pd.Series, threshold: float = -0.02) -> bool:
        """
        Check if VaR is within acceptable range.
        
        Source: Research Source #7 - VaR filter improved Sharpe from 0.83 to 1.43
        
        Args:
            returns: Recent returns series
            threshold: VaR threshold (e.g., -0.02 = -2%)
            
        Returns:
            True if safe to trade
        """
        var = self.calculate_historical_var(returns)
        return var > threshold  # VaR > -2% means less tail risk

# Example: Use VaR filter in strategy
"""
def on_data(self, data):
    returns = data['close'].pct_change()
    
    # Check VaR filter
    var_calc = VaRCalculator(confidence=0.95)
    if not var_calc.should_trade(returns, threshold=-0.02):
        # Too volatile, skip signal
        return []
    
    # Continue with signal generation...
"""
```

---

## Phase 5: Implementation Timeline

### Week 1: Core Risk Management
- Day 1-2: Kelly Criterion implementation
- Day 3-4: Position sizers (Fixed, ATR, Volatility)
- Day 5-7: Stop loss calculations

### Week 2: Portfolio Risk
- Day 1-2: Portfolio heat calculator
- Day 3-4: Correlation analysis
- Day 5-7: Circuit breaker implementation

### Week 3: Advanced Risk
- Day 1-3: VaR calculator
- Day 4-5: Risk/reward validation
- Day 6-7: Integration with strategy module

### Week 4: Testing
- Day 1-3: Unit tests
- Day 4-5: Integration tests
- Day 6-7: Documentation

---

## Risk Limits Summary

| Level | Metric | Limit | Action |
|-------|--------|-------|--------|
| **Signal** | VaR(95%) | > -2% | Skip trade |
| **Position** | Risk/Trade | 2% max | Reduce size |
| **Position** | Stop Loss | 2x ATR | Exit position |
| **Strategy** | Drawdown | -20% | Disable strategy |
| **Strategy** | Consecutive Losses | 5 | Pause strategy |
| **Portfolio** | Heat | 50% max | No new positions |
| **Portfolio** | Daily Loss | -5% | Stop trading |
| **Portfolio** | Drawdown | -20% | Circuit breaker |

---

## Success Criteria

- [ ] All position sizing methods implemented
- [ ] Kelly Criterion working with backtest stats
- [ ] Multiple stop loss types available
- [ ] Portfolio heat monitoring active
- [ ] Circuit breaker functional
- [ ] VaR filter integrated
- [ ] Risk/reward validation on all trades
- [ ] Unit tests covering edge cases

---

*Risk Management Research Plan Complete*
*Critical for Capital Preservation*
