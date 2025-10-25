#!/usr/bin/env python3
import argparse
import os
import sys
import time
from datetime import datetime, timedelta
from typing import List, Tuple, Optional

import pandas as pd

# Lazy import to give a clearer error if yfinance is missing
try:
    import yfinance as yf
except Exception as e:
    print("Error: yfinance is not installed. Install with: pip install yfinance", file=sys.stderr)
    raise

def read_symbols(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    # Normalize column names
    cols = {c.strip().lower(): c for c in df.columns}
    if "symbol" not in cols:
        raise ValueError("Input CSV must contain a 'Symbol' column")
    # Try to find a security name column if present
    sec_name_col = None
    for key in ("security name", "security", "name", "company", "company name"):
        if key in cols:
            sec_name_col = cols[key]
            break
    if sec_name_col is None:
        # Create a placeholder
        df["Security Name"] = ""
        sec_name_col = "Security Name"
    else:
        # Ensure the column is named exactly "Security Name"
        if sec_name_col != "Security Name":
            df.rename(columns={sec_name_col: "Security Name"}, inplace=True)
    # Ensure Symbol column exact name
    if cols["symbol"] != "Symbol":
        df.rename(columns={cols["symbol"]: "Symbol"}, inplace=True)
    # Drop rows with missing symbols
    df = df[df["Symbol"].astype(str).str.strip().ne("")].copy()
    df["Symbol"] = df["Symbol"].astype(str).str.strip()
    return df[["Symbol", "Security Name"]]

def safe_download(
    ticker: str,
    period: str = "10y",
    interval: str = "1d",
    auto_adjust: bool = True,
    max_retries: int = 3,
    pause: float = 1.0
) -> pd.DataFrame:
    """Download with simple retry logic. Returns empty DataFrame if nothing."""
    last_err = None
    for attempt in range(1, max_retries + 1):
        try:
            df = yf.download(
                tickers=ticker,
                period=period,
                interval=interval,
                auto_adjust=auto_adjust,
                threads=False,
                progress=False
            )
            # Some tickers return multi-index columns even for single ticker in some yfinance versions
            if isinstance(df.columns, pd.MultiIndex):
                # Prefer the 'Close' level flattening
                df.columns = [" ".join([str(c) for c in col if str(c) != ""]).strip() for col in df.columns.values]
            if not df.empty:
                df = df.reset_index()
            return df
        except Exception as e:
            last_err = e
            if attempt < max_retries:
                time.sleep(pause * attempt)
            else:
                # On final failure, return empty with error note in metadata via attribute
                empty = pd.DataFrame()
                empty.attrs["error"] = str(e)
                return empty
    # Should not reach here
    empty = pd.DataFrame()
    if last_err is not None:
        empty.attrs["error"] = str(last_err)
    return empty

def process_symbols(
    df_symbols: pd.DataFrame,
    outdir: str,
    threads: int = 4,
    auto_adjust: bool = True
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Returns:
        combined_df: all rows appended, with columns: Date, Open, High, Low, Close, Adj Close?, Volume, Symbol, Security Name
        log_df: per-symbol status log
    """
    os.makedirs(outdir, exist_ok=True)
    # Simple concurrency using ThreadPoolExecutor
    from concurrent.futures import ThreadPoolExecutor, as_completed

    results = []
    logs = []
    tasks = {}

    def worker(sym: str, name: str):
        data = safe_download(sym, period="10y", interval="1d", auto_adjust=auto_adjust)
        status = "ok"
        msg = ""
        if data.empty:
            status = "empty"
            msg = data.attrs.get("error", "")
        else:
            # Standardize column names
            rename_map = {}
            for col in data.columns:
                if col.lower() == "datetime":
                    rename_map[col] = "Date"
            if rename_map:
                data = data.rename(columns=rename_map)
            # Ensure Date column exists
            if "Date" not in data.columns and "Date" not in data.columns.str.title():
                # In most yfinance versions, the index becomes a column named "Date" after reset_index()
                # If not, try to infer
                if "index" in data.columns:
                    data.rename(columns={"index": "Date"}, inplace=True)

            data["Symbol"] = sym
            data["Security Name"] = name

            # Save per-symbol CSV
            safe_sym = "".join([c for c in sym if c.isalnum() or c in ("_", "-", ".")])
            per_csv = os.path.join(outdir, f"{safe_sym}.csv")
            data.to_csv(per_csv, index=False)

        log_row = {"Symbol": sym, "Security Name": name, "status": status, "message": msg}
        return data, log_row

    with ThreadPoolExecutor(max_workers=max(1, threads)) as ex:
        for _, row in df_symbols.iterrows():
            sym = str(row["Symbol"]).strip()
            name = str(row["Security Name"]) if pd.notna(row["Security Name"]) else ""
            tasks[ex.submit(worker, sym, name)] = sym

        for fut in as_completed(tasks):
            data, log_row = fut.result()
            results.append(data)
            logs.append(log_row)

    # Combine
    non_empty = [d for d in results if not d.empty]
    if non_empty:
        combined = pd.concat(non_empty, axis=0, ignore_index=True)
        # Sort by Symbol then Date if Date present
        if "Date" in combined.columns:
            combined.sort_values(by=["Symbol", "Date"], inplace=True)
    else:
        combined = pd.DataFrame()

    log_df = pd.DataFrame(logs)
    # Save combined and logs
    combined_csv = os.path.join(outdir, "combined_daily_10y.csv")
    combined.to_csv(combined_csv, index=False)
    log_csv = os.path.join(outdir, "download_log.csv")
    log_df.to_csv(log_csv, index=False)

    return combined, log_df

def main():
    parser = argparse.ArgumentParser(description="Download 10 years of daily US stock data from Yahoo using a CSV of symbols.")
    parser.add_argument("--input", required=True, help="Path to CSV with columns: Symbol, Security Name")
    parser.add_argument("--outdir", default="yahoo_daily_10y_output", help="Output directory")
    parser.add_argument("--threads", type=int, default=4, help="Number of parallel download threads")
    parser.add_argument("--adjust", action="store_true", help="Auto-adjust OHLC for splits and dividends")
    args = parser.parse_args()

    df_symbols = read_symbols(args.input)
    combined, log_df = process_symbols(df_symbols, args.outdir, threads=args.threads, auto_adjust=args.adjust)

    print(f"Done. Combined rows: {len(combined)}")
    print(f"Outputs:")
    print(f" - Combined CSV: {os.path.join(args.outdir, 'combined_daily_10y.csv')}")
    print(f" - Per-symbol folder: {os.path.join(args.outdir, 'per_symbol')}")
    print(f" - Log CSV: {os.path.join(args.outdir, 'download_log.csv')}")

if __name__ == "__main__":
    main()
