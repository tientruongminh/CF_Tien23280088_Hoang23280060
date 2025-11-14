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


## 5. Design Fundamental-Based Trading Strategies (Optional)

Xây dựng chiến lược dựa trên dữ liệu cơ bản (nếu có)

Gợi ý: phân loại growth stocks và value stocks bằng các tỷ số tài chính

## 6. Build Momentum Strategies

Thiết kế chiến lược momentum dựa trên dữ liệu price–volume



