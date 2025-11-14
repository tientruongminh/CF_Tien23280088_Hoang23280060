#!/bin/bash

python week123/src/run_strategy.py \
  --csv_path "week123/data/yfinance/per_symbol/ATLO.csv" \
  --window 20 \
  --num_std 2 \
  --initial_capital 10000
