#!/usr/bin/env bash
set -euo pipefail

INPUT="${1:-week123/american_companies/nasdaq-listed.csv}"
OUTDIR="${2:-week123/data/yfinance}"
LOGDIR="${3:-week123/logs}"
FILTER_MODE="${4:-pre}"          # off | pre | post
MIN_YEARS="${5:-10}"             # minimum number of rows for filtering 

mkdir -p "$OUTDIR" "$LOGDIR"

python week123/src/yfin_downloader.py \
  --input "$INPUT" \
  --outdir "$OUTDIR" \
  --adjust \
  --sleep 0.5 \
  --filter "$FILTER_MODE" \
  --min-years "$MIN_YEARS" \
  --logfile "$LOGDIR/yfin_download.log"
