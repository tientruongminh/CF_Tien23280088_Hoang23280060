#!/usr/bin/env python3
import argparse
import os
import sys
import time
from typing import Optional

import pandas as pd

try:
    import yfinance as yf
except Exception:
    print("Please install dependencies: pip install yfinance pandas", file=sys.stderr)
    raise

def read_symbols(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    cols_l = {c.lower().strip(): c for c in df.columns}
    if "symbol" not in cols_l:
        raise ValueError("CSV must contain a 'Symbol' column")
    sym_col = cols_l["symbol"]
    name_col = None
    for k in ("security name","security","name","company","company name","issuer name","description"):
        if k in cols_l:
            name_col = cols_l[k]
            break
    out = pd.DataFrame()
    out["Symbol"] = df[sym_col].astype(str).str.strip()
    out["Security Name"] = df[name_col].astype(str) if name_col else ""
    out = out[out["Symbol"].ne("")]
    return out.reset_index(drop=True)

def safe_download_one(symbol: str, period: Optional[str], interval: str, start: Optional[str], end: Optional[str], auto_adjust: bool, max_retries: int, pause: float) -> pd.DataFrame:
    last_err = None
    for i in range(1, max_retries+1):
        try:
            if period:
                df = yf.download(symbol, period=period, interval=interval, auto_adjust=auto_adjust, threads=False, progress=False)
            else:
                df = yf.download(symbol, start=start, end=end, interval=interval, auto_adjust=auto_adjust, threads=False, progress=False)
            if not df.empty:
                df = df.reset_index()
            return df
        except Exception as e:
            last_err = e
            time.sleep(pause * i)
    empty = pd.DataFrame()
    empty.attrs["error"] = str(last_err) if last_err else "unknown error"
    return empty

def main():
    ap = argparse.ArgumentParser(description="Colab-friendly Yahoo Finance daily downloader (10y by default)")
    ap.add_argument("--input", required=True, help="CSV with at least 'Symbol' column; optional 'Security Name'")
    ap.add_argument("--outdir", default="yahoo_daily_out", help="Output directory")
    ap.add_argument("--threads", type=int, default=1, help="Parallel threads (kept for CLI compat; not used)")
    ap.add_argument("--adjust", action="store_true", help="Use auto-adjusted prices")
    ap.add_argument("--start", default=None, help="Start date YYYY-MM-DD (overrides period if set)")
    ap.add_argument("--end", default=None, help="End date YYYY-MM-DD")
    ap.add_argument("--period", default="10y", help="Yahoo period string (default 10y). Ignored if --start is set")
    ap.add_argument("--resume", action="store_true", help="Skip symbols that already have per_symbol CSV")
    ap.add_argument("--force", action="store_true", help="Force re-download even if per_symbol exists")
    ap.add_argument("--limit", type=int, default=None, help="Only process first N symbols (debug)")
    ap.add_argument("--logfile", default=None, help="Write logs to this file to reduce notebook stdout")
    ap.add_argument("--sleep", type=float, default=0.5, help="Sleep seconds between symbols to be polite")
    args = ap.parse_args()

    def log(msg: str):
        ts = time.strftime("%H:%M:%S")
        line = f"[{ts}] {msg}"
        if args.logfile:
            with open(args.logfile, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        else:
            print(line, flush=True)

    df_syms = read_symbols(args.input)
    if args.limit:
        df_syms = df_syms.head(args.limit).copy()

    outdir = args.outdir
    perdir = os.path.join(outdir, "per_symbol")
    os.makedirs(perdir, exist_ok=True)

    combined_path = os.path.join(outdir, "combined_daily.csv")
    log_csv = os.path.join(outdir, "download_log.csv")

    logs = []
    processed = 0
    header_written = os.path.exists(combined_path) and os.path.getsize(combined_path) > 0

    # Sequential processing to reduce RAM; each symbol saved immediately
    for idx, row in df_syms.iterrows():
        sym = row["Symbol"]
        name = row["Security Name"]
        safe_sym = "".join([c for c in sym if c.isalnum() or c in ("_", "-", ".")])
        per_csv = os.path.join(perdir, f"{safe_sym}.csv")

        if args.resume and not args.force and os.path.exists(per_csv) and os.path.getsize(per_csv) > 0:
            log(f"Skip existing {sym}")
            processed += 1
            continue

        log(f"Downloading {sym} ({idx+1}/{len(df_syms)})")
        df = safe_download_one(
            symbol=sym,
            period=None if args.start else args.period,
            interval="1d",
            start=args.start,
            end=args.end,
            auto_adjust=args.adjust,
            max_retries=3,
            pause=1.0
        )

        status = "ok"
        msg = ""
        if df.empty:
            status = "empty"
            msg = df.attrs.get("error", "")
            log(f"Empty/failed: {sym} - {msg}")
        else:
            if "Date" not in df.columns and "date" in [c.lower() for c in df.columns]:
                for c in df.columns:
                    if c.lower() == "date":
                        df.rename(columns={c: "Date"}, inplace=True)
                        break
            df["Symbol"] = sym
            df["Security Name"] = name
            df.to_csv(per_csv, index=False)

            mode = "a" if header_written else "w"
            df.to_csv(combined_path, index=False, mode=mode, header=not header_written)
            header_written = True

        logs.append({"Symbol": sym, "Security Name": name, "status": status, "message": msg})
        processed += 1
        time.sleep(max(0.0, args.sleep))

    pd.DataFrame(logs).to_csv(log_csv, index=False)
    log(f"Done. Processed={processed}. Outputs: {combined_path}, {perdir}, {log_csv}")

if __name__ == "__main__":
    main()
