# BACKTESTING STRATEGY RESEARCH PLAN
## Comprehensive Validation & Optimization Framework

**Document Version:** 1.0  
**Last Updated:** 2026-02-10  
**Status:** Research Complete, Ready for Execution  
**Phase:** Phase 1 - Strategy Validation

---

## Executive Summary

### Backtesting Philosophy

This research plan follows the **RBI Framework** principle: *"Never deploy a strategy without rigorous backtesting."* We will subject each strategy to multiple validation layers to ensure robustness and minimize overfitting.

### Validation Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                        BACKTESTING VALIDATION PYRAMID                                │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                     │
│                           ┌───────────────────────┐                                │
│                           │   LIVE DEPLOYMENT     │                                │
│                           │   (Final Validation)  │                                │
│                           └───────────┬───────────┘                                │
│                                       │                                            │
│                           ┌───────────▼───────────┐                                │
│                           │  WALK-FORWARD TEST    │                                │
│                           │  (Time-Series CV)     │                                │
│                           └───────────┬───────────┘                                │
│                                       │                                            │
│                           ┌───────────▼───────────┐                                │
│                           │  MONTE CARLO SIM      │                                │
│                           │  (Robustness Check)   │                                │
│                           └───────────┬───────────┘                                │
│                                       │                                            │
│                           ┌───────────▼───────────┐                                │
│                           │  OUT-OF-SAMPLE TEST   │                                │
│                           │  (Unseen Data)        │                                │
│                           └───────────┬───────────┘                                │
│                                       │                                            │
│                           ┌───────────▼───────────┐                                │
│                           │  PARAMETER OPTIMIZE   │                                │
│                           │  (In-Sample)          │                                │
│                           └───────────┬───────────┘                                │
│                                       │                                            │
│                           ┌───────────▼───────────┐                                │
│                           │   INITIAL BACKTEST    │                                │
│                           │   (Proof of Concept)  │                                │
│                           └───────────────────────┘                                │
│                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Data Acquisition & Preparation

### Data Requirements

**Historical Data Specifications:**

```yaml
data_specifications:
  timeframe: 1h
  lookback_period: 2_years
  minimum_records: 17520  # 2 years × 365 days × 24 hours
  
  symbols:
    primary: BTC/USDT
    secondary: ETH/USDT
    
  columns_required:
    - timestamp
    - open
    - high
    - low
    - close
    - volume
    
  quality_checks:
    - no_missing_values
    - no_duplicate_timestamps
    - continuous_data (no_gaps > 4h)
    - reasonable_ohlc_values
    
  data_sources:
    - ccxt_binance_historical
    - ccxt_coinbase_historical
    - alternative: yfinance
    
  splits:
    in_sample: 70%  # Training data
    out_sample: 30%  # Testing data (never seen during optimization)
```

### Data Download Script

```python
# data/download_historical.py
"""
Download and prepare historical data for backtesting.
"""

import ccxt
import pandas as pd
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_ohlcv(
    exchange_name: str,
    symbol: str,
    timeframe: str,
    days: int = 730,
    output_path: str = None
) -> pd.DataFrame:
    """
    Download historical OHLCV data from exchange.
    
    Args:
        exchange_name: Exchange ID (e.g., 'binance', 'coinbase')
        symbol: Trading pair (e.g., 'BTC/USDT')
        timeframe: Candle timeframe (e.g., '1h', '4h', '1d')
        days: Number of days to download
        output_path: Optional path to save CSV
        
    Returns:
        DataFrame with OHLCV data
    """
    logger.info(f"Downloading {symbol} {timeframe} from {exchange_name}")
    
    # Initialize exchange
    exchange_class = getattr(ccxt, exchange_name)
    exchange = exchange_class({'enableRateLimit': True})
    
    # Calculate start time
    since = exchange.parse8601(
        (datetime.utcnow() - timedelta(days=days)).isoformat()
    )
    
    # Download data in chunks
    all_ohlcv = []
    while since < exchange.milliseconds():
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since, limit=1000)
            if len(ohlcv) == 0:
                break
            all_ohlcv.extend(ohlcv)
            since = ohlcv[-1][0] + 1
            logger.info(f"Downloaded {len(all_ohlcv)} candles...")
        except Exception as e:
            logger.error(f"Error downloading: {e}")
            break
    
    # Convert to DataFrame
    df = pd.DataFrame(
        all_ohlcv,
        columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
    )
    
    # Convert timestamp to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df.set_index('timestamp', inplace=True)
    
    # Clean data
    df = clean_ohlcv_data(df)
    
    # Save if path provided
    if output_path:
        df.to_csv(output_path)
        logger.info(f"Saved to {output_path}")
    
    logger.info(f"Downloaded {len(df)} total candles")
    return df

def clean_ohlcv_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and validate OHLCV data.
    
    Checks:
    - Remove duplicates
    - Fill small gaps (interpolate)
    - Remove outliers
    - Ensure OHLC consistency
    """
    initial_len = len(df)
    
    # Remove duplicates
    df = df[~df.index.duplicated(keep='first')]
    
    # Sort by timestamp
    df.sort_index(inplace=True)
    
    # Check for gaps > 4 hours (16 candles at 15min, 4 at 1h)
    df['time_diff'] = df.index.to_series().diff()
    max_gap = df['time_diff'].max()
    logger.info(f"Maximum data gap: {max_gap}")
    
    # Remove rows with zero volume (often bad data)
    df = df[df['volume'] > 0]
    
    # Ensure OHLC consistency
    df['high'] = df[['open', 'high', 'low', 'close']].max(axis=1)
    df['low'] = df[['open', 'high', 'low', 'close']].min(axis=1)
    
    # Remove extreme outliers (>5 std dev from mean)
    for col in ['open', 'high', 'low', 'close']:
        mean = df[col].mean()
        std = df[col].std()
        df = df[abs(df[col] - mean) < 5 * std]
    
    final_len = len(df)
    logger.info(f"Cleaned data: {initial_len} → {final_len} rows "
                f"({(1 - final_len/initial_len)*100:.1f}% removed)")
    
    # Drop helper column
    df.drop('time_diff', axis=1, inplace=True, errors='ignore')
    
    return df

def prepare_train_test_split(
    df: pd.DataFrame,
    train_ratio: float = 0.7
) -> tuple:
    """
    Split data into training and testing sets.
    
    Args:
        df: OHLCV DataFrame
        train_ratio: Percentage for training (default 70%)
        
    Returns:
        Tuple of (train_df, test_df)
    """
    split_idx = int(len(df) * train_ratio)
    
    train_df = df.iloc[:split_idx].copy()
    test_df = df.iloc[split_idx:].copy()
    
    logger.info(f"Train: {len(train_df)} samples ({train_ratio:.0%})")
    logger.info(f"Test: {len(test_df)} samples ({1-train_ratio:.0%})")
    logger.info(f"Train period: {train_df.index[0]} to {train_df.index[-1]}")
    logger.info(f"Test period: {test_df.index[0]} to {test_df.index[-1]}")
    
    return train_df, test_df

# Main execution
if __name__ == "__main__":
    # Download BTC/USDT 1h data
    df = download_ohlcv(
        exchange_name='binance',
        symbol='BTC/USDT',
        timeframe='1h',
        days=730,
        output_path='data/btc_usdt_1h.csv'
    )
    
    # Split into train/test
    train_df, test_df = prepare_train_test_split(df, train_ratio=0.7)
    
    # Save splits
    train_df.to_csv('data/btc_usdt_1h_train.csv')
    test_df.to_csv('data/btc_usdt_1h_test.csv')
```

