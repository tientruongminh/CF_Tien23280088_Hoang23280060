# Lab: Week 1 to Week 3
## 1. Collect Price–Volume Data

Download historical OHLC data: open, high, low, close

Include adjusted close and trading volume

### Yfinance Library
Dataset: [Kaggle](https://www.kaggle.com/datasets/hoanggvo/computational-finance)

This is our full-crawled version, contains the full ticket combined and each ticket price in separated, in 10 years period, those are not anything that having on the internet. 

There are samples in data/yfinance/per_symbol.
Big Note: as the code convention, the samples don't have the adjusted close column, but actually, the close price is the adjusted close. 

If you refer VNese ticket, please checkout this version (we currently not using this for out main stream): [Kaggle](https://www.kaggle.com/datasets/khanhkdn/vietnam-stock-market-as-of-september-11-2025?select=all_stocks.csv)

## 2. Collect Fundamental Data

Download fundamental datasets (nếu có nguồn miễn phí)

Ví dụ: EPS, P/E, P/B, ROE, revenue, etc.

Job has been done: Using simfin (free public API key) to download Fundamental Data. 
Please check the codes in notebooks/simfin_demo.ipynb
The demo results are in data/simfin

## 3. Study Technical Indicators

Tham khảo sách, tài liệu online, blog, Google Search

Một số chỉ báo phổ biến: MA, EMA, RSI, MACD, Bollinger Bands, OBV, v.v.

## 4. Design Technical-Based Trading Strategies

Chuyển ý tưởng hoặc giả thuyết giao dịch thành biểu thức toán học / code

Xây dựng chiến lược dựa trên các technical indicators

Kiểm tra mô hình bằng dữ liệu giá – khối lượng lịch sử


## 4.1. Goal

Build a small Python mini-library that:

1. Loads 10 years of daily price data from `ATLO.csv`.
2. Computes basic technical indicators:
   - Simple Moving Average (SMA) with configurable window (e.g., 10 or 20 days)
   - Rolling standard deviation (same window)
   - Bollinger Bands:
     - Upper = SMA + k·σ
     - Lower = SMA − k·σ
     - Default k = 2
3. Generates trading signals using the Bollinger Band logic:
   - **Buy** when price moves **up into the band** from **below the lower band**
   - **Sell** when price moves **down into the band** from **above the upper band**
4. Runs a simple backtest over the full 10-year dataset.

## 4.2. Planned Strategy Logic

### 4.2.1. Simple Moving Average (SMA)

$$
\text{SMA}_t = \frac{1}{N} \sum_{i=0}^{N-1} C_{t-i}
$$

### 4.2.2. Rolling Standard Deviation

$$
\sigma_t = \sqrt{\frac{1}{N-1} \sum_{i=0}^{N-1} (C_{t-i} - \text{SMA}_t)^2}
$$

### 4.2.3. Bollinger Bands

$$
\text{Upper}_t = \text{SMA}_t + k\sigma_t
$$

$$
\text{Lower}_t = \text{SMA}_t - k\sigma_t
$$

### 4.2.4 Trading Signals (Mean Reversion)

#### Buy Signal (time t)

- Yesterday:  
  $$
  C_{t-1} < \text{Lower}_{t-1}
  $$
- Today:  
  $$
  \text{Lower}_t \le C_t \le \text{Upper}_t,\quad C_t > C_{t-1}
  $$

#### Sell Signal (time t)

- Yesterday:  
  $$
  C_{t-1} > \text{Upper}_{t-1}
  $$
- Today:  
  $$
  \text{Lower}_t \le C_t \le \text{Upper}_t,\quad C_t < C_{t-1}
  $$

### 4.2.5. Backtest Assumptions

- Long-only strategy
- Start with no position
- Buy when signal = +1 and currently flat
- Sell when signal = −1 and currently long
- Execute trades at **next day’s Open**
- Position sizing: **all-in**
- Optional parameters: commission and slippage (default = 0)

---

## 4.3. Planned Module Structure

### `data_loader.py`
- `load_price_data(path)`  
  Cleans CSV, fixes types, sorts by date.

### `indicators.py`
- `sma(series, window)`
- `rolling_std(series, window)`
- `bollinger_bands(series, window, num_std=2.0)`

### `signals.py`
- `bollinger_reversion_signals(df, window, num_std=2.0)`  
  Produces columns:  
  - `sma`  
  - `bb_upper`  
  - `bb_lower`  
  - `signal` (1 = buy, −1 = sell, 0 = none)

### `backtest.py`
- `backtest_long_only(df, initial_capital=10000, commission_per_trade=0.0, slippage_bps=0.0)`  
  Tracks:
  - Shares
  - Cash
  - Portfolio value
  - Returns and cumulative returns

### `run_strategy.py` (optional)
- Script connecting all modules to run the strategy on `ATLO.csv`

---

## 4.4. Default Assumptions

- Daily data from a sample in github: ATLO.csv 
- Indicators exactly as defined (SMA, Std, Bollinger Bands)
- Strategy uses “re-enter band” mean-reversion logic
- Trading rules:
  - Long-only
  - All-in buys, full exit on sells
  - Execute trades at next-day Open
  - Transaction costs optional (default 0)

## 4.5. How to run && results
```bash
!bash week123/scripts/run_strategy.sh ATLO

# Backtest summary:
#   initial_capital: 10000.0000
#   final_equity: 8572.0321
#   total_return: -0.1428
#   annualized_return: -0.0153
#   annualized_volatility: 0.2279
#   sharpe_ratio: -0.0672
#   max_drawdown: -0.4756
#   n_days: 2514
#   n_trades: 48
```

```bash
!bash week123/scripts/run_strategy.sh ATOS

# Backtest summary:
#   initial_capital: 10000.0000
#   final_equity: 855.4787
#   total_return: -0.9145
#   annualized_return: -0.2184
#   annualized_volatility: 0.6244
#   sharpe_ratio: -0.3498
#   max_drawdown: -0.9833
#   n_days: 2514
#   n_trades: 42
```


## 5. Design Fundamental-Based Trading Strategies (Optional)

Xây dựng chiến lược dựa trên dữ liệu cơ bản (nếu có)

Gợi ý: phân loại growth stocks và value stocks bằng các tỷ số tài chính

## 6. Build Momentum Strategies

Thiết kế chiến lược momentum dựa trên dữ liệu price–volume

> ### Momentum Research Pipeline Overview

## 6.1. Overall Pipeline Logic

The momentum framework is structured as a clean, modular research pipeline.

### **Data Layer**
Transform daily stock prices into a monthly return panel suitable for momentum analysis.

### **Signal Layer**
Use past returns to create momentum scores and convert them into portfolio weights for:

- **Cross-sectional long-short momentum** across many stocks
- **Time-series momentum** for a single stock

### **Backtest Layer**
Apply weights to future returns (with proper lag to prevent look-ahead bias) and compute portfolio performance and statistics.

### **Example Script Layer**
End-to-end workflow:
- Load data
- Create monthly return panel
- Choose momentum model
- Output results

Core idea:
> Assets with strong recent performance tend to continue performing strongly for a while, and assets with weak performance tend to stay weak.

---

## 6.2. Data Logic (`momentum_data`)

This section covers how to transform multiple raw CSVs (e.g., `ATLO.csv`) into a clean momentum-ready dataset.

### **6.2.1 Build a Daily Price Panel**

#### Logic:
Each CSV contains:
- `Date`
- Price column (usually `Close`)
- `Symbol`

Steps:
1. Clean dates and price values.
2. Pivot so rows = dates and columns = symbols.
   - If a CSV has many symbols → each symbol becomes a column.
   - If it has one symbol → one column.
3. For multiple CSVs:
   - Read and vertically stack all rows.
   - Pivot into a matrix:  
     **rows = dates**, **columns = symbols**, **cells = closing prices**.

**Result:**  
Daily price panel of shape:  
`[num_days, num_stocks]`.

---

### **6.2.2 Convert Daily Prices to Monthly Prices**

#### Logic:
For each stock:

- Group daily prices by calendar month.
- Monthly price = **last trading day** of the month.

**Result:**  
Monthly price panel:  
`[num_months, num_stocks]`.

---

### **6.2.3 Compute Monthly Log Returns**

For each stock and month $t$:

$$
\text{log\_return}_t = \ln\left(\frac{P_t}{P_{t-1}}\right)
$$

Log returns:
- Add over time
- Convenient for momentum scoring

**Result:**  
Monthly log return panel:  
`[num_months, num_stocks]`.

---

## 6.3. Signal Logic (`momentum_signals`)

Turns monthly log returns into momentum signals and portfolio weights.

---

### **6.3.1. Momentum Score**

#### Logic:
For each stock and month $t$:

1. Look back over a fixed number of months.
2. Optionally skip the most recent month (to avoid reversal noise).  
   Example: **12−1 momentum** uses months $t-12$  to  $t-2$.
3. Sum log returns over that window.

#### Interpretation:
- **Large positive score** → strong recent performance (winner)
- **Large negative score** → poor performance (loser)

---

### **6.3.2. Cross-Sectional Long-Short Weights**

At each rebalance month:

1. Take the momentum scores across all stocks.
2. Drop missing values.
3. Rank stocks from highest to lowest.
4. Select:
   - Top `n_long` → long leg
   - Bottom `n_short` → short leg
5. Assign equal weights within each leg:
   - Long leg total weight = `+long_capital` (e.g., +0.5)
   - Short leg total weight = `−short_capital` (e.g., −0.5)

If the universe is small, scale weights to match available stocks.

**Result:**  
Weight matrix with:
- Nonzero weights only for selected long/short stocks
- Long weights sum to a positive number
- Short weights sum to a negative number of similar magnitude

---

### **6.3.3 Leg Returns and Portfolio Return**

Given weights and monthly simple returns:

#### Long leg:

$\text{long\_return} = \frac{\sum w_i r_i}{\sum w_i}$

#### Short leg:
$\text{short\_asset\_return} = \frac{\sum w_i r_i}{\sum w_i}$


$\text{short\_profit} = -\text{short\_asset\_return}$


#### Portfolio return:
If long and short capital are equal:


$\text{portfolio\_return} = \frac{\text{long\_profit} + \text{short\_profit}}{2}$


**Result:**  
Time series of:
- Long leg return
- Short leg return
- Combined portfolio return

---

## 6.4. Backtest Logic (`momentum_backtest`)

Turns signals into a real strategy with performance evaluation.

---

Steps:

1. **Compute momentum scores** using monthly log returns.
2. **Build long-short weights** via ranking and selection.
3. **Lag the weights**  
   - Weights computed at month $t$ are applied to returns from $t$ to $t+1$.
4. **Apply weights to returns**
   - Convert log returns → simple returns
   - Compute leg returns and portfolio return
5. **Compute performance metrics**
   - Cumulative return
   - Mean and stdev of monthly returns
   - Annualized return and volatility
   - Sharpe ratio
   - t-statistic for average monthly return

**Purpose:**  
Evaluate whether cross-sectional momentum is economically and statistically significant.

---

This directly follows momentum intuition:
> If the asset has strong recent momentum, go long.  
> If it has weak momentum, go short.

## 6. How to run && results


```bash
!bash week123/scripts/run_momentum.sh ATLO ATLX ATNI ATON ATOS

# Momentum backtest summary:
#   n_periods: 116
#   mean_monthly_return: 0.1971
#   std_monthly_return: 2.1675
#   annualized_return: 7.6572
#   annualized_volatility: 7.5083
#   sharpe_ratio: 1.0198
#   t_stat_mean_return: 0.9792
#   final_cumulative_return: 3.4868

# First few monthly portfolio returns:
#             long_return  short_return  portfolio_return  cum_return
# Date                                                               
# 2016-04-30    -0.062500     -0.032976         -0.014762   -0.014762
# 2016-05-31    -0.064846     -0.065558          0.000356   -0.014411
# 2016-06-30    -0.055246     -0.024486         -0.015380   -0.029569
# 2016-07-31     0.091850      0.053571          0.019139   -0.010996
# 2016-08-31    -0.054342      0.181052         -0.117697   -0.127399
```

