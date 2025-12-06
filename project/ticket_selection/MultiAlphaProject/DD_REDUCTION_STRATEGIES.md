# Drawdown Reduction Strategies

## 🎯 OBJECTIVE

**Current:** Banks cluster Max DD = -48.6%  
**Target:** Reduce to -30% to -35% range  
**Methods:** 3 practical strategies

---

## 📊 STRATEGY 1: Dynamic Exposure Scaling (Volatility-Based)

### Concept
Reduce position size when market volatility is high

### Implementation

```python
def calculate_dynamic_exposure(df_close, window=60):
    """
    Scale exposure based on volatility
    """
    returns = df_close.mean(axis=1).pct_change()
    rolling_vol = returns.rolling(window).std() * np.sqrt(252)
    current_vol = rolling_vol.iloc[-1]
    
    # Scale exposure inversely with vol
    if current_vol < 0.20:      # Low vol (< 20%)
        exposure = 1.0          # 100%
    elif current_vol < 0.30:    # Normal (20-30%)
        exposure = 0.75         # 75%
    elif current_vol < 0.40:    # High (30-40%)
        exposure = 0.50         # 50%
    else:                       # Crisis (> 40%)
        exposure = 0.25         # 25%
    
    return exposure
```

### Expected Impact
```
During COVID March 2020:
- Vol spiked to 60%
- Exposure would drop to 25%
- DD: -48% → ~-25% (estimated)

Normal times:
- Vol 15-25%
- Exposure 75-100%
- Returns: Maintain most upside
```

**Pros:** 
- Automatic risk reduction in crises
- Preserves upside in calm markets

**Cons:**
- May exit too early
- Transaction costs from scaling in/out

**Estimated DD Reduction:** -48% → -35%

---

## 📉 STRATEGY 2: Trailing Stop-Loss

### Concept
Exit when drawdown hits threshold, resume when recovered

### Implementation

```python
def apply_trailing_stoploss(
    positions,
    cumulative_returns,
    stop_threshold=-0.30,   # Exit at -30% DD
    resume_threshold=-0.15  # Resume at -15% DD
):
    """
    Progressive stop-loss with recovery
    """
    running_max = cumulative_returns.cummax()
    drawdown = (cumulative_returns - running_max) / running_max
    
    stopped = False
    modified_positions = positions.copy()
    
    for date in positions.index:
        current_dd = drawdown.loc[date]
        
        # Trigger stop
        if current_dd < stop_threshold:
            stopped = True
            print(f"STOP-LOSS: DD {current_dd:.1%}")
        
        # Resume trading
        elif stopped and current_dd > resume_threshold:
            stopped = False
            print(f"RESUME: DD recovered to {current_dd:.1%}")
        
        # Zero positions if stopped
        if stopped:
            modified_positions.loc[date] = 0
    
    return modified_positions
```

### Example Scenario

```
Normal Trading:
Day 1-50: Portfolio growing, DD = -5% to -10%

Crisis Hits:
Day 51: DD = -31% → TRIGGER STOP-LOSS
Day 52-80: Flat (0% exposure, preserving capital)

Recovery:
Day 81: DD recovered to -14% → RESUME TRADING
Day 82+: Back to normal trading

Result:
- Max DD capped at -30%
- Missed some bottom (cost)
- But avoided -48% disaster
```

**Pros:**
- Hard cap on maximum loss
- Automatic execution

**Cons:**
- May sell at bottom
- Miss recovery if exits permanently

**Estimated DD Reduction:** -48% → -30%

---

## 🎲 STRATEGY 3: Kelly Criterion Position Sizing

### Concept
Size positions based on win rate & profit factor (optimal f)

### Formula

```
Kelly % = Win_Rate - [(1 - Win_Rate) / Win_Loss_Ratio]
```

### For Banks Cluster

```python
# Current metrics
win_rate = 0.547  # 54.7%
win_loss_ratio = 1.115  # Wins are 11.5% bigger than losses

# Kelly calculation
kelly_pct = 0.547 - ((1 - 0.547) / 1.115)
kelly_pct = 0.547 - 0.406
kelly_pct = 0.141  # 14.1%

# Half-Kelly (more conservative)
half_kelly = 0.141 / 2 = 0.07  # 7%
```

### Implementation

```python
def calculate_kelly_sizing(win_rate, profit_factor):
    """
    Calculate optimal position size
    """
    win_loss_ratio = profit_factor  # Approximation
    
    kelly = win_rate - ((1 - win_rate) / win_loss_ratio)
    
    # Clip to reasonable range
    kelly = max(0.05, min(kelly, 0.25))  # 5-25%
    
    # Use half-Kelly for safety
    return kelly / 2
```

### Application

