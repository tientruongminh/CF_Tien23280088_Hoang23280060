# Next Trade Signal Generation Guide

## 🎯 HOW TO GENERATE NEXT TRADE SIGNALS

### OVERVIEW

Next trade signals show **what to buy/sell tomorrow** based on latest data.

**Process:**
```
Latest Price Data → Calculate 5 Alphas → ML Combination → Position Sizing → Recommendations
```

---

## 📋 STEP-BY-STEP GUIDE

### Step 1: Get Latest Price Data

You need **today's closing prices** for all stocks in cluster.

**Option A: Manual Update**
```bash
# Edit CSV file with latest prices
nano project/ticket_selection/clusters/cluster_financial-services_banks-regional.csv

# Add new row at bottom:
2024-12-06,35.20,180.50,42.10,55.80
# Date, BAC, JPM, WFC, C
```

**Option B: Auto-download (if API available)**
```python
import yfinance as yf
import pandas as pd

# Download latest
tickers = ['BAC', 'JPM', 'WFC', 'C']
data = yf.download(tickers, period='1d')['Close']

# Append to existing CSV
df = pd.read_csv('cluster_banks.csv', index_col=0)
df.loc[pd.Timestamp.today()] = data.values
df.to_csv('cluster_banks.csv')
```

---

### Step 2: Create Signal Generation Script

**File:** `generate_next_signals.py`

```python
#!/usr/bin/env python3
"""
Generate Next Trading Day Signals
==================================
Calculates what to buy/sell tomorrow based on latest data.
"""

import pandas as pd
import numpy as np
import pickle
import os

# Import alphas
from alphas import (
    calculate_mr_score, calculate_mom_score, calculate_vb_score,
    calculate_xsr_score, calculate_val_score, predict_combined_score
)
import config

def generate_next_day_signals(cluster_file, model_file=None):
    """
    Generate trading signals for next day
    
    Args:
        cluster_file: Path to CSV with latest prices
        model_file: Trained ML model (optional, trains if not provided)
    
    Returns:
        DataFrame with recommendations per stock
    """
    print(f"\n{'='*60}")
    print(f"NEXT DAY TRADING SIGNALS")
    print(f"{'='*60}\n")
    
    # 1. Load data
    print("📊 Loading latest price data...")
    df_close = pd.read_csv(cluster_file, index_col=0, parse_dates=True)
    print(f"   Data through: {df_close.index[-1]}")
    print(f"   Stocks: {list(df_close.columns)}")
    
    # 2. Calculate alphas
    print("\n⚙️  Calculating alpha signals...")
    scores = {
        "MR":  calculate_mr_score(df_close, config.WINDOW_COI),
        "Mom": calculate_mom_score(df_close, config.WINDOW_MOM),
        "VB":  calculate_vb_score(df_close, config.WINDOW_VOL_SHORT, config.WINDOW_VOL_LONG),
        "XSR": calculate_xsr_score(df_close),
        "Val": calculate_val_score(df_close, config.WINDOW_VALUE),
    }
    
    # 3. Load or train model
    print("\n🤖 Loading ML model...")
    if model_file and os.path.exists(model_file):
        with open(model_file, 'rb') as f:
            model = pickle.load(f)
        print(f"   Loaded from: {model_file}")
    else:
        print("   Training new model...")
        from alphas.combiner_ml import train_lambda_model
        
        model = train_lambda_model(
            scores_dict=scores,
            df_close=df_close,
            alpha=1.0,
            horizon=1,
            min_history=252
        )
        
        # Save for future use
        if model_file:
            with open(model_file, 'wb') as f:
                pickle.dump(model, f)
            print(f"   Saved to: {model_file}")
    
    # Print learned weights
    print("\n📈 ML Learned Weights:")
    for i, alpha_name in enumerate(['MR', 'Mom', 'VB', 'XSR', 'Val']):
        print(f"   {alpha_name:6s}: {model.coef_[i]:+.4f}")
    
    # 4. Get latest signals (last row)
    latest_signals = {}
    for alpha_name, signal_df in scores.items():
        latest_signals[alpha_name] = signal_df.iloc[-1]
    
    # 5. Calculate combined scores
    print("\n🎯 Latest Alpha Signals (Last Trading Day):")
    print(f"   Date: {df_close.index[-1]}")
    
    combined_scores = {}
    recommendations = []
    
    for ticker in df_close.columns:
        # Get signals for this ticker
        alpha_values = {
            name: latest_signals[name][ticker] 
            for name in ['MR', 'Mom', 'VB', 'XSR', 'Val']
        }
        
        # ML combination
        X = np.array(list(alpha_values.values())).reshape(1, -1)
        combined = model.predict(X)[0]
        combined_scores[ticker] = combined
        
        # Determine action
        if combined > 0.3:
            action = "STRONG BUY"
            position = "30%"
        elif combined > 0.1:
            action = "BUY"
            position = "20%"
        elif combined > -0.1:
            action = "HOLD"
            position = "0%"
        elif combined > -0.3:
            action = "REDUCE"
            position = "-10%"
        else:
            action = "SELL"
            position = "-20%"
        
        # Print individual signals
        print(f"\n   {ticker}:")
        print(f"      MR:  {alpha_values['MR']:+.3f}")
        print(f"      Mom: {alpha_values['Mom']:+.3f}")
        print(f"      VB:  {alpha_values['VB']:+.3f}")
        print(f"      XSR: {alpha_values['XSR']:+.3f}")
        print(f"      Val: {alpha_values['Val']:+.3f}")
        print(f"      → Combined: {combined:+.3f}")
        print(f"      → Action: {action} ({position})")
        
        # Store recommendation
        recommendations.append({
            'Ticker': ticker,
            'MR': alpha_values['MR'],
            'Mom': alpha_values['Mom'],
            'VB': alpha_values['VB'],
            'XSR': alpha_values['XSR'],
            'Val': alpha_values['Val'],
            'Combined_Score': combined,
            'Action': action,
            'Position_Size': position,
            'Current_Price': df_close[ticker].iloc[-1]
        })
    
    # 6. Create summary DataFrame
    df_recommendations = pd.DataFrame(recommendations)
    df_recommendations = df_recommendations.sort_values('Combined_Score', ascending=False)
    
    # 7. Portfolio summary
    print(f"\n{'='*60}")
    print("PORTFOLIO SUMMARY FOR NEXT TRADING DAY")
    print(f"{'='*60}")
    
    total_buy = len(df_recommendations[df_recommendations['Action'].str.contains('BUY')])
    total_sell = len(df_recommendations[df_recommendations['Action'].str.contains('SELL|REDUCE')])
    total_hold = len(df_recommendations[df_recommendations['Action'] == 'HOLD'])
    
    print(f"\nActions:")
    print(f"  BUY:  {total_buy} stocks")
    print(f"  HOLD: {total_hold} stocks")
    print(f"  SELL: {total_sell} stocks")
    
    print(f"\nTop Recommendations:")
    print(df_recommendations[['Ticker', 'Combined_Score', 'Action', 'Position_Size']].to_string(index=False))
    
    # 8. Save to file
    output_file = 'next_trading_signals.csv'
    df_recommendations.to_csv(output_file, index=False)
    print(f"\n💾 Saved to: {output_file}")
    
    return df_recommendations


if __name__ == "__main__":
    # Example usage
    cluster = "project/ticket_selection/clusters/cluster_financial-services_banks-regional.csv"
    model = "trained_model_banks.pkl"
    
    signals = generate_next_day_signals(cluster, model)
```

