#!/usr/bin/env python3
import argparse
import os
import sys
import time
from typing import Optional, Tuple

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


def safe_download_one(symbol: str,
                      period: Optional[str],
                      interval: str,
                      start: Optional[str],
                      end: Optional[str],
                      auto_adjust: bool,
                      max_retries: int,
                      pause: float) -> pd.DataFrame:
    last_err = None
    for i in range(1, max_retries+1):
        try:
            if period:
                df = yf.download(symbol, period=period, interval=interval,
                                 auto_adjust=auto_adjust, threads=False, progress=False)
            else:
                df = yf.download(symbol, start=start, end=end, interval=interval,
                                 auto_adjust=auto_adjust, threads=False, progress=False)
            if not df.empty:
                df = df.reset_index()
            return df
        except Exception as e:
            last_err = e
            time.sleep(pause * i)
    empty = pd.DataFrame()
    empty.attrs["error"] = str(last_err) if last_err else "unknown error"
    return empty


# ---------- history filter helpers ----------

def _span_years_and_rows(df: pd.DataFrame, date_col: str = "Date") -> Tuple[float, int]:
    """Return (span_years, n_rows) for a dataframe that has a datetime index or Date column."""
    if df.empty:
        return 0.0, 0
    if date_col in df.columns:
        ds = pd.to_datetime(df[date_col])
    else:
        # yfinance .history returns Date index; our downloads reset_index already
        ds = pd.to_datetime(df.index)
    d0 = ds.min()
    d1 = ds.max()
    span_days = (d1 - d0).days if pd.notna(d0) and pd.notna(d1) else 0
    return span_days / 365.25, len(df)


def has_enough_history_pre(symbol: str, min_years: float, *, monthly_points_floor: int = 8) -> Tuple[bool, str]:
    """
    Lightweight probe: request monthly bars for last min_years and check earliest date span.
    Also guard by a very small floor on returned rows to catch dead tickers.
    """
    try:
        dfm = yf.download(symbol, period=f"{int(max(1, round(min_years)))}y",
                          interval="1mo", auto_adjust=False, threads=False, progress=False)
        if dfm.empty:
            return False, "no monthly data in probe"
        dfm = dfm.reset_index()
        span_years, n_rows = _span_years_and_rows(dfm, "Date" if "Date" in dfm.columns else dfm.columns[0])
        # Require span close to requested min_years and enough monthly points
        # Allow 5 percent tolerance for holidays and listing day offsets
        ok_span = span_years >= min_years * 0.95
        ok_rows = n_rows >= max(int(min_years * 12 * 0.8), monthly_points_floor)
        if ok_span and ok_rows:
            return True, f"probe ok: span={span_years:.2f}y rows={n_rows}"
        return False, f"probe short: span={span_years:.2f}y rows={n_rows}"
    except Exception as e:
        return False, f"probe error: {e}"


def passes_post_filter(df_daily: pd.DataFrame, min_years: float, min_rows: int) -> Tuple[bool, str]:
    span_years, n_rows = _span_years_and_rows(df_daily, "Date" if "Date" in df_daily.columns else df_daily.columns[0])
    # trading days per year roughly 252; pick a conservative floor if user passes min_rows=0
    floors = []
    if min_years > 0:
        floors.append(int(min_years * 180))  # tolerant floor for partial suspensions
    if min_rows > 0:
        floors.append(int(min_rows))
    row_floor = max(floors) if floors else 0
    ok_span = span_years >= min_years * 0.95
    ok_rows = n_rows >= row_floor
    if ok_span and ok_rows:
        return True, f"post ok: span={span_years:.2f}y rows={n_rows} floor={row_floor}"
    return False, f"post short: span={span_years:.2f}y rows={n_rows} floor={row_floor}"


# ---------- main ----------

def main():
    ap = argparse.ArgumentParser(description="Colab-friendly Yahoo Finance daily downloader with 10y filter")
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

    # new filter options
    ap.add_argument("--filter", choices=["off", "pre", "post"], default="post",
                    help="Filter tickers that lack enough history: off or pre or post")
    ap.add_argument("--min-years", type=float, default=10.0, help="Minimum span in years to accept")
    ap.add_argument("--min-rows", type=int, default=2000,
                    help="Minimum daily rows to accept in post filter. Set 0 to disable row floor")
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

    # Sequential processing
    for idx, row in df_syms.iterrows():
        sym = row["Symbol"]
        name = row["Security Name"]
        safe_sym = "".join([c for c in sym if c.isalnum() or c in ("_", "-", ".")])
        per_csv = os.path.join(perdir, f"{safe_sym}.csv")

        if args.resume and not args.force and os.path.exists(per_csv) and os.path.getsize(per_csv) > 0:
            log(f"Skip existing {sym}")
            processed += 1
            continue

        # optional pre filter
        if args.filter == "pre" and not args.start:
            ok, reason = has_enough_history_pre(sym, args.min_years)
            if not ok:
                log(f"Pre filter drop {sym}: {reason}")
                logs.append({"Symbol": sym, "Security Name": name, "status": "short_history_pre", "message": reason})
                processed += 1
                time.sleep(max(0.0, args.sleep))
                continue
            else:
                log(f"Pre filter pass {sym}: {reason}")

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
        wrote = False
        if df.empty:
            status = "empty"
            msg = df.attrs.get("error", "")
            log(f"Empty or failed: {sym} - {msg}")
        else:
            # fix date column name if needed
            if "Date" not in df.columns and "date" in [c.lower() for c in df.columns]:
                for c in df.columns:
                    if c.lower() == "date":
                        df.rename(columns={c: "Date"}, inplace=True)
                        break

            # optional post filter on the downloaded daily df
            if args.filter == "post":
                ok_post, reason_post = passes_post_filter(df, args.min_years, args.min_rows)
                if not ok_post:
                    status = "short_history_post"
                    msg = reason_post
                    log(f"Post filter drop {sym}: {reason_post}")
                else:
                    log(f"Post filter pass {sym}: {reason_post}")

            if status == "ok":
                df["Symbol"] = sym
                df["Security Name"] = name

                # write per symbol
                df.to_csv(per_csv, index=False)
                wrote = True

                # append to combined
                mode = "a" if header_written else "w"
                df.to_csv(combined_path, index=False, mode=mode, header=not header_written)
                header_written = True

        logs.append({"Symbol": sym, "Security Name": name, "status": status, "message": msg})
        processed += 1
        time.sleep(max(0.0, args.sleep))

    pd.DataFrame(logs).to_csv(log_csv, index=False)
    print(f"Done. Processed={processed}. Outputs: {combined_path}, {perdir}, {log_csv}")


if __name__ == "__main__":
    main()
