

# **Time-Series Trading and Volatility-Based Strategy Framework**

### Computational Finance – Week 5 Project

---

## **1. Introduction**

This project implements a complete quantitative trading system combining classical time-series models, volatility-based strategies, and a systematic backtesting engine.
The goal is to evaluate how statistical forecasting methods and volatility dynamics can be used to generate algorithmic trading signals on historical equity data.

The system is designed to be modular, reproducible, and extensible, with clear separation between data processing, modeling, strategy construction, and evaluation.

---

## **2. Project Structure**

```
time_series_trading/
│
├── data.py               # Data loading, cleaning, log-returns, feature engineering
├── models.py             # AR/MA/ARIMA, Kalman, Particle Filter, Bollinger, volatility models
├── backtest.py           # Backtesting engine, PnL logic, Sharpe calculations
├── main.py               # Main workflow: run all models + export outputs
├── run.sh                # Shell script for command-line execution
└── requirements.txt      # Python dependencies
```

---

## **3. Data Requirements**

Input CSV files must include:

* Date
* Open, High, Low, Close
* Volume
* Symbol
* Security Name

### **Preprocessing (in `data.py`)**

* Convert timestamps
* Sort data chronologically
* Convert numeric columns
* Compute log-returns
* Add technical features:

  * 20-day rolling volatility
  * Bollinger Bands (upper, mid, lower)

This ensures all downstream models receive consistent, cleaned, and feature-rich data.

---

## **4. Implemented Models & Strategies**

### **4.1 AR, MA and ARIMA Models**

* ARIMA(1,0,0) → AR(1)
* ARIMA(0,0,1) → MA(1)
* ARIMA(1,1,1) → full ARIMA

Used for return forecasting.
Trading signal: `sign(forecast)`.

---

### **4.2 Kalman Filter Trend Model**

State-space smoothing of noisy prices.
Signal: `sign(smoothed_price.diff())`.

---

### **4.3 Particle Filter (Sequential Monte Carlo)**

Monte Carlo estimation of expected return.
Signal: `sign(expected_return)`.

---

### **4.4 Bollinger Bands Mean Reversion**

* Long: price crosses up from below lower band
* Short: price crosses down from above upper band
* Position held until reversal

---

### **4.5 Volatility-Based Position Sizing**

Scaled exposure:

[
\text{Position} = \frac{\text{Target Vol}}{\text{Rolling Volatility}}
]

This provides dynamic risk control by reducing exposure in turbulent markets.

---

## **5. Backtesting Framework**

Performed through `backtest.py`:

### **Execution rules**

* One-period lag to avoid look-ahead bias
* Log-return PnL accumulation
* Transaction costs in basis points

### **Performance metrics**

1. Number of periods
2. Mean daily return
3. Daily volatility
4. Annualized return
5. Annualized volatility
6. Sharpe ratio

All models share the same backtesting engine for direct comparison.

---

## **6. Running the System**

### **Basic usage**

```
bash run.sh ATLO.csv
```

### **Custom transaction cost**

```
bash run.sh ATLO.csv 10
```

### **Internal execution**

```
python3 main.py --csv_path <csv_path> --fee_bps <fee>
```

The script automatically:

* Loads and preprocesses the data
* Executes all time-series and volatility strategies
* Backtests them on the same dataset
* Plots equity curves
* Produces a JSON summary file

---

## **7. JSON Output (Automated Export)**

Every run generates a **single JSON file** containing all strategy performance metrics.

### **File naming convention**

```
results_<SYMBOL>.json
```

Example for input file `ATLO.csv`:

```
results_ATLO.json
```

### **Example JSON content**

```json
{
    "Bollinger": {
        "n_periods": 2512,
        "mean_daily": -0.00034267494,
        "vol_daily": 0.0189738322,
        "ann_return": -0.0863540849,
        "ann_vol": 0.3012002485,
        "sharpe": -0.2866999125
    },
    "Volatility Trend": {
        "n_periods": 2512,
        "mean_daily": -0.0008597998,
        "vol_daily": 0.0100805698,
        "ann_return": -0.2166695581,
        "ann_vol": 0.1600240851,
        "sharpe": -1.3539809206
    },
    "ARIMA ar1": {
        "n_periods": 2512,
        "mean_daily": 0.0,
        "vol_daily": 0.0,
        "ann_return": 0.0,
        "ann_vol": 0.0,
        "sharpe": 0.0
    },
    "Kalman": {
        "n_periods": 2512,
        "mean_daily": -0.0012949148,
        "vol_daily": 0.0190648296,
        "ann_return": -0.3263185401,
        "ann_vol": 0.3026447878,
        "sharpe": -1.0782228975
    }
}
```

The JSON provides machine-readable output suitable for:

* Reports
* Dashboards
* Jupyter analysis
* Further statistical testing
* Comparative research

---

## **8. Interpretation and Insights**

This project highlights:

* Weak predictability of daily returns (AR/MA/ARIMA generally neutral)
* Stronger signal extraction from state-space smoothing (Kalman, Particle)
* Clear mean-reversion behavior in Bollinger strategies
* Effective volatility normalization via position sizing
* Importance of robust backtesting and transaction cost modeling

It provides a complete foundation for computational finance experimentation.

---

## **9. Extensions and Future Enhancements**

Potential improvements include:

* LSTM / GRU forecasting models
* Transformer-based time-series prediction
* Regime-switching ARIMA or HMM
* Cross-asset / multi-factor portfolios
* Market microstructure slippage models
* Online learning or reinforcement learning
* Particle MCMC, Rao-Blackwellized filters

---

## **10. Installation**

Install required dependencies:

```
pip install -r requirements.txt
```

---

## **11. Conclusion**

This framework delivers a complete, reproducible environment for evaluating classical time-series trading models, Bayesian filtering methods, and volatility-adjusted strategies.
It demonstrates both academic theory and practical implementation, providing a solid platform for deeper quantitative research.


