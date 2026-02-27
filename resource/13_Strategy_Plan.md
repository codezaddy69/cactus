# TRADING BOT STRATEGY PLAN
## Complete Implementation Roadmap

**Document Version:** 1.0  
**Last Updated:** 2026-02-10  
**Status:** Research Complete, Ready for Implementation  
**Framework:** RBI (Research → Backtest → Implement)

---

## Executive Summary

### Strategic Decisions Made

Based on comprehensive research of 9+ sources, analysis of 14 strategy types, and evaluation of portfolio construction approaches, the following strategic decisions have been finalized:

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Primary Strategy** | Mean Reversion (RSI + Bollinger Bands) | Research source #7 achieved 1.43 Sharpe out-of-sample with VaR filter |
| **Starting Approach** | Single Strategy | Lower risk, faster iteration, proven sufficiency |
| **Symbols** | BTC/USDT, ETH/USDT | High liquidity, tight spreads, reliable data |
| **Timeframe** | 1H primary, 4H confirmation | Balance between signal quality and trade frequency |
| **Risk per Trade** | 2% (Kelly-adjusted) | Optimal growth with safety buffer |
| **Leverage** | 1x (no leverage initially) | Minimize catastrophic risk during development |
| **Backtest Engine** | Backtesting.py | MIT license, fast, proven, excellent metrics |
| **Indicators** | Pandas TA | 150+ indicators, MIT license, vectorized |

### Expected Performance Targets

```
Phase 1 (Single Strategy):
├── Sharpe Ratio: 1.0 - 1.4
├── Annual Return: 15 - 25%
├── Max Drawdown: 15 - 20%
├── Win Rate: 50 - 55%
└── Trade Frequency: 8 - 12 per month

Phase 2 (Dual Strategy):
├── Portfolio Sharpe: 1.2 - 1.6
├── Correlation: < 0.5 between strategies
├── Max Drawdown: 12 - 15%
└── Diversification benefit: +20% risk-adjusted return

Phase 3 (Multi-Strategy):
├── Portfolio Sharpe: 1.5 - 2.0
├── Max Drawdown: < 12%
└── Strategies: 5 - 7 uncorrelated
```

---

## Phase 1: Mean Reversion Strategy (Immediate Implementation)

### Strategy Logic

**Entry Conditions (ALL must be true):**
```
1. RSI(14) < 30 (oversold momentum condition)
2. Price < Lower Bollinger Band(20, 2.0) (statistical cheapness)
3. VaR(95%) < -2% (low tail risk environment)
4. Volume > 1.0x 20-period average (confirm interest)
```

**Exit Conditions (ANY can trigger):**
```
1. RSI(14) > 70 (overbought)
2. Price > Upper Bollinger Band (statistically expensive)
3. Trailing stop: 2x ATR(14) from entry
4. Time exit: 48 hours maximum hold
5. Emergency: VaR > -5% (high volatility)
```

**Position Sizing:**
```
Position Size = min(
    Account Balance × Kelly Fraction × 0.5,
    Account Balance × 0.02,  # Max 2% risk
    Strategy Max Position Size
)

Where Kelly Fraction = (Win Rate × Avg Win - Loss Rate × Avg Loss) / Avg Win
```

### Technical Implementation

**Files Required:**
```
strategies/
├── mean_reversion.py           # Core strategy logic
├── indicators.py               # Custom indicator calculations
└── config/
    └── mean_reversion.yaml     # Strategy parameters
```

**Key Components:**

```python
# 1. Signal Generation
class MeanReversionStrategy(BaseStrategy):
    def generate_signals(self, data):
        indicators = self.calculate_indicators(data)
        
        if (indicators['rsi'] < 30 and 
            data['close'] < indicators['bb_lower'] and
            indicators['var_95'] > -0.02):
            return Signal.BUY
            
        elif (indicators['rsi'] > 70 or 
              data['close'] > indicators['bb_upper']):
            return Signal.SELL
```

```python
# 2. Risk Filter (VaR)
def calculate_var_filter(self, returns, confidence=0.95):
    """
    Value at Risk filter
    Only trade when tail risk is acceptable
    """
    var = np.percentile(returns, (1 - confidence) * 100)
    return var > self.var_threshold  # -0.02
```

