from __future__ import annotations

from typing import Optional, List
import numpy as np
import pandas as pd


def load_price_panel(
    path: str,
    price_col: str = "Close",
    symbol_col: str = "Symbol",
) -> pd.DataFrame:
    """
    Load daily prices from a CSV and return a Date x Symbol panel of prices.

    Expected columns in the CSV:
      - "Date"
      - price_col (default "Close")
      - symbol_col (default "Symbol", can be a single symbol like ATLO)

    Returns
    -------
    prices : pd.DataFrame
        Wide DataFrame with Date index and one column per symbol.
    """
    df = pd.read_csv(path)

    # Parse dates and drop invalid
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])

    # Clean price column
    if price_col not in df.columns:
        raise KeyError(f"Price column '{price_col}' not found in CSV.")

    df[price_col] = pd.to_numeric(df[price_col], errors="coerce")
    df = df.dropna(subset=[price_col])

    df = df.sort_values("Date")

    if symbol_col in df.columns:
        prices = df.pivot(index="Date", columns=symbol_col, values=price_col)
    else:
        # Single asset without symbol column
        prices = df.set_index("Date")[[price_col]]
        prices.columns = ["asset"]

    prices.index.name = "Date"

    return prices

def load_price_panel_from_files(
    paths: List[str],
    price_col: str = "Close",
    symbol_col: str = "Symbol",
) -> pd.DataFrame:
    """
    Load daily prices from multiple CSVs and build a Date x Symbol price panel.
    Each CSV must have Date, price_col, and symbol_col (e.g. one stock per file).
    """
    frames = []
    for p in paths:
        df = pd.read_csv(p)
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df.dropna(subset=["Date"])

        if price_col not in df.columns:
            raise KeyError(f"Price column '{price_col}' not found in file {p}.")
        if symbol_col not in df.columns:
            raise KeyError(f"Symbol column '{symbol_col}' not found in file {p}.")

        df[price_col] = pd.to_numeric(df[price_col], errors="coerce")
        df = df.dropna(subset=[price_col])

        frames.append(df[["Date", symbol_col, price_col]])

    if not frames:
        raise ValueError("No data loaded from given paths.")

    all_df = pd.concat(frames, ignore_index=True)
    all_df = all_df.sort_values("Date")

    prices = all_df.pivot(index="Date", columns=symbol_col, values=price_col)
    prices.index.name = "Date"

    return prices


def to_monthly_prices(
    daily_prices: pd.DataFrame,
    method: str = "last",
) -> pd.DataFrame:
    """
    Resample daily prices to month end prices.

    Parameters
    ----------
    daily_prices : pd.DataFrame
        Date x Symbol daily prices.
    method : {"last", "mean"}
        Aggregation within each month:
          - "last": last available price in the month
          - "mean": average price in the month
    """
    if method == "last":
        monthly = daily_prices.resample("M").last()
    elif method == "mean":
        monthly = daily_prices.resample("M").mean()
    else:
        raise ValueError("method must be 'last' or 'mean'.")

    return monthly


def monthly_log_returns(monthly_prices: pd.DataFrame) -> pd.DataFrame:
    """
    Compute monthly log returns from month end prices.

    r_t = log(P_t / P_{t-1})

    Returns
    -------
    log_ret : pd.DataFrame
        Date x Symbol of monthly log returns.
    """
    log_prices = np.log(monthly_prices)
    log_ret = log_prices.diff()
    return log_ret