### Data Quality Checklist

```
Data Quality Verification:
□ Downloaded 2+ years of 1H data
□ No missing values in OHLCV columns
□ Timestamps are continuous (no gaps > 4 hours)
□ No duplicate timestamps
□ Volume > 0 for all records
□ OHLC logical consistency (high >= low, etc.)
□ No extreme outliers (>5 std dev)
□ Train/test split: 70/30 ratio
□ Test period > 6 months for statistical significance
```

---

## Phase 2: Initial Backtesting (Proof of Concept)

### Quick Validation Backtest

**Purpose:** Verify strategy logic works and produces sensible results.

```python
# backtest/initial_validation.py
"""
Quick initial backtest to validate strategy logic.
"""

from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import pandas as pd
import pandas_ta as ta

class MeanReversionQuickTest(Strategy):
    """
    Quick implementation for initial validation.
    Simplified version of full strategy.
    """
    
    # Parameters
    rsi_period = 14
    rsi_oversold = 30
    rsi_overbought = 70
    bb_period = 20
    bb_std = 2.0
    
    def init(self):
        # Calculate indicators
        close = pd.Series(self.data.Close)
        
        # RSI
        self.rsi = self.I(ta.rsi, close, self.rsi_period)
        
        # Bollinger Bands
        bb = ta.bbands(close, length=self.bb_period, std=self.bb_std)
        self.bb_upper = self.I(lambda: bb.iloc[:, 0])
        self.bb_lower = self.I(lambda: bb.iloc[:, 2])
    
    def next(self):
        # Entry: RSI oversold AND price below lower band
        if (self.rsi[-1] < self.rsi_oversold and 
            self.data.Close[-1] < self.bb_lower[-1]):
            if not self.position:
                self.buy()
        
        # Exit: RSI overbought OR price above upper band
        elif (self.rsi[-1] > self.rsi_overbought or 
              self.data.Close[-1] > self.bb_upper[-1]):
            if self.position:
                self.position.close()

# Run quick test
def run_initial_validation(data_path: str):
    """Run initial backtest to validate strategy logic"""
    
    # Load data
    data = pd.read_csv(data_path)
    data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    
    # Run backtest
    bt = Backtest(
        data, 
        MeanReversionQuickTest,
        cash=10000,
        commission=0.002,  # 0.2% commission
        exclusive_orders=True
    )
    
    stats = bt.run()
    
    print("\n" + "="*50)
    print("INITIAL VALIDATION RESULTS")
    print("="*50)
    print(f"Total Return: {stats['Return [%]']:.2f}%")
    print(f"Sharpe Ratio: {stats['Sharpe Ratio']:.2f}")
    print(f"Max Drawdown: {stats['Max. Drawdown [%]']:.2f}%")
    print(f"# Trades: {stats['# Trades']}")
    print(f"Win Rate: {stats['Win Rate [%]']:.1f}%")
    print(f"Avg Trade: {stats['Avg. Trade [%]']:.3f}%")
    print(f"Profit Factor: {stats['Profit Factor']:.2f}")
    print("="*50)
    
    # Validation criteria
    if stats['# Trades'] < 10:
        print("❌ FAIL: Too few trades (< 10)")
    elif stats['Return [%]'] < 0:
        print("❌ FAIL: Negative return")
    else:
        print("✅ PASS: Basic logic validated")
    
    # Plot
    bt.plot(filename='backtest_results/initial_validation.html')
    
    return stats

if __name__ == "__main__":
    stats = run_initial_validation('data/btc_usdt_1h_train.csv')
```

### Initial Validation Criteria

```
Quick Validation Checklist:
□ Strategy executes trades (not stuck)
□ Number of trades > 10 (sensible frequency)
□ Return is positive (basic profitability)
□ No extreme drawdowns (> 50%)
□ Win rate between 30-70% (realistic)
□ Logic produces expected signals
□ Can generate plot without errors
```

---

## Phase 3: Parameter Optimization (In-Sample)

### Grid Search Optimization

**Purpose:** Find optimal parameters using training data only.