```python
# 3. Position Sizing (Kelly Criterion)
def calculate_kelly_size(self, backtest_stats):
    """
    Calculate Kelly fraction from historical performance
    Use Half-Kelly for safety
    """
    win_rate = backtest_stats['win_rate']
    avg_win = backtest_stats['avg_win']
    avg_loss = abs(backtest_stats['avg_loss'])
    
    if avg_loss == 0:
        return 0
    
    win_loss_ratio = avg_win / avg_loss
    kelly = (win_loss_ratio * win_rate - (1 - win_rate)) / win_loss_ratio
    
    # Use Half-Kelly for crypto volatility
    return max(0, min(kelly * 0.5, 0.25))
```

### Performance Expectations

Based on Research Source #7 (Quantitativo):

| Metric | Training | Out-of-Sample | Conservative Target |
|--------|----------|---------------|---------------------|
| **Sharpe Ratio** | 0.83 | 1.43 | 1.0 |
| **Annual Return** | 7.1% | ~12% | 15% |
| **Max Drawdown** | -15% | -12% | -18% |
| **Time Invested** | 18% | 18% | 20% |
| **Win Rate** | ~52% | ~54% | 50% |

**Key Insights from Research:**
- VaR filter improved Sharpe from 0.83 to 1.43
- Strategy improved on out-of-sample data (rare)
- Parameter sensitivity exists (requires robustness testing)
- Only 18% market exposure = efficient capital use

---

## Phase 2: Strategy Diversification (Weeks 7-12)

### Strategy Selection Criteria

**Primary Filter: Correlation < 0.5 with existing strategies**

| Strategy | Market Regime | Expected Sharpe | Correlation to Mean Rev |
|----------|--------------|-----------------|------------------------|
| Mean Reversion | Ranging | 1.2 - 1.4 | 1.00 |
| Momentum (MACD) | Trending | 0.9 - 1.2 | 0.30 |
| Arbitrage | Any | 2.0+ | 0.10 |
| Liquidation | Volatile | 1.5 - 2.0 | 0.40 |

### Strategy 2: Momentum (MACD + ADX)

**Logic:**
```
Entry: MACD line crosses above signal line AND ADX > 25
Exit: MACD crosses below signal line OR ADX < 20
Filter: Only trade in direction of 200 EMA trend
```

**Parameters:**
- MACD Fast: 12
- MACD Slow: 26
- MACD Signal: 9
- ADX Period: 14
- ADX Threshold: 25

**Expected Performance:**
- Sharpe: 0.9 - 1.2
- Win Rate: 45 - 50%
- Best Performance: Strong trending markets

### Strategy 3: Cross-Exchange Arbitrage

**Logic:**
```
Entry: Price discrepancy > (fees + 0.1% buffer)
Execution: Buy low exchange, sell high exchange simultaneously
Exit: Automatic (instant arb)
Hold Time: < 1 second
```

**Requirements:**
- Accounts on 2+ exchanges (Binance, Coinbase)
- Minimum $5K capital per exchange
- Low-latency execution (< 500ms)

**Expected Performance:**
- Sharpe: 2.0+
- Returns: 15 - 30% annually
- Risk: Very low (market neutral)
- Frequency: 5 - 20 opportunities per day

### Portfolio Construction

**Allocation Weights (Equal Risk Contribution):**

```yaml
portfolio_allocation:
  mean_reversion:
    weight: 0.40
    target_volatility: 0.15
    max_drawdown: 0.18
    
  momentum:
    weight: 0.30
    target_volatility: 0.18
    max_drawdown: 0.22
    
  arbitrage:
    weight: 0.30
    target_volatility: 0.05
    max_drawdown: 0.03
```

**Dynamic Rebalancing:**
- Frequency: Weekly
- Logic: Increase weight to strategies with higher recent Sharpe
- Threshold: Rebalance if weight deviates > 10% from target

---

## Phase 3: Advanced Strategies (Weeks 13-20)

### Strategy 4: Liquidation Cascade Hunter

**Data Required:**
- Real-time liquidation feeds (CoinGlass API)
- Order book depth
- Funding rates

**Logic:**
```
Entry Conditions:
1. Large liquidation cluster identified (> $500K)
2. Gap to next cluster > 2%
3. Price has pulled back 1 candle (confirmation)
4. Trading with trend (20 EMA filter)

Exit: Close position before gap fills or after 4 hours
```

**Performance:**
- Sharpe: 1.5 - 2.0
- Win Rate: 60 - 70%
- Trade Frequency: 2 - 5 per week
- Best for: High volatility periods

### Strategy 5: Funding Rate Arbitrage

**Logic:**
```
Entry: Funding rate > 0.1% (8-hour period)
Strategy: 
  - If positive funding: Short perpetual, buy spot
  - If negative funding: Long perpetual, sell spot
  
Hold: Until funding rate reverts or 24 hours
```

