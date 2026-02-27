# Article: Cross-Exchange Funding Rate Arbitrage with Boros
**Source:** Boros_Fi / Medium (Pendle Team)  
**Date:** December 19, 2025  
**Author:** Pendle Team

## Full Content

### Executive Summary

Perpetuals markets have become the most traded financial market in crypto with Open Interest (OI) regularly exceeding $150-$200B. Given identical asset exposure, funding rates should equilibrate across platforms through arbitrage. In reality, they rarely do - persistent spreads exist daily, presenting arbitrage opportunities.

**Key Findings:**
- Cross-perp funding rate arbitrage delivers consistent yields of **5.98%-11.4% Fixed APR** across BTC and ETH markets between Hyperliquid and Binance
- Returns outperform traditional low-risk strategies (AAVE lending, ETH staking) by 2-4x with zero directional price exposure
- Peak opportunities exceeded **23% APR** during observation, with prior instances reaching **48% APR**
- These arbitrage opportunities present themselves repeatedly over time - recurring extractable yield streams rather than isolated events
- Unlike traditional funding rate arbitrage exposed to rate volatility, this strategy with Boros locks in fixed yields at entry
- Opportunities extend across other assets (BNB, HYPE) and exchanges (OKX, Bybit)

### How Funding Rate Arbitrage Works

**Perpetual futures don't have expiry.** Exchanges use funding rates to keep perp prices anchored to spot. Funding is the periodic payment exchanged between longs and shorts.

- When perp > spot, funding is positive → longs pay shorts
- When perp < spot, funding is negative → shorts pay longs

Different exchanges have different liquidity, trader flows, market sentiment, and risk models, so cross-venue perp markets don't move perfectly in sync. This creates persistent opportunities.

**Example:**
- Funding rate BTC on Exchange A → +5% APR (Long)
- Funding rate BTC on Exchange B → +25% APR (Short)

Being short on B is attractive since shorts receive 25% APR. Long on A is cheap as longs only pay 5% APR. Funding differential: 25% - 5% = **20% APR**

### Traditional Naked Arbitrage Challenges

Traditional approach sounds simple: take opposite perp positions on 2 exchanges. But in practice, it's operationally heavy:

- Requires margin deposited on multiple exchanges
- 2 separate perp positions means double liquidation risks
- Double risk of losing on funding fees if differential changes
- During volatile conditions, difficult to ensure healthy margin and rebalancing

### Boros Solution: Fixed-Rate Funding

Boros facilitates Interest Rate Swaps onchain called Yield Units (YUs), where one YU represents one notional unit of the perp market's funding.

**Example:** 10 YU-BTCUSDT-BN represents funding of 10 notional BTC on Binance's BTCUSDT perp market

YUs are priced according to their Implied APR, while holders receive/pay Underlying APR (floating funding rate):

**Long Perp + Long YU (Pay Fixed):**
- Long YUs: Receive Underlying APR (floating), pay fixed Implied APR
- Long perp: Pay Underlying APR (floating)
- Result: Floating APR cancels out, pay only fixed Implied APR

**Short Perp + Short YU (Receive Fixed):**
- Short YUs: Pay Underlying APR (floating), receive fixed Implied APR  
- Short perp: Receive Underlying APR (floating)
- Result: Floating APR cancels out, receive only fixed Implied APR

### Boros Arbitrage Strategy Steps

**Assuming Hyperliquid has higher Implied APR:**

A. Short Hyperliquid BTC YU (on Boros)  
B. Short BTC on Hyperliquid  
C. Long Binance BTC YU (on Boros)  
D. Long BTC on Binance

**Result:**
- A + B = Receive fixed funding on BTC on Hyperliquid
- C + D = Pay fixed funding on BTC on Binance
- B + D = Delta-neutral on BTC
- **A + B + C + D = Receive fixed funding differential with zero BTC price exposure or funding rate volatility**

### Benefits of Boros Approach

1. **Elimination of funding-rate volatility risk:** Lock in fixed rate, no worry about sudden swings
2. **Fixed yield strategy:** Lock in differences immediately when they appear
3. **Longer duration arbitrage:** Positions can be held safely for much longer
4. **Immunity to extended negative rates:** Lock in arbitrage when it appears
5. **Enhanced returns with leverage:** Amplify fixed-yield returns (e.g., 15% Fixed APR × 10x leverage = 150% Fixed APR)
6. **Delta-neutral:** Eliminates directional price risk