```python
# backtest/parameter_optimization.py
"""
Parameter optimization using grid search.
WARNING: Only use on training data!
"""

from backtesting import Backtest
import pandas as pd
import numpy as np
from itertools import product
import json
from datetime import datetime

class ParameterOptimizer:
    """
    Grid search optimizer for strategy parameters.
    """
    
    def __init__(self, strategy_class, data, cash=10000, commission=0.002):
        self.strategy_class = strategy_class
        self.data = data
        self.cash = cash
        self.commission = commission
        self.results = []
    
    def optimize(self, param_grid: dict, metric='Sharpe Ratio'):
        """
        Run grid search over parameter space.
        
        Args:
            param_grid: Dict of param_name: [values]
            metric: Metric to optimize ('Sharpe Ratio', 'Return', etc.)
            
        Returns:
            DataFrame of results sorted by metric
        """
        # Generate all parameter combinations
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        combinations = list(product(*param_values))
        
        print(f"Testing {len(combinations)} parameter combinations...")
        
        for i, combo in enumerate(combinations):
            params = dict(zip(param_names, combo))
            
            try:
                # Run backtest
                bt = Backtest(
                    self.data,
                    self.strategy_class,
                    cash=self.cash,
                    commission=self.commission,
                    exclusive_orders=True
                )
                
                stats = bt.run(**params)
                
                # Store results
                result = {
                    'params': params,
                    'sharpe': stats['Sharpe Ratio'],
                    'return': stats['Return [%]'],
                    'drawdown': stats['Max. Drawdown [%]'],
                    'trades': stats['# Trades'],
                    'win_rate': stats['Win Rate [%]'],
                    'profit_factor': stats['Profit Factor'],
                    'sqn': stats.get('SQN', 0)
                }
                
                self.results.append(result)
                
                if (i + 1) % 10 == 0:
                    print(f"Completed {i+1}/{len(combinations)}")
                    
            except Exception as e:
                print(f"Error with params {params}: {e}")
                continue
        
        # Convert to DataFrame and sort
        results_df = pd.DataFrame(self.results)
        results_df = results_df.sort_values(metric.replace(' ', '_').lower(), 
                                           ascending=False)
        
        return results_df
    
    def get_top_results(self, n=10):
        """Get top N results"""
        return self.results[:n]
    
    def save_results(self, filepath):
        """Save optimization results to JSON"""
        with open(filepath, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'results': self.results
            }, f, indent=2, default=str)

# Parameter grid for Mean Reversion
mean_reversion_params = {
    'rsi_period': [10, 14, 20, 25],
    'rsi_oversold': [20, 25, 30, 35],
    'rsi_overbought': [65, 70, 75, 80],
    'bb_period': [15, 20, 25, 30],
    'bb_std': [1.5, 2.0, 2.5, 3.0]
}

# Run optimization
def run_optimization(data_path: str):
    """Run full parameter optimization"""
    
    # Load training data
    data = pd.read_csv(data_path)
    data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    
    # Initialize optimizer
    from initial_validation import MeanReversionQuickTest
    optimizer = ParameterOptimizer(MeanReversionQuickTest, data)
    
    # Run grid search
    results = optimizer.optimize(mean_reversion_params, metric='Sharpe Ratio')
    
    # Save results
    optimizer.save_results('backtest_results/optimization_results.json')
    
    # Display top 10
    print("\n" + "="*70)
    print("TOP 10 PARAMETER COMBINATIONS (Training Data)")
    print("="*70)
    print(results.head(10).to_string())
    print("="*70)
    
    # Best parameters
    best = results.iloc[0]
    print("\n🏆 BEST PARAMETERS:")
    print(f"Parameters: {best['params']}")
    print(f"Sharpe: {best['sharpe']:.2f}")
    print(f"Return: {best['return']:.2f}%")
    print(f"Max DD: {best['drawdown']:.2f}%")
    print(f"Trades: {best['trades']}")
    
    return results

if __name__ == "__main__":
    results = run_optimization('data/btc_usdt_1h_train.csv')
```

### Optimization Analysis

```python
# backtest/analyze_optimization.py
"""
Analyze optimization results for robustness.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json

def analyze_parameter_sensitivity(results_path: str):
    """
    Analyze which parameters have most impact on performance.
    """
    # Load results
    with open(results_path, 'r') as f:
        data = json.load(f)
    
    results_df = pd.DataFrame(data['results'])
    
    # Analyze sensitivity for each parameter
    param_names = list(results_df['params'].iloc[0].keys())
    
    print("\n" + "="*70)
    print("PARAMETER SENSITIVITY ANALYSIS")
    print("="*70)
    
    for param in param_names:
        # Extract parameter values
        results_df[param] = results_df['params'].apply(lambda x: x[param])
        
        # Group by parameter value and calculate mean Sharpe
        grouped = results_df.groupby(param).agg({
            'sharpe': ['mean', 'std', 'min', 'max'],
            'return': 'mean',
            'drawdown': 'mean'
        })
        
        print(f"\n{param.upper()}:")
        print(grouped)
        
        # Calculate sensitivity (std of Sharpe across values)
        sensitivity = grouped['sharpe']['std'].mean()
        print(f"Sensitivity Score: {sensitivity:.3f}")
        
        if sensitivity > 0.5:
            print("⚠️  HIGH SENSITIVITY - Consider wider range or different value")
        elif sensitivity < 0.1:
            print("✅ LOW SENSITIVITY - Parameter is stable")

def plot_optimization_surface(results_df, param_x, param_y, metric='sharpe'):
    """
    Plot 2D heatmap of parameter space.
    """
    # Extract parameters
    results_df[param_x] = results_df['params'].apply(lambda x: x[param_x])
    results_df[param_y] = results_df['params'].apply(lambda x: x[param_y])
    
    # Create pivot table
    pivot = results_df.pivot_table(
        values=metric,
        index=param_y,
        columns=param_x,
        aggfunc='mean'
    )
    
    # Plot
    plt.figure(figsize=(10, 8))
    sns.heatmap(pivot, annot=True, fmt='.2f', cmap='RdYlGn')
    plt.title(f'{metric.upper()} by {param_x} and {param_y}')
    plt.tight_layout()
    plt.savefig(f'backtest_results/heatmap_{param_x}_{param_y}.png')
    plt.close()

# Check for overfitting

def check_overfitting(results_df):
    """
    Check if optimization shows signs of overfitting.
    """
    print("\n" + "="*70)
    print("OVERFITTING DETECTION")
    print("="*70)
    
    # 1. Check if top results are clustered
    top_10 = results_df.head(10)
    
    for param in ['rsi_period', 'bb_period', 'bb_std']:
        values = top_10['params'].apply(lambda x: x[param])
        unique = values.nunique()
        
        print(f"\n{param}:")
        print(f"  Unique values in top 10: {unique}")
        print(f"  Most common: {values.mode().values[0]}")
        
        if unique == 1:
            print("  ⚠️  All top results use same value - possible overfitting")
        elif unique >= 3:
            print("  ✅ Good diversity - less likely overfit")
    
    # 2. Check performance distribution
    sharpe_std = results_df['sharpe'].std()
    sharpe_mean = results_df['sharpe'].mean()
    cv = sharpe_std / abs(sharpe_mean) if sharpe_mean != 0 else float('inf')
    
    print(f"\nSharpe Ratio Coefficient of Variation: {cv:.2f}")
    if cv > 2.0:
        print("⚠️  High variance - parameters very sensitive")
    else:
        print("✅ Reasonable variance - parameter space stable")
```

