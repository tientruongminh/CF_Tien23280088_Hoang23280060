#!/bin/bash

FILES=("$@")

# Build full paths
CSV_PATHS=""
for f in "${FILES[@]}"; do
  CSV_PATHS+="week123/data/yfinance/per_symbol/${f}.csv "
done

python week123/src/run_momentum_strategy.py \
  --csv_paths $CSV_PATHS \
  --lookback_months 3 \
  --skip_recent_months 1 \
  --n_long 20 \
  --n_short 20 \
  --long_capital 0.6 \
  --short_capital 0.4
