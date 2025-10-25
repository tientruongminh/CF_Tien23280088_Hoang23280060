#!/usr/bin/env bash
set -euo pipefail

INPUT="${1:-american_companies/nasdaq-listed.csv}"
OUTDIR="${2:-data/yfinance}"
LOGDIR="${3:-logs}"

python /content/yfin_downloader_colab_safe.py \
  --input "$INPUT" \
  --outdir "$OUTDIR" \
  --adjust \
  --sleep 0.5 \
  --logfile "$LOGDIR/yfin_download.log"