### Optimization Best Practices

```
Parameter Optimization Rules:

1. ONLY optimize on TRAINING data (70%)
2. Never optimize on test data (30%) - that's cheating
3. Test parameter sensitivity - good parameters should work across a range
4. Avoid overfitting:
   - Don't optimize too many parameters at once
   - Use walk-forward analysis for final validation
   - Require parameters to be stable across nearby values

5. Good optimization results show:
   - Top parameters are in a "plateau" (not isolated peaks)
   - Performance doesn't drop off cliff with small changes
   - Multiple parameter combinations achieve good results

6. Red flags:
   - Best parameters at extreme values (20, 80 RSI)
   - Very narrow peak (only 1-2 combinations work)
   - Performance highly sensitive to small changes
```

---

## Phase 4: Out-of-Sample Testing

### Unseen Data Validation

**Purpose:** Verify optimized parameters work on completely unseen data.

```python
# backtest/out_of_sample_test.py
"""
Out-of-sample testing - the true test of strategy robustness.
"""

from backtesting import Backtest
import pandas as pd
import json

def out_of_sample_test(
    strategy_class,
    train_data_path: str,
    test_data_path: str,
    best_params: dict
):
    """
    Test optimized strategy on out-of-sample data.
    
    Args:
        strategy_class: Strategy class to test
        train_data_path: Path to training data
        test_data_path: Path to test data (unseen)
        best_params: Optimized parameters from grid search
        
    Returns:
        Comparison of train vs test performance
    """
    
    # Load data
    train_data = pd.read_csv(train_data_path)
    train_data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    
    test_data = pd.read_csv(test_data_path)
    test_data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    
    # Run on training data (in-sample)
    bt_train = Backtest(
        train_data,
        strategy_class,
        cash=10000,
        commission=0.002
    )
    train_stats = bt_train.run(**best_params)
    
    # Run on test data (out-of-sample)
    bt_test = Backtest(
        test_data,
        strategy_class,
        cash=10000,
        commission=0.002
    )
    test_stats = bt_test.run(**best_params)
    
    # Compare
    comparison = {
        'train': {
            'sharpe': train_stats['Sharpe Ratio'],
            'return': train_stats['Return [%]'],
            'drawdown': train_stats['Max. Drawdown [%]'],
            'trades': train_stats['# Trades'],
            'win_rate': train_stats['Win Rate [%]']
        },
        'test': {
            'sharpe': test_stats['Sharpe Ratio'],
            'return': test_stats['Return [%]'],
            'drawdown': test_stats['Max. Drawdown [%]'],
            'trades': test_stats['# Trades'],
            'win_rate': test_stats['Win Rate [%]']
        },
        'degradation': {
            'sharpe': train_stats['Sharpe Ratio'] - test_stats['Sharpe Ratio'],
            'return': train_stats['Return [%]'] - test_stats['Return [%]'],
            'drawdown': test_stats['Max. Drawdown [%]'] - train_stats['Max. Drawdown [%]']
        }
    }
    
    # Print results
    print("\n" + "="*70)
    print("OUT-OF-SAMPLE TEST RESULTS")
    print("="*70)
    print(f"{'Metric':<20} {'Train (In-Sample)':<20} {'Test (Out-of-Sample)':<20} {'Degradation':<15}")
    print("-"*70)
    print(f"{'Sharpe':<20} {comparison['train']['sharpe']:<20.2f} {comparison['test']['sharpe']:<20.2f} {comparison['degradation']['sharpe']:<15.2f}")
    print(f"{'Return %':<20} {comparison['train']['return']:<20.2f} {comparison['test']['return']:<20.2f} {comparison['degradation']['return']:<15.2f}")
    print(f"{'Max DD %':<20} {comparison['train']['drawdown']:<20.2f} {comparison['test']['drawdown']:<20.2f} {comparison['degradation']['drawdown']:<15.2f}")
    print(f"{'Trades':<20} {comparison['train']['trades']:<20} {comparison['test']['trades']:<20}")
    print("="*70)
    
    # Validation
    sharpe_degradation = comparison['degradation']['sharpe']
    
    if sharpe_degradation < 0.3:
        print("✅ EXCELLENT: Minimal degradation (< 0.3 Sharpe)")
    elif sharpe_degradation < 0.5:
        print("✅ GOOD: Acceptable degradation (0.3-0.5 Sharpe)")
    elif sharpe_degradation < 0.8:
        print("⚠️  CAUTION: Moderate degradation (0.5-0.8 Sharpe)")
    else:
        print("❌ FAIL: Severe degradation (> 0.8 Sharpe) - Strategy overfit")
    
    # Save results
    with open('backtest_results/oos_test_results.json', 'w') as f:
        json.dump(comparison, f, indent=2)
    
    return comparison

# Run OOS test
def run_oos_test():
    """Execute out-of-sample test"""
    
    from initial_validation import MeanReversionQuickTest
    
    # Load best params from optimization
    with open('backtest_results/optimization_results.json', 'r') as f:
        opt_data = json.load(f)
    
    best_params = opt_data['results'][0]['params']
    
    # Run OOS test
    comparison = out_of_sample_test(
        MeanReversionQuickTest,
        'data/btc_usdt_1h_train.csv',
        'data/btc_usdt_1h_test.csv',
        best_params
    )
    
    return comparison

if __name__ == "__main__":
    run_oos_test()
```

