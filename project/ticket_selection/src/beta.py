# pair_cluster/beta.py

import numpy as np
import pandas as pd

from .config import BETA_MIN_OBS
from .data_loader import load_ohlcv
from .data_loader import compute_spy_returns

"""
Tính beta với SPY cho toàn universe.
"""


def compute_beta_vs_spy(ticker, spy_ret, min_obs=BETA_MIN_OBS):
    df = load_ohlcv(ticker)
    if df is None:
        return None

    start_date = spy_ret["Date"].min()
    end_date = spy_ret["Date"].max()

    df = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)].copy()
    df["r_i"] = np.log(df["Close"]).diff()
    df_ret = df[["Date", "r_i"]].dropna()

    merged = pd.merge(df_ret, spy_ret, on="Date", how="inner")
    if merged.shape[0] < min_obs:
        return None

    ri = merged["r_i"].values
    rm = merged["r_m"].values

    cov_im = np.cov(ri, rm, ddof=1)[0, 1]
    var_m = np.var(rm, ddof=1)
    if var_m == 0:
        return None

    beta = cov_im / var_m
    return {"ticker": ticker, "beta_spy": beta}


def compute_all_betas(tickers, spy_ret):
    rows = []
    for tk in tickers:
        res = compute_beta_vs_spy(tk, spy_ret)
        if res is not None:
            rows.append(res)
    df_beta = pd.DataFrame(rows)
    return df_beta
