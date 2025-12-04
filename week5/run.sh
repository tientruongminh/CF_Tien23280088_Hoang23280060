#!/bin/bash

set -euo pipefail

# Path to per-symbol yfinance data
PER_SYMBOL_DIR="/workspaces/CF_Tien23280088_Hoang23280060/week1-3/data/yfinance/per_symbol"

DEFAULT_FEE_BPS=5.0

# Move to folder where run.sh is (week5)
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

run_one_csv() {
    local csv_path="$1"
    local fee_bps="$2"

    if [ ! -f "$csv_path" ]; then
        echo "[ERROR] File not found: $csv_path"
        return 1
    fi

    echo "==========================================="
    echo " Running Week5 Trading Models"
    echo " File: $csv_path"
    echo " Fee bps: $fee_bps"
    echo "==========================================="

    python3 main.py --csv_path "$csv_path" --fee_bps "$fee_bps"

    echo "-------------------------------------------"
    echo " Completed: $csv_path"
    echo "-------------------------------------------"
}

# Case 1: no arguments → run all CSV files
if [ $# -eq 0 ]; then
    echo "Running all CSV files in: $PER_SYMBOL_DIR"

    shopt -s nullglob
    CSV_FILES=("$PER_SYMBOL_DIR"/*.csv)

    if [ ${#CSV_FILES[@]} -eq 0 ]; then
        echo "[ERROR] No CSV files found in $PER_SYMBOL_DIR"
        exit 1
    fi

    for csv in "${CSV_FILES[@]}"; do
        run_one_csv "$csv" "$DEFAULT_FEE_BPS"
    done

    echo "==========================================="
    echo " All jobs finished."
    echo "==========================================="
    exit 0
fi

# Case 2: one or two arguments
TARGET="$1"
FEE_BPS="${2:-$DEFAULT_FEE_BPS}"

CSV_PATH=""

# If TARGET ends with .csv
if [[ "$TARGET" == *.csv ]]; then
    # 1) If it is an existing path as-is (absolute or relative), use it
    if [ -f "$TARGET" ]; then
        CSV_PATH="$TARGET"
    else
        # 2) Otherwise assume it's just a filename inside PER_SYMBOL_DIR
        BASENAME="$(basename "$TARGET")"
        CSV_PATH="$PER_SYMBOL_DIR/$BASENAME"
    fi
else
    # TARGET is a symbol (e.g. ATLO) → add .csv inside PER_SYMBOL_DIR
    CSV_PATH="$PER_SYMBOL_DIR/${TARGET}.csv"
fi

echo "Resolved CSV path: $CSV_PATH"
run_one_csv "$CSV_PATH" "$FEE_BPS"

echo "==========================================="
echo " Done."
echo "==========================================="