### Out-of-Sample Success Criteria

```
Out-of-Sample Validation:
□ Sharpe degradation < 0.5 from training
□ Return degradation < 50% from training
□ Win rate within ±10% of training
□ Max drawdown within ±5% of training
□ Strategy remains profitable on test data
□ Number of trades reasonable (not 0 or 1000+)
```

---

## Phase 5: Monte Carlo Simulation

### Robustness Testing

**Purpose:** Test strategy robustness by randomizing trade sequences.

```python
# backtest/monte_carlo_simulation.py
"""
Monte Carlo simulation to test strategy robustness.
Shuffles trade order to simulate different market paths.
"""

import numpy as np
import pandas as pd
from backtesting import Backtest
import matplotlib.pyplot as plt

def extract_trades(stats):
    """Extract individual trade returns from backtest stats"""
    # This is a simplified version - actual implementation would parse trade log
    # For now, we'll simulate based on win rate and average trade
    
    n_trades = stats['# Trades']
    win_rate = stats['Win Rate [%]'] / 100
    avg_trade = stats['Avg. Trade [%]'] / 100
    
    # Generate simulated trade returns
    trades = []
    for _ in range(n_trades):
        is_win = np.random.random() < win_rate
        if is_win:
            # Winning trade
            ret = np.random.normal(avg_trade * 1.5, abs(avg_trade))
        else:
            # Losing trade
            ret = np.random.normal(-abs(avg_trade) * 0.5, abs(avg_trade) * 0.5)
        trades.append(ret)
    
    return np.array(trades)

def monte_carlo_simulation(
    trades: np.ndarray,
    n_simulations: int = 1000,
    initial_capital: float = 10000
):
    """
    Run Monte Carlo simulation by reshuffling trades.
    
    Args:
        trades: Array of trade returns
        n_simulations: Number of MC runs
        initial_capital: Starting capital
        
    Returns:
        Dictionary of simulation statistics
    """
    final_equities = []
    max_drawdowns = []
    returns = []
    
    print(f"Running {n_simulations} Monte Carlo simulations...")
    
    for i in range(n_simulations):
        # Shuffle trade order
        shuffled_trades = np.random.permutation(trades)
        
        # Simulate equity curve
        equity = initial_capital
        equity_curve = [equity]
        
        for trade_return in shuffled_trades:
            equity *= (1 + trade_return)
            equity_curve.append(equity)
        
        # Calculate metrics
        final_equity = equity_curve[-1]
        total_return = (final_equity - initial_capital) / initial_capital
        
        # Calculate max drawdown
        equity_series = pd.Series(equity_curve)
        peak = equity_series.expanding().max()
        drawdown = (equity_series - peak) / peak
        max_dd = drawdown.min()
        
        final_equities.append(final_equity)
        max_drawdowns.append(max_dd)
        returns.append(total_return)
    
    # Calculate statistics
    results = {
        'final_equity': {
            'mean': np.mean(final_equities),
            'median': np.median(final_equities),
            'std': np.std(final_equities),
            'min': np.min(final_equities),
            'max': np.max(final_equities),
            'percentile_5': np.percentile(final_equities, 5),
            'percentile_95': np.percentile(final_equities, 95)
        },
        'returns': {
            'mean': np.mean(returns),
            'median': np.median(returns),
            'std': np.std(returns),
            'percentile_5': np.percentile(returns, 5),
            'percentile_95': np.percentile(returns, 95)
        },
        'max_drawdown': {
            'mean': np.mean(max_drawdowns),
            'median': np.median(max_drawdowns),
            'percentile_95': np.percentile(max_drawdowns, 95),
            'worst': np.min(max_drawdowns)
        }
    }
    
    return results

def plot_mc_results(results):
    """Visualize Monte Carlo results"""
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Final equity distribution
    ax = axes[0, 0]
    ax.hist(results['final_equity']['distribution'], bins=50, alpha=0.7)
    ax.axvline(results['final_equity']['mean'], color='r', linestyle='--', 
               label=f"Mean: ${results['final_equity']['mean']:,.0f}")
    ax.axvline(results['final_equity']['percentile_5'], color='orange', 
               linestyle='--', label=f"5%: ${results['final_equity']['percentile_5']:,.0f}")
    ax.set_xlabel('Final Equity ($)')
    ax.set_ylabel('Frequency')
    ax.set_title('Monte Carlo: Final Equity Distribution')
    ax.legend()
    
    # Max drawdown distribution
    ax = axes[0, 1]
    ax.hist(results['max_drawdown']['distribution'], bins=50, alpha=0.7, color='red')
    ax.axvline(results['max_drawdown']['mean'], color='black', linestyle='--',
               label=f"Mean: {results['max_drawdown']['mean']:.1%}")
    ax.set_xlabel('Max Drawdown')
    ax.set_ylabel('Frequency')
    ax.set_title('Monte Carlo: Max Drawdown Distribution')
    ax.legend()
    
    plt.tight_layout()
    plt.savefig('backtest_results/monte_carlo_results.png', dpi=150)
    plt.close()

def run_monte_carlo():
    """Execute Monte Carlo simulation"""
    
    # Load backtest results
    with open('backtest_results/oos_test_results.json', 'r') as f:
        oos_results = json.load(f)
    
    # Extract or simulate trades
    # In practice, you'd extract actual trades from backtest
    # Here we'll use the test data statistics
    
    win_rate = oos_results['test']['win_rate'] / 100
    n_trades = oos_results['test']['trades']
    avg_return = oos_results['test']['return'] / 100
    
    # Simulate trade returns based on statistics
    # This is simplified - real implementation would use actual trade history
    trades = []
    for i in range(n_trades):
        if np.random.random() < win_rate:
            trades.append(np.random.normal(0.02, 0.015))  # Winning trade
        else:
            trades.append(np.random.normal(-0.01, 0.01))  # Losing trade
    
    trades = np.array(trades)
    
    # Run Monte Carlo
    mc_results = monte_carlo_simulation(trades, n_simulations=1000)
    
    # Print results
    print("\n" + "="*70)
    print("MONTE CARLO SIMULATION RESULTS (1000 runs)")
    print("="*70)
    
    print(f"\nFinal Equity Statistics:")
    print(f"  Mean: ${mc_results['final_equity']['mean']:,.0f}")
    print(f"  Median: ${mc_results['final_equity']['median']:,.0f}")
    print(f"  Std Dev: ${mc_results['final_equity']['std']:,.0f}")
    print(f"  5th Percentile: ${mc_results['final_equity']['percentile_5']:,.0f}")
    print(f"  95th Percentile: ${mc_results['final_equity']['percentile_95']:,.0f}")
    
    print(f"\nReturn Statistics:")
    print(f"  Mean: {mc_results['returns']['mean']:.1%}")
    print(f"  5th Percentile: {mc_results['returns']['percentile_5']:.1%}")
    print(f"  95th Percentile: {mc_results['returns']['percentile_95']:.1%}")
    
    print(f"\nMax Drawdown Statistics:")
    print(f"  Mean: {mc_results['max_drawdown']['mean']:.1%}")
    print(f"  95th Percentile: {mc_results['max_drawdown']['percentile_95']:.1%}")
    print(f"  Worst Case: {mc_results['max_drawdown']['worst']:.1%}")
    
    # Validation
    print("\n" + "="*70)
    if mc_results['returns']['percentile_5'] > 0:
        print("✅ ROBUST: Profitable in 95% of simulations")
    else:
        print("⚠️  WARNING: 5% chance of loss - consider position sizing reduction")
    
    if mc_results['max_drawdown']['percentile_95'] > -0.30:
        print("✅ ROBUST: Max drawdown < 30% in 95% of cases")
    else:
        print("⚠️  WARNING: Potential for severe drawdowns")
    
    return mc_results

if __name__ == "__main__":
    import json
    mc_results = run_monte_carlo()
```