---

### Step 3: Run Signal Generator

```bash
cd /home/tiencd123456/CF_Tien23280088_Hoang23280060-1/project/ticket_selection/MultiAlphaProject

python generate_next_signals.py
```

**Expected Output:**
```
============================================================
NEXT DAY TRADING SIGNALS
============================================================

📊 Loading latest price data...
   Data through: 2024-12-06
   Stocks: ['BAC', 'JPM', 'WFC', 'C']

⚙️  Calculating alpha signals...

🤖 Loading ML model...
   Loaded from: trained_model_banks.pkl

📈 ML Learned Weights:
   MR    : +0.0004
   Mom   : -0.0003
   VB    : +0.0004
   XSR   : +0.0009
   Val   : +0.0007

🎯 Latest Alpha Signals (Last Trading Day):
   Date: 2024-12-06

   BAC:
      MR:  +0.450
      Mom: -0.120
      VB:  +0.230
      XSR: +0.670
      Val: +0.340
      → Combined: +0.520
      → Action: STRONG BUY (30%)

   JPM:
      MR:  +0.230
      Mom: +0.450
      VB:  +0.120
      XSR: -0.230
      Val: +0.450
      → Combined: +0.410
      → Action: STRONG BUY (30%)

   [... other stocks ...]

============================================================
PORTFOLIO SUMMARY FOR NEXT TRADING DAY
============================================================

Actions:
  BUY:  2 stocks
  HOLD: 1 stocks
  SELL: 1 stocks

Top Recommendations:
Ticker  Combined_Score Action       Position_Size
BAC              0.520 STRONG BUY            30%
JPM              0.410 STRONG BUY            30%
WFC              0.050 HOLD                   0%
C               -0.150 REDUCE               -10%

💾 Saved to: next_trading_signals.csv
```