### Empirical Analysis Results

#### BTC (October 31, 2025 Maturity)
- Persistent pricing gap: average **11.4%** discrepancy
- **Weighted Average Fixed APR: 11.4%**
- Average Position Size: 1.21 BTC per opportunity
- Peak opportunities: up to 23.5% APR

#### BTC (November 28, 2025 Maturity)
- Average discrepancy: **6.42%** (smaller but still consistent)
- **Weighted Average Fixed APR: 6.42%**
- Average Position Size: 0.71 BTC per opportunity
- Peak opportunities: 12.36% APR

#### ETH (October 31, 2025 Maturity)
- Average discrepancy: **9.94%**
- **Weighted Average Fixed APR: 9.94%**
- Average Position Size: 40.65 ETH (~1.44 BTC equivalent)
- Peak opportunities: 23.88% APR

#### ETH (November 28, 2025 Maturity)
- Average discrepancy: **5.98%**
- **Weighted Average Fixed APR: 5.98%**
- Average Position Size: 34.26 ETH (~1.21 BTC equivalent)
- Peak opportunities: 17.1% APR

**Comparison to Traditional Yields:**
- 3.5-9x higher than ETH staking (2.5-3%)
- 2.3-3x higher than AAVE lending (3.0-4.0%)
- Competitive with sUSDe while providing fixed, predictable returns

### Risk Considerations

**Orderbook Depth & Liquidity:**
- Maximum trade sizes: low-6 figures in margin
- Real-world liquidity may vary
- Orderbook recovery may extend beyond 1 hour
- Exiting positions may require careful limit orders or TWAP execution

**Asset Volatility & Liquidation Risks:**
While overall position is delta-neutral, individual legs exposed:
- Hyperliquid short perp: Vulnerable if BTC/ETH spikes up
- Binance long perp: Vulnerable if BTC/ETH crashes down
- Boros short YU: Vulnerable if Implied APR spikes up
- Boros long YU: Vulnerable if Implied APR crashes down

**Timing & Execution Risk:**
- Requires coordination across 4 legs on multiple venues
- Margin must be present on two exchanges plus Boros collateral
- Multi-venue setup introduces execution complexity
- Price volatility may cause imperfect hedges

**Counterparty Risk (BTC):**
- BTC YU trades require wBTC as collateral
- Exposed to BitGo's solvency
- Smart contract risks

**Trading Fees:**
- Boros: 0.05% position fee + 0.2% YU settlement fee
- Binance: 0.02% maker / 0.05% taker
- Hyperliquid: 0.015% maker / 0.045% taker
- Longer duration trades more fee-efficient

### Structural Opportunities Beyond Study

While analysis focused on BTC and ETH between Hyperliquid and Binance, opportunities extend:

**BNB:**
- Binance maintains 0% APR baseline (exchange policy)
- Other venues maintain 10.95% APR standard
- Creates persistent structural arbitrage

**Altcoin Perps:**
- SOL, HYPE, DOGE and others show exchange-specific policies
- Liquidity profiles create durable funding differentials

**Other Exchanges:**
- OKX displays persistent funding gaps
- Total addressable market much larger than study suggests

---

## Key Points Extracted

### 1. Core Arbitrage Concept
**Market Inefficiency:**
- Identical assets should have same funding rates across exchanges
- Reality: Persistent spreads exist daily
- Hyperliquid consistently higher funding than Binance
- Structural differences create ongoing opportunities

**Yield Potential:**
- Average: 5.98% - 11.4% Fixed APR
- Peak: Up to 48% APR historically
- Consistent, recurring opportunities (not one-time)
- 2-4x better than traditional low-risk yields

### 2. Traditional vs Boros Approach

**Traditional Arbitrage Problems:**
- Double perp positions = double liquidation risk
- Funding rate volatility exposure
- Must monitor and adjust constantly
- Operational burden (margin on multiple exchanges)

**Boros Advantages:**
- Converts floating to fixed rates
- Lock in yield at entry
- Eliminates funding rate volatility
- Longer holding periods possible
- Predictable, fixed returns

### 3. Boros Mechanics

