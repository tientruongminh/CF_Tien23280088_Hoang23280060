#!/bin/bash

FILE="${1}"

python week123/src/run_momentum_strategy.py \
  --csv_path "week123/data/yfinance/per_symbol/${FILE}.csv" \
  --lookback_months 3 \
  --skip_recent_months 1 \
  --n_long 20 \
  --n_short 20 \
  --long_capital 0.6 \
  --short_capital 0.4
