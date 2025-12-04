# pair_cluster/returns_volume.py

from functools import reduce

import numpy as np
import pandas as pd

from .config import RET_LOOKBACK_YEARS
from .data_loader import load_ohlcv

"""
Xây return matrix, tính average dollar volume.
"""


def build_price_dict(tickers):
    price_data = {}
    for tk in tickers:
        df = load_ohlcv(tk)
        if df is not None:
            price_data[tk] = df
    return price_data


def build_common_return_matrix(price_data, lookback_years=RET_LOOKBACK_YEARS):
    # Common date range
    start_dates = [df["Date"].min() for df in price_data.values()]
    end_dates = [df["Date"].max() for df in price_data.values()]
    latest_start = max(start_dates)
    earliest_end = min(end_dates)

    three_years = pd.Timestamp(earliest_end) - pd.Timedelta(days=365 * lookback_years)
    range_start = max(latest_start, three_years)
    range_end = earliest_end

    ret_list = []
    for tk, df in price_data.items():
        df_win = df[(df["Date"] >= range_start) & (df["Date"] <= range_end)].copy()
        df_win["r"] = np.log(df_win["Close"]).diff()
        df_ret = df_win[["Date", "r"]].dropna()
        df_ret = df_ret.rename(columns={"r": tk})
        ret_list.append(df_ret)

    if not ret_list:
        return None, None, None

    df_returns = reduce(
        lambda left, right: pd.merge(left, right, on="Date", how="inner"),
        ret_list,
    )

    df_returns = df_returns.sort_values("Date").reset_index(drop=True)
    return df_returns, range_start, range_end


def compute_avg_dollar_volume(price_data, range_start, range_end):
    rows = []
    for tk, df in price_data.items():
        df_win = df[(df["Date"] >= range_start) & (df["Date"] <= range_end)].copy()
        if df_win.empty:
            continue
        df_win["dollar_vol"] = df_win["Close"] * df_win["Volume"]
        avg_dv = df_win["dollar_vol"].mean()
        rows.append({"ticker": tk, "avg_dollar_vol": avg_dv})
    df_dv = pd.DataFrame(rows).dropna(subset=["avg_dollar_vol"])
    return df_dv