**Yield Units (YUs):**
- Interest Rate Swaps onchain
- 1 YU = 1 notional unit of perp funding
- Priced by Implied APR
- Pay/receive Underlying APR (floating)

**Delta-Neutral Fixed Yield Construction:**
- Short YU + Short Perp = Receive Fixed
- Long YU + Long Perp = Pay Fixed
- Combined = Capture spread with no price exposure

### 4. Four-Leg Trade Structure

**Trade Composition:**
1. Short Hyperliquid YU (Boros)
2. Short Hyperliquid Perp
3. Long Binance YU (Boros)
4. Long Binance Perp

**Result:**
- Legs 1+2: Receive fixed on Hyperliquid
- Legs 3+4: Pay fixed on Binance
- Legs 2+4: Delta-neutral BTC/ETH exposure
- Net: Fixed yield from funding differential

### 5. Risk Management

**Primary Risks:**
- Individual leg liquidation (despite delta-neutral overall)
- Orderbook liquidity constraints
- Execution timing across 4 legs
- Counterparty risk (wBTC custodian)
- Trading fees eroding profits

**Mitigation:**
- Maintain excess margin on each leg
- Monitor real-time orderbook depth
- Use tools like Insilico Terminal for multi-exchange management
- Diversify across multiple exchanges
- Account for all fees in profit calculations

### 6. Market Opportunity Scale

**Current Markets:**
- BTC/ETH Hyperliquid vs Binance: 5.98-11.4% APR
- Multiple maturities (October/November 2025)
- Position sizes: 0.71-1.44 BTC equivalent average

**Expansion Potential:**
- BNB: 0% vs 10.95% structural gap
- Altcoins: SOL, HYPE, DOGE showing spreads
- Additional exchanges: OKX, Bybit
- Total addressable market much larger

### 7. Practical Implementation

**Requirements:**
- Margin on Hyperliquid and Binance
- BTC/ETH collateral on Boros
- Real-time monitoring across 3 platforms
- Ability to execute 4 coordinated trades

**Best Practices:**
- Calculate break-even including all fees
- Monitor individual leg margins
- Use automation tools for execution
- Consider TWAP for large exits
- Maintain significant excess margin

---

## Technical Concepts Explained for 1st Year Dev

**What is a Funding Rate?**
Think of it like interest on a loan. In perpetual futures (contracts that never expire), the exchange needs to keep the futures price close to the actual asset price (spot). If everyone wants to go long (bet price goes up), the futures price gets pushed above spot. The exchange says: "Longs must pay shorts every 8 hours" to discourage this imbalance and bring prices back in line.

**Why Different Exchanges Have Different Rates:**
Each exchange is like a different marketplace. They have different:
- Liquidity (how much money is available)
- Types of traders (aggressive vs conservative)
- Risk management rules
- Settlement schedules (8-hour vs hourly)

So the "interest rate" (funding) varies between them - like how mortgage rates vary between banks.

**What is a Yield Unit (YU)?**
Think of it like a contract that says: "I agree to pay/receive whatever the funding rate is on this exchange." It's a way to bet on or hedge against funding rates themselves, separate from the actual asset price.

**Delta-Neutral Explained:**
- Long Spot: You buy Bitcoin → you profit if BTC goes up
- Short Perp: You bet Bitcoin will go down → you profit if BTC goes down
- Combined: If BTC goes up $100, you gain on spot but lose on short = $0 net
- If BTC goes down $100, you lose on spot but gain on short = $0 net
- Result: You don't care about BTC price direction (delta = 0)

But you DO care about funding rates! While price-neutral, you're earning funding payments every 8 hours.

**Fixed vs Floating Rates:**
- Floating: Rate changes every 8 hours (unpredictable)
- Fixed: Rate locked in at entry (predictable)
- Boros lets you convert floating to fixed, removing uncertainty

**Why Four Legs?**
Think of it like a complex equation where we want to isolate just the funding rate difference:
- Leg 1+2: Capture Hyperliquid funding
- Leg 3+4: Capture Binance funding  
- Legs 2+4: Cancel out price exposure
- Result: Only funding rate difference remains

**APR Calculation:**
- 0.05% per 8 hours = 0.05% × 3 payments/day × 365 days = 54.75% APR
- This is why small funding rates can become massive annual returns

---

## Implementation Ideas for Developers

