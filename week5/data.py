# data.py

from typing import Tuple
import numpy as np
import pandas as pd


def load_single_stock_csv(csv_path: str) -> pd.DataFrame:
    """
    Load 1 file CSV với các cột:
      Date, Open, High, Low, Close, Volume, Symbol, Security Name

    Chuẩn hóa index về Date và tính cột Close numeric.
    """
    df = pd.read_csv(csv_path)

    cols_l = {c.lower().strip(): c for c in df.columns}

    # Date column
    if "date" not in cols_l:
        raise ValueError("CSV must contain a 'Date' column")
    date_col = cols_l["date"]

    # Close column
    close_col = None
    for k in ("close", "adj close", "adj_close"):
        if k in cols_l:
            close_col = cols_l[k]
            break
    if close_col is None:
        raise ValueError("CSV must contain a 'Close' or 'Adj Close' column")

    df[date_col] = pd.to_datetime(df[date_col])
    df = df.sort_values(date_col).set_index(date_col)

    df[close_col] = pd.to_numeric(df[close_col], errors="coerce")
    df["Close"] = df[close_col]

    df = df.dropna(subset=["Close"])
    return df


def add_log_return(df: pd.DataFrame) -> pd.DataFrame:
    """
    Thêm cột log_return = ln(P_t / P_{t-1}).
    """
    df = df.copy()
    df["log_return"] = np.log(df["Close"] / df["Close"].shift(1))
    return df


def add_bollinger_bands(
    df: pd.DataFrame,
    window: int = 20,
    n_std: float = 2.0,
) -> pd.DataFrame:
    """
    Thêm Bollinger Bands:
      bb_mid   = SMA(window)
      bb_upper = bb_mid + n_std * rolling_std
      bb_lower = bb_mid - n_std * rolling_std
    """
    df = df.copy()

    rolling_mean = df["Close"].rolling(window).mean()
    rolling_std = df["Close"].rolling(window).std()

    df["bb_mid"] = rolling_mean
    df["bb_upper"] = rolling_mean + n_std * rolling_std
    df["bb_lower"] = rolling_mean - n_std * rolling_std

    return df


def add_volatility_features(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """
    Thêm:
      - log_return
      - rolling_vol (std của log_return)
      - Bollinger Bands
    """
    df = add_log_return(df)
    df["rolling_vol"] = df["log_return"].rolling(window).std()
    df = add_bollinger_bands(df, window=window, n_std=2.0)
    return df