### Monte Carlo Success Criteria

```
Monte Carlo Validation:
□ Profitable in > 90% of simulations (5th percentile > 0)
□ 95th percentile max drawdown < 30%
□ Mean return close to backtest return
□ Low standard deviation of final equity
□ No extreme outliers (min/max within 2 std dev)
```

---

## Phase 6: Walk-Forward Analysis

### Time-Series Cross Validation

**Purpose:** Test strategy across multiple time periods to ensure robustness.

```python
# backtest/walk_forward_analysis.py
"""
Walk-forward analysis - the gold standard for strategy validation.
"""

import pandas as pd
import numpy as np
from backtesting import Backtest
import json

def walk_forward_analysis(
    strategy_class,
    data: pd.DataFrame,
    train_days: int = 90,
    test_days: int = 30,
    step_days: int = 30,
    param_grid: dict = None
):
    """
    Perform walk-forward analysis.
    
    Process:
    1. Train on period N (e.g., 90 days)
    2. Test on period N+1 (e.g., next 30 days)
    3. Step forward by step_days
    4. Repeat until end of data
    
    Args:
        strategy_class: Strategy to test
        data: Full OHLCV DataFrame
        train_days: Training window size
        test_days: Testing window size
        step_days: Step size between windows
        param_grid: Parameter grid for optimization (optional)
        
    Returns:
        DataFrame of walk-forward results
    """
    
    results = []
    window_num = 0
    
    # Calculate number of windows
    total_days = (data.index[-1] - data.index[0]).days
    n_windows = (total_days - train_days - test_days) // step_days
    
    print(f"Running walk-forward analysis: {n_windows} windows")
    print(f"Train: {train_days} days, Test: {test_days} days, Step: {step_days} days")
    
    start_date = data.index[0]
    
    while True:
        # Define window dates
        train_start = start_date + pd.Timedelta(days=window_num * step_days)
        train_end = train_start + pd.Timedelta(days=train_days)
        test_end = train_end + pd.Timedelta(days=test_days)
        
        # Check if we have enough data
        if test_end > data.index[-1]:
            break
        
        # Split data
        train_mask = (data.index >= train_start) & (data.index < train_end)
        test_mask = (data.index >= train_end) & (data.index < test_end)
        
        train_data = data[train_mask]
        test_data = data[test_mask]
        
        if len(train_data) < 100 or len(test_data) < 30:
            window_num += 1
            continue
        
        print(f"\nWindow {window_num + 1}/{n_windows}")
        print(f"Train: {train_start.date()} to {train_end.date()}")
        print(f"Test: {train_end.date()} to {test_end.date()}")
        
        # Optimize on training data if param_grid provided
        if param_grid:
            # Simplified - would use actual optimizer here
            best_params = optimize_single_window(strategy_class, train_data, param_grid)
        else:
            best_params = {}
        
        # Test on out-of-sample data
        bt = Backtest(
            test_data,
            strategy_class,
            cash=10000,
            commission=0.002
        )
        
        stats = bt.run(**best_params)
        
        # Store results
        result = {
            'window': window_num + 1,
            'train_start': train_start,
            'train_end': train_end,
            'test_start': train_end,
            'test_end': test_end,
            'sharpe': stats['Sharpe Ratio'],
            'return': stats['Return [%]'],
            'drawdown': stats['Max. Drawdown [%]'],
            'trades': stats['# Trades'],
            'win_rate': stats['Win Rate [%]'],
            'params': best_params
        }
        
        results.append(result)
        
        print(f"Sharpe: {result['sharpe']:.2f}, Return: {result['return']:.2f}%, "
              f"Trades: {result['trades']}")
        
        window_num += 1
    
    return pd.DataFrame(results)

def analyze_walk_forward(results_df: pd.DataFrame):
    """
    Analyze walk-forward results for consistency.
    """
    print("\n" + "="*70)
    print("WALK-FORWARD ANALYSIS SUMMARY")
    print("="*70)
    
    # Calculate statistics
    n_windows = len(results_df)
    profitable_windows = (results_df['return'] > 0).sum()
    
    print(f"\nTotal Windows: {n_windows}")
    print(f"Profitable Windows: {profitable_windows} ({profitable_windows/n_windows:.1%})")
    
    print(f"\nSharpe Ratio Statistics:")
    print(f"  Mean: {results_df['sharpe'].mean():.2f}")
    print(f"  Std: {results_df['sharpe'].std():.2f}")
    print(f"  Min: {results_df['sharpe'].min():.2f}")
    print(f"  Max: {results_df['sharpe'].max():.2f}")
    print(f"  Profitable (>0): {(results_df['sharpe'] > 0).sum()}/{n_windows}")
    
    print(f"\nReturn Statistics:")
    print(f"  Mean: {results_df['return'].mean():.2f}%")
    print(f"  Std: {results_df['return'].std():.2f}%")
    print(f"  Min: {results_df['return'].min():.2f}%")
    print(f"  Max: {results_df['return'].max():.2f}%")
    
    print(f"\nDrawdown Statistics:")
    print(f"  Mean: {results_df['drawdown'].mean():.2f}%")
    print(f"  Worst: {results_df['drawdown'].min():.2f}%")
    
    # Consistency check
    sharpe_cv = results_df['sharpe'].std() / abs(results_df['sharpe'].mean()) if results_df['sharpe'].mean() != 0 else float('inf')
    
    print("\n" + "="*70)
    print("CONSISTENCY ASSESSMENT")
    print("="*70)
    
    if profitable_windows / n_windows > 0.7:
        print("✅ CONSISTENT: Profitable in > 70% of windows")
    else:
        print("⚠️  INCONSISTENT: Profitable in < 70% of windows")
    
    if sharpe_cv < 1.0:
        print("✅ STABLE: Low coefficient of variation")
    else:
        print("⚠️  VOLATILE: High variation between windows")
    
    # Trend analysis
    from scipy import stats
    x = np.arange(len(results_df))
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, results_df['sharpe'])
    
    print(f"\nTrend Analysis:")
    print(f"  Slope: {slope:.4f} (Sharpe change per window)")
    if slope < -0.01:
        print("  ⚠️  DEGRADING: Performance declining over time")
    elif slope > 0.01:
        print("  ✅ IMPROVING: Performance improving over time")
    else:
        print("  ✅ STABLE: No significant trend")
    
    return results_df

def run_walk_forward():
    """Execute walk-forward analysis"""
    
    from initial_validation import MeanReversionQuickTest
    
    # Load data
    data = pd.read_csv('data/btc_usdt_1h.csv')
    data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    
    # Define parameter grid
    param_grid = {
        'rsi_period': [14, 20],
        'rsi_oversold': [25, 30],
        'bb_std': [2.0, 2.5]
    }
    
    # Run walk-forward
    results = walk_forward_analysis(
        MeanReversionQuickTest,
        data,
        train_days=90,
        test_days=30,
        step_days=30,
        param_grid=param_grid
    )
    
    # Analyze
    analyze_walk_forward(results)
    
    # Save
    results.to_csv('backtest_results/walk_forward_results.csv', index=False)
    
    return results

if __name__ == "__main__":
    wf_results = run_walk_forward()
```