### 1. System Architecture
```
Data Collection:
├── Funding rates from Hyperliquid
├── Funding rates from Binance
├── Implied APR from Boros (both exchanges)
└── Real-time spot and perp prices

Risk Monitor:
├── Individual leg margin levels
├── Overall position delta
├── Liquidation distances
└── Funding rate trend analysis

Execution Engine:
├── Coordinated 4-leg trade execution
├── TWAP for large positions
├── Margin rebalancing
└── Emergency position closure

Profit Tracker:
├── Fixed rate locked in
├── Fees paid
├── Net P&L
└── APR calculation
```

### 2. Core Algorithm
```python
class FundingArbitrageBot:
    def __init__(self):
        self.min_apr_threshold = 0.10  # 10% minimum
        self.exchanges = ['hyperliquid', 'binance']
        self.position = None
        
    def scan_opportunities(self):
        """Scan for funding rate differentials"""
        opportunities = []
        
        for asset in ['BTC', 'ETH']:
            hl_rate = self.get_implied_apr('hyperliquid', asset)
            bn_rate = self.get_implied_apr('binance', asset)
            
            if hl_rate > bn_rate:
                spread = hl_rate - bn_rate
                if spread > self.min_apr_threshold:
                    opportunities.append({
                        'asset': asset,
                        'spread': spread,
                        'hl_rate': hl_rate,
                        'bn_rate': bn_rate,
                        'action': 'short_hl_long_bn'
                    })
        
        return opportunities
    
    def execute_arbitrage(self, opportunity):
        """Execute 4-leg trade"""
        asset = opportunity['asset']
        
        # Leg 1: Short Hyperliquid YU
        self.boros.short_yu('hyperliquid', asset, notional)
        
        # Leg 2: Short Hyperliquid Perp
        self.hyperliquid.short_perp(asset, notional)
        
        # Leg 3: Long Binance YU
        self.boros.long_yu('binance', asset, notional)
        
        # Leg 4: Long Binance Perp
        self.binance.long_perp(asset, notional)
        
        self.position = {
            'asset': asset,
            'notional': notional,
            'locked_apr': opportunity['spread'],
            'legs': 4,
            'entry_time': datetime.now()
        }
    
    def monitor_position(self):
        """Monitor all 4 legs"""
        for leg in self.position.legs:
            margin_level = self.get_margin_level(leg)
            if margin_level < 0.5:  # 50% threshold
                self.send_alert(f"MARGIN WARNING: {leg}")
            if margin_level < 0.25:  # 25% threshold
                self.emergency_close(leg)
```

### 3. Risk Management Module
```python
class RiskManager:
    def __init__(self):
        self.max_leg_exposure = 0.20  # 20% per exchange
        self.min_margin_buffer = 3.0  # 3x requirement
        
    def validate_trade(self, opportunity):
        """Pre-trade validation"""
        # Check liquidity
        if not self.check_orderbook_depth(opportunity):
            return False
            
        # Check margin availability
        total_margin_needed = self.calculate_margin(opportunity)
        if total_margin_needed > self.available_margin * 0.8:
            return False
            
        # Check fee impact
        fees = self.calculate_fees(opportunity)
        if fees > opportunity['spread'] * 0.2:  # Max 20% of spread
            return False
            
        return True
    
    def calculate_fees(self, opportunity):
        """Calculate all trading fees"""
        boros_fee = notional * 0.0005  # 0.05%
        boros_settlement = notional * 0.002  # 0.2%
        binance_fee = notional * 0.0002  # 0.02% maker
        hyperliquid_fee = notional * 0.00015  # 0.015% maker
        
        return boros_fee + boros_settlement + binance_fee + hyperliquid_fee
```

### 4. Key Metrics Dashboard
- Current funding rates (all exchanges)
- Implied APR spreads
- Active position P&L
- Individual leg margin levels
- Locked APR vs current rates
- Cumulative fees paid
- Net APY achieved

### 5. Automation Considerations
- 24/7 monitoring required (crypto never sleeps)
- API rate limits across multiple platforms
- WebSocket connections for real-time data
- Automated margin rebalancing
- Emergency stop mechanisms
- Profit-taking and re-entry logic

---

**Tags:** #FundingRateArbitrage #CrossExchange #FixedYield #DeltaNeutral #Boros #PerpetualFutures
