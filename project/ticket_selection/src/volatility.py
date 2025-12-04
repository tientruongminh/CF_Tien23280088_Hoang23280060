# pair_cluster/volatility.py

import numpy as np
import pandas as pd

from config import VOL_MIN_OBS, VOL_LOOKBACK_DAYS
from data_loader import load_ohlcv

"""
Tính volatility 1 năm và decile cho toàn universe.
"""


def compute_1y_vol(ticker, min_obs=VOL_MIN_OBS):
    """
    Tính annualized volatility 1 năm gần nhất trên log return Close.
    Dùng tối đa VOL_LOOKBACK_DAYS phiên gần nhất.
    """
    df = load_ohlcv(ticker)
    if df is None:
        return None

    df_recent = df.sort_values("Date").tail(VOL_LOOKBACK_DAYS)
    prices = df_recent["Close"].astype(float)
    rets = np.log(prices).diff().dropna()

    if rets.shape[0] < min_obs:
        return None

    vol_1y = rets.std() * np.sqrt(252.0)
    return {"ticker": ticker, "vol_1y": vol_1y}


def compute_all_vols(tickers):
    rows = []
    for tk in tickers:
        res = compute_1y_vol(tk)
        if res is not None:
            rows.append(res)
    df_vol = pd.DataFrame(rows)
    df_vol = df_vol.replace([np.inf, -np.inf], np.nan).dropna(subset=["vol_1y"])
    df_vol = df_vol[df_vol["vol_1y"] > 0]
    df_vol["vol_decile"] = pd.qcut(df_vol["vol_1y"], 10, labels=False) + 1
    return df_vol