```
Current: 100% exposure (25% per stock × 4 stocks)

Kelly-Based:
- Full Kelly: 14% total → 3.5% per stock
- Half Kelly: 7% total → 1.75% per stock

Result:
- Much smaller positions
- DD would be proportionally smaller
- But returns also much lower
```

**Analysis:**
- Full Kelly: Too conservative for our case
- Better: Modified Kelly with 40-60% of full Kelly

```python
# Modified approach
base_exposure = 1.0  # 100%
kelly_factor = calculate_kelly_sizing(0.547, 1.38)
# = 0.141

modified_exposure = base_exposure * min(1.0, kelly_factor * 5)
# = 1.0 * min(1.0, 0.705) = 0.705 = 70%
```

**Estimated DD Reduction:** -48% → -34%

---

## 🔧 STRATEGY 4: Diversification Within Cluster

### Concept
Add more stocks to Banks cluster

### Current

```
4 stocks: BAC, JPM, WFC, C
Average correlation: ~0.55
```

### Proposed

```
Add 2-3 more regional banks:
- USB (US Bancorp)
- PNC (PNC Financial)
- TFC (Truist Financial)

Total: 6-7 stocks
Expected correlation: ~0.45 (lower)
```

### Impact

```python
# Portfolio variance formula
σ_portfolio² = (1/n) * σ² + (1 - 1/n) * Cov

With 4 stocks:
σ_p² = 0.25σ² + 0.75*Cov

With 7 stocks:
σ_p² = 0.14σ² + 0.86*Cov

Reduction: ~12% lower variance
```

**Expected DD Reduction:** -48% → -42%

---

## 💰 STRATEGY 5: Partial Cash Reserve

### Concept
Keep 20-30% in cash as buffer

### Implementation

```python
# Instead of 100% invested
max_gross_exposure = 0.75  # 75%

# Benefits
- 25% cash cannot lose value
- Available for opportunities
- Reduces overall portfolio volatility
```

### Impact

```
Original Portfolio:
- 100% exposure
- Max DD: -48.6%

With 25% Cash:
- 75% exposure to strategy
- DD on invested portion: -48.6%
- Total portfolio DD: -48.6% × 0.75 = -36.5%
```

**Estimated DD Reduction:** -48% → -36%

**Trade-off:** Returns also reduced by 25%

---

## 📊 COMBINED STRATEGY RECOMMENDATION

### Best Approach: Multi-Layer Protection

```python
def enhanced_risk_management(
    positions,
    df_close,
    cumulative_returns
):
    """
    Combine multiple strategies
    """
    # Layer 1: Kelly-based max exposure (70%)
    base_exposure = 0.70
    
    # Layer 2: Vol-adjusted dynamic scaling
    vol_multiplier = calculate_dynamic_exposure(df_close)
    current_exposure = base_exposure * vol_multiplier
    
    # Layer 3: Stop-loss protection
    positions = apply_trailing_stoploss(
        positions,
        cumulative_returns,
        stop_threshold=-0.30
    )
    
    # Apply exposure
    positions = positions * current_exposure
    
    return positions
```

### Expected Results

```
Normal Market:
- Exposure: 70% (Kelly-adjusted)
- DD reduction from exposure: -48% → -34%

High Vol Market:
- Exposure: 35% (70% × 0.5 vol scaling)
- DD reduction: -34% → -20%

Crisis (DD > -30%):
- Exposure: 0% (stop-loss triggered)
- DD capped at: -30%

Overall Expected Max DD: -25% to -30%
```

---

## ✅ IMPLEMENTATION PRIORITIES

### Priority 1: Dynamic Exposure (Easiest)
```
Effort: LOW (50 lines of code)
Impact: MEDIUM (-48% → -35%)
Recommended: YES - implement first
```

### Priority 2: Stop-Loss (Medium)
```
Effort: MEDIUM (100 lines)
Impact: HIGH (-48% → -30%)
Recommended: YES - strong protection
```

### Priority 3: Add Stocks (Data-dependent)
```
Effort: HIGH (need data collection)
Impact: MEDIUM (-48% → -42%)
Recommended: IF data available
```

### Priority 4: Kelly Sizing (Optional)
```
Effort: LOW (simple formula)
Impact: MEDIUM (-48% → -34%)
Recommended: OPTIONAL (conservative)
```

---

## 🎯 FINAL RECOMMENDATION

**Implement Combination:**

1. **70% Base Exposure** (Kelly-influenced)
2. **+Dynamic Vol Scaling** (25-100% of base)
3. **+Stop-Loss at -30%** (hard cap)

**Expected Outcome:**
- Target Max DD: **-30%**
- Expected Returns: **40-50% CAGR** (vs 55% now)
- Sharpe: **1.4-1.5** (vs 1.58 now)

**Trade-off:** Accept 10-15% lower returns for 40% DD reduction

---

*Status: Strategies designed, ready for implementation*  
*Recommendation: Start with Dynamic Exposure + Stop-Loss*