**Expected Performance:**
- Returns: 15 - 25% annually
- Risk: Very low (delta neutral)
- Capital Requirement: $10K+ (split across spot and futures)

### Full Multi-Strategy Portfolio

**Final Allocation (Target State):**

```
Strategy Portfolio (5-7 strategies)
├── Mean Reversion:        25% ($12.5K of $50K)
├── Momentum:              20% ($10K)
├── Arbitrage:             20% ($10K)
├── Liquidation Hunter:    15% ($7.5K)
├── VWAP Microstructure:   10% ($5K)
├── Funding Rate Arb:      10% ($10K)
└── Cash Reserve:           0% (fully deployed)

Target Portfolio Metrics:
├── Portfolio Sharpe:      1.5 - 2.0
├── Max Drawdown:          < 12%
├── Annual Return:         25 - 40%
└── Strategy Correlation:  < 0.5 (average)
```

---

## A/B Testing Framework

### Continuous Optimization Pipeline

**Active A/B Tests (Always Running 1-2):**

```python
# Current Test Queue
test_queue = [
    {
        'name': 'RSI_Period_Optimization',
        'variant_a': {'rsi_period': 14},
        'variant_b': {'rsi_period': 21},
        'metric': 'sharpe_ratio',
        'min_trades': 50,
        'status': 'RUNNING'
    },
    {
        'name': 'BB_Standard_Deviation',
        'variant_a': {'bb_std': 2.0},
        'variant_b': {'bb_std': 2.5},
        'metric': 'win_rate',
        'min_trades': 50,
        'status': 'QUEUED'
    },
    {
        'name': 'Exit_Strategy',
        'variant_a': {'exit_type': 'fixed_levels'},
        'variant_b': {'exit_type': 'trailing_stop'},
        'metric': 'profit_factor',
        'min_trades': 75,
        'status': 'PLANNED'
    }
]
```

### Test Execution Protocol

**Week 1-2: Setup**
- Define hypothesis
- Configure 50/50 capital split
- Deploy both variants
- Set minimum sample size (50 trades)

**Week 3-5: Data Collection**
- Run both variants simultaneously
- Monitor daily metrics
- Ensure sufficient trade count
- Check for early stopping conditions

**Week 6: Analysis**
- Calculate statistical significance (t-test)
- Evaluate practical significance
- Make deployment decision
- Document learnings

**Statistical Decision Rules:**
```
IF p_value < 0.05 AND practical_difference > 10%:
    → Deploy winner to 100% allocation
ELIF p_value >= 0.05:
    → Inconclusive, extend test OR try different variants
ELIF early_stop_triggered (loser down > 10%):
    → Early termination, deploy winner
```

---

## Risk Management Integration

### Strategy-Level Risk Controls

```python
strategy_risk_limits = {
    'max_position_size': 0.25,  # 25% of account per strategy
    'max_risk_per_trade': 0.02,  # 2% risk per trade
    'max_drawdown': 0.20,  # Pause strategy at 20% DD
    'max_daily_loss': 0.05,  # 5% daily loss limit
    'max_consecutive_losses': 5,  # Pause after 5 losses
    'correlation_limit': 0.70  # Max correlation with other strategies
}
```

### Portfolio-Level Risk Controls

```python
portfolio_risk_limits = {
    'max_portfolio_heat': 0.50,  # 50% max exposure
    'max_portfolio_drawdown': 0.15,  # 15% max DD
    'max_daily_loss': 0.03,  # 3% daily portfolio loss
    'max_strategy_correlation': 0.50,  # Average correlation
    'var_limit': 0.02,  # 95% VaR < 2%
    'circuit_breaker': True  # Emergency stop all
}
```

### Position Sizing Matrix

| Account Size | Risk/Trade | Max Position | Leverage | Max Concurrent |
|-------------|-----------|--------------|----------|----------------|
| $1K - $5K | 2% | $100 | 1x | 2 positions |
| $5K - $10K | 2% | $200 | 1x | 3 positions |
| $10K - $50K | 2% | $500 | 1x | 5 positions |
| $50K+ | 1.5% | $750 | 1-2x | 7 positions |

---

## Implementation Timeline

### Week-by-Week Breakdown