---

### Step 4: Interpret Signals

**next_trading_signals.csv contains:**

| Column | Meaning |
|--------|---------|
| **Ticker** | Stock symbol |
| **MR, Mom, VB, XSR, Val** | Individual alpha scores |
| **Combined_Score** | ML-weighted combination |
| **Action** | STRONG BUY / BUY / HOLD / SELL |
| **Position_Size** | Recommended allocation % |
| **Current_Price** | Latest closing price |

**Trading Rules:**

```
Combined Score > 0.3  → STRONG BUY (30% position)
Combined Score > 0.1  → BUY (20% position)
|Combined Score| < 0.1 → HOLD (no change)
Combined Score < -0.1 → REDUCE (sell 10%)
Combined Score < -0.3 → SELL (sell 20%)
```

---

## 🔄 AUTOMATED DAILY WORKFLOW

### Setup Daily Cron Job

```bash
# Edit crontab
crontab -e

# Add line (runs at 6 PM after market close):
0 18 * * 1-5 cd /home/tiencd123456/CF_Tien23280088_Hoang23280060-1/project/ticket_selection/MultiAlphaProject && python generate_next_signals.py
```

### Email Notifications (Optional)

```python
# Add to generate_next_signals.py
import smtplib
from email.mime.text import MIMEText

def send_signal_email(recommendations):
    """Send trading signals via email"""
    msg = MIMEText(recommendations.to_string())
    msg['Subject'] = f'Trading Signals for {pd.Timestamp.today().date()}'
    msg['From'] = 'your-email@gmail.com'
    msg['To'] = 'your-email@gmail.com'
    
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login('your-email@gmail.com', 'your-password')
        server.send_message(msg)
```

---

## 💡 ADVANCED: REAL-TIME SIGNALS

### Option 1: Add to Dashboard

Integrate into `app.py`:

```python
# In app.py, add new tab
with tabs[2]:  # Trading Signals tab
    st.markdown("### Next Trading Day Signals")
    
    if st.button("Generate Latest Signals"):
        with st.spinner("Calculating..."):
            signals = generate_next_day_signals(cluster_file, model_file)
            st.dataframe(signals)
```

### Option 2: API Endpoint

Create REST API:

```python
from flask import Flask, jsonify
app = Flask(__name__)

@app.route('/api/signals/<cluster>')
def get_signals(cluster):
    signals = generate_next_day_signals(f'clusters/{cluster}.csv')
    return jsonify(signals.to_dict('records'))

if __name__ == '__main__':
    app.run(port=5000)
```

Access via: `http://localhost:5000/api/signals/banks`

---

## 📊 SIGNAL QUALITY INDICATORS

### Confidence Metrics

```python
def calculate_signal_confidence(combined_score, historical_accuracy):
    """
    Assess signal reliability
    """
    # Signal strength
    strength = abs(combined_score)
    
    # Historical win rate for this signal level
    if strength > 0.5:
        expected_win_rate = 0.65  # Strong signals more reliable
    elif strength > 0.3:
        expected_win_rate = 0.58
    else:
        expected_win_rate = 0.52  # Weak signals less reliable
    
    confidence = strength * expected_win_rate
    
    return {
        'strength': strength,
        'confidence': confidence,
        'expected_win_rate': expected_win_rate
    }
```

---

## ✅ CHECKLIST BEFORE TRADING

Before executing next-day signals:

- [ ] Latest price data downloaded (today's close)
- [ ] All 5 alphas calculated without errors
- [ ] ML model loaded successfully
- [ ] Combined scores reasonable (-1 to +1)
- [ ] Position sizes sum ≤ 100%
- [ ] Reviewed high-conviction signals (score > |0.3|)
- [ ] Checked market conditions (VIX, news)
- [ ] Risk management rules applied

---

## 🚨 WARNINGS

**1. Data Quality**
- Ensure prices are latest (not stale)
- Check for corporate actions (splits, dividends)

**2. Signal Delay**
- Signals based on TODAY's close
- Execute TOMORROW at open
- Gap risk exists overnight

**3. Market Conditions**
- Signals assume normal conditions
- During crisis, reduce position sizes
- Consider manual override

---

*Use signals as guidance, not absolute instructions. Always apply discretion and risk management.*