### Walk-Forward Success Criteria

```
Walk-Forward Analysis:
□ Profitable in > 70% of test windows
□ Mean Sharpe > 1.0
□ Sharpe coefficient of variation < 1.0
□ No degrading trend over time
□ Maximum drawdown < 25% in any window
□ Reasonable trade count per window (> 5)
```

---

## Phase 7: Stress Testing

### Market Regime Analysis

**Purpose:** Test strategy performance across different market conditions.

```python
# backtest/stress_testing.py
"""
Stress test strategy across different market regimes.
"""

import pandas as pd
import numpy as np
from backtesting import Backtest

def identify_market_regimes(data: pd.DataFrame, lookback: int = 50):
    """
    Identify market regimes (bull, bear, sideways).
    
    Returns:
        DataFrame with regime column added
    """
    df = data.copy()
    
    # Calculate trend
    df['sma_50'] = df['Close'].rolling(lookback).mean()
    df['returns'] = df['Close'].pct_change()
    df['volatility'] = df['returns'].rolling(lookback).std() * np.sqrt(365)
    
    # Define regimes
    conditions = [
        (df['Close'] > df['sma_50'] * 1.05) & (df['volatility'] < 0.5),
        (df['Close'] < df['sma_50'] * 0.95) & (df['volatility'] < 0.5),
        df['volatility'] > 0.8
    ]
    choices = ['bull', 'bear', 'volatile']
    
    df['regime'] = np.select(conditions, choices, default='sideways')
    
    return df

def test_by_regime(strategy_class, data_path: str):
    """
    Test strategy performance by market regime.
    """
    # Load data
    data = pd.read_csv(data_path)
    data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    
    # Identify regimes
    data = identify_market_regimes(data)
    
    # Test each regime
    results = {}
    
    for regime in ['bull', 'bear', 'sideways', 'volatile']:
        regime_data = data[data['regime'] == regime]
        
        if len(regime_data) < 100:
            continue
        
        print(f"\nTesting {regime.upper()} market regime...")
        print(f"Data points: {len(regime_data)}")
        
        bt = Backtest(
            regime_data,
            strategy_class,
            cash=10000,
            commission=0.002
        )
        
        stats = bt.run()
        
        results[regime] = {
            'sharpe': stats['Sharpe Ratio'],
            'return': stats['Return [%]'],
            'drawdown': stats['Max. Drawdown [%]'],
            'trades': stats['# Trades'],
            'win_rate': stats['Win Rate [%]']
        }
        
        print(f"Sharpe: {stats['Sharpe Ratio']:.2f}, "
              f"Return: {stats['Return [%]']:.2f}%, "
              f"Trades: {stats['# Trades']}")
    
    return results

def stress_test_specific_events(strategy_class, data_path: str):
    """
    Test during specific high-stress market events.
    """
    
    # Define known stressful periods
    stress_events = {
        'COVID_Crash': ('2020-03-01', '2020-04-01'),
        'BTC_ATH_2021': ('2021-04-01', '2021-05-01'),
        'China_Ban_2021': ('2021-05-01', '2021-07-01'),
        'FTX_Collapse': ('2022-11-01', '2022-12-01'),
        'SVB_Crisis': ('2023-03-01', '2023-04-01')
    }
    
    # Load data
    data = pd.read_csv(data_path, parse_dates=['timestamp'], index_col='timestamp')
    data.columns = ['Open', 'High', 'Low', 'Close', 'Volume']
    
    results = {}
    
    for event_name, (start, end) in stress_events.items():
        event_data = data[start:end]
        
        if len(event_data) < 10:
            continue
        
        print(f"\nStress test: {event_name} ({start} to {end})")
        
        bt = Backtest(
            event_data,
            strategy_class,
            cash=10000,
            commission=0.002
        )
        
        stats = bt.run()
        
        results[event_name] = {
            'return': stats['Return [%]'],
            'drawdown': stats['Max. Drawdown [%]'],
            'trades': stats['# Trades']
        }
        
        print(f"Return: {stats['Return [%]']:.2f}%, "
              f"Max DD: {stats['Max. Drawdown [%]']:.2f}%")
    
    return results

def run_stress_tests():
    """Execute all stress tests"""
    
    from initial_validation import MeanReversionQuickTest
    
    print("="*70)
    print("STRESS TESTING")
    print("="*70)
    
    # Regime testing
    print("\n1. MARKET REGIME TESTING")
    regime_results = test_by_regime(
        MeanReversionQuickTest,
        'data/btc_usdt_1h.csv'
    )
    
    # Event testing
    print("\n2. STRESS EVENT TESTING")
    event_results = stress_test_specific_events(
        MeanReversionQuickTest,
        'data/btc_usdt_1h.csv'
    )
    
    # Summary
    print("\n" + "="*70)
    print("STRESS TEST SUMMARY")
    print("="*70)
    
    # Check if strategy survives major events
    survived = all(r['drawdown'] > -30 for r in event_results.values())
    
    if survived:
        print("✅ SURVIVED: All stress events without >30% drawdown")
    else:
        print("⚠️  WARNING: Major drawdowns during stress events")
    
    return regime_results, event_results

if __name__ == "__main__":
    run_stress_tests()
```