```
PHASE 1: Single Strategy (Weeks 1-6)
├── Week 1: Infrastructure Setup
│   ├── Set up Python environment (3.11+)
│   ├── Install dependencies (CCXT, Backtesting.py, Pandas TA)
│   ├── Create project structure
│   └── Test exchange connections (Binance testnet)
│
├── Week 2: Strategy Development
│   ├── Implement BaseStrategy class
│   ├── Code MeanReversionStrategy
│   ├── Add indicator calculations
│   └── Implement signal generation
│
├── Week 3: Backtesting
│   ├── Download 2 years historical data
│   ├── Run initial backtests
│   ├── Parameter optimization
│   └── Walk-forward validation
│
├── Week 4: Risk Management
│   ├── Implement Kelly position sizing
│   ├── Add VaR filter
│   ├── Create stop-loss logic
│   └── Circuit breaker implementation
│
├── Week 5: Paper Trading
│   ├── Deploy to testnet/paper trading
│   ├── Monitor for 1 week
│   ├── Fix bugs and issues
│   └── Validate execution logic
│
└── Week 6: Live Deployment (Small)
    ├── Deploy with $1,000 live
    ├── Monitor closely
    ├── Daily performance review
    └── Scale up if profitable

PHASE 2: Dual Strategy (Weeks 7-12)
├── Week 7: Momentum Strategy
├── Week 8: Arbitrage Strategy
├── Week 9: Portfolio Integration
├── Week 10: Backtest Portfolio
├── Week 11: Paper Trade Portfolio
└── Week 12: Live Portfolio ($5-10K)

PHASE 3: Multi-Strategy (Weeks 13-20)
├── Week 13-14: Liquidation Strategy
├── Week 15-16: Funding Rate Arb
├── Week 17-18: VWAP Microstructure
├── Week 19: Full Integration
└── Week 20: Production ($50K+)

PHASE 4: Optimization (Weeks 21+)
├── Continuous A/B testing
├── ML signal filtering
├── Advanced portfolio optimization
└── Scale capital gradually
```

---

## Success Metrics & KPIs

### Phase 1 Success Criteria

**Must Achieve (Non-negotiable):**
- [ ] Backtest Sharpe > 1.0
- [ ] Max drawdown < 20%
- [ ] Positive return over 3-month backtest
- [ ] No critical bugs in paper trading
- [ ] Correct order execution (100% accuracy)

**Nice to Have:**
- [ ] Backtest Sharpe > 1.2
- [ ] Live profit after 2 weeks
- [ ] Win rate > 50%
- [ ] Average trade > $10 profit

### Phase 2 Success Criteria

- [ ] Portfolio Sharpe > individual average
- [ ] Strategy correlation < 0.5
- [ ] Max drawdown < 15%
- [ ] Each strategy profitable independently
- [ ] System uptime > 99%

### Phase 3 Success Criteria

- [ ] Portfolio Sharpe > 1.5
- [ ] Max drawdown < 12%
- [ ] Annual return > 25%
- [ ] Fully autonomous operation
- [ ] Comprehensive monitoring and alerting

---

## Technical Stack Requirements

### Core Dependencies

```txt
# requirements.txt
pandas>=2.0.0
pandas-ta>=0.3.0
numpy>=1.24.0
backtesting>=0.3.0
ccxt>=4.0.0
fastapi>=0.100.0
websockets>=11.0
pydantic>=2.0
pyyaml>=6.0
scikit-learn>=1.3.0
scipy>=1.11.0
python-dotenv>=1.0.0
```

### Infrastructure

| Component | Technology | License | Purpose |
|-----------|-----------|---------|---------|
| Exchange API | CCXT | MIT | Unified exchange connectivity |
| Backtesting | Backtesting.py | MIT | Strategy validation |
| Indicators | Pandas TA | MIT | Technical analysis |
| Database | InfluxDB 3 | MIT | Time-series data |
| Cache | Redis | BSD | Session state |
| API | FastAPI | MIT | REST/WebSocket |
| Dashboard | Dash/Plotly | MIT | Visualization |
| ML | scikit-learn | BSD | Signal filtering |
| Stats | scipy | BSD | A/B testing |

---

## Conclusion

This Strategy Plan provides a complete roadmap from research to production deployment. The phased approach minimizes risk while maximizing learning velocity.

**Key Decisions:**
1. **Start with single strategy** - Mean Reversion with VaR filter
2. **Build incrementally** - Add strategies only after proven success
3. **A/B test continuously** - Optimize parameters systematically
4. **Risk-first approach** - Position sizing and limits before profits

**Next Steps:**
1. Begin Phase 1 implementation
2. Set up development environment
3. Implement Mean Reversion strategy
4. Start backtesting process

**Critical Success Factor:**
Do not proceed to Phase 2 until Phase 1 success criteria are met. Building on unstable foundations increases catastrophic failure risk.

---

*End of Strategy Plan*
*Ready for Implementation Phase*