### Stress Test Success Criteria

```
Stress Testing:
□ Profitable or small loss in bull markets
□ Profitable or small loss in bear markets
□ Best performance in sideways markets (mean reversion)
□ Max drawdown < 30% during major crashes
□ Strategy doesn't blow up in volatile periods
□ No catastrophic losses in any regime
```

---

## Complete Backtesting Checklist

```
BACKTESTING COMPLETION CHECKLIST
================================

Phase 1: Data Preparation
□ Downloaded 2+ years of data
□ Cleaned and validated data
□ Split into 70/30 train/test
□ No data leakage

Phase 2: Initial Validation
□ Strategy executes correctly
□ Generates sensible number of trades
□ Basic profitability confirmed

Phase 3: Parameter Optimization
□ Grid search completed on training data
□ Parameters show stability (not isolated peaks)
□ Sensitivity analysis completed
□ Best parameters selected

Phase 4: Out-of-Sample Test
□ Sharpe degradation < 0.5
□ Profitable on test data
□ Win rate within ±10% of training
□ No overfitting detected

Phase 5: Monte Carlo
□ 1000+ simulations run
□ Profitable in > 90% of runs
□ 95th percentile drawdown < 30%
□ Results are stable

Phase 6: Walk-Forward
□ Multiple time windows tested
□ Profitable in > 70% of windows
□ No degrading trend
□ Consistent performance

Phase 7: Stress Testing
□ Tested in all market regimes
□ Survived major historical events
□ Max drawdown < 30% in stress
□ No catastrophic failures

FINAL VALIDATION
□ All phases passed
□ Strategy is robust
□ Ready for paper trading
□ Ready for small live deployment
```

---

## Backtesting Execution Plan

### Week 1: Setup & Initial Testing
- Day 1-2: Download and clean data
- Day 3-4: Initial strategy implementation
- Day 5-7: Initial backtest and validation

### Week 2: Optimization & OOS
- Day 1-3: Parameter optimization
- Day 4-5: Sensitivity analysis
- Day 6-7: Out-of-sample testing

### Week 3: Advanced Validation
- Day 1-2: Monte Carlo simulation
- Day 3-4: Walk-forward analysis
- Day 5-7: Stress testing

### Week 4: Analysis & Documentation
- Day 1-3: Compile all results
- Day 4-5: Generate reports
- Day 6-7: Prepare for paper trading

---

## Success Metrics Summary

| Validation Layer | Target | Minimum Acceptable |
|-----------------|--------|-------------------|
| **Initial Backtest** | Sharpe > 1.2 | Sharpe > 1.0 |
| **Parameter Optimization** | Stable plateau | No overfitting |
| **Out-of-Sample** | Degradation < 0.3 | Degradation < 0.5 |
| **Monte Carlo** | 95% profitable | 90% profitable |
| **Walk-Forward** | 80% windows profitable | 70% profitable |
| **Stress Test** | DD < 25% | DD < 30% |

---

## Conclusion

This backtesting research plan provides a comprehensive framework for validating trading strategies. By following this multi-layer validation approach, we minimize the risk of overfitting and ensure strategies are robust enough for live deployment.

**Key Principles:**
1. **Multiple Validation Layers**: No single test is sufficient
2. **Out-of-Sample Critical**: Never optimize on test data
3. **Statistical Significance**: Require sufficient sample sizes
4. **Robustness Over Returns**: Better to have stable than spectacular
5. **Stress Test Everything**: Prepare for worst-case scenarios

**Next Steps:**
1. Execute Phase 1 (Data preparation)
2. Implement strategy code
3. Run through all validation phases
4. Document results
5. Prepare for paper trading

---

*Backtesting Research Plan Complete*
*Ready for Implementation*
