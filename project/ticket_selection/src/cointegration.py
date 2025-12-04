# pair_cluster/cointegration.py

from itertools import combinations

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import coint

from config import COINT_LOOKBACK_YEARS, COINT_MIN_OBS, COINT_ALPHA
from data_loader import load_ohlcv

"""
Test cointegration cho một cụm mã.
"""


def find_cointegrated_pairs(df_cluster, tickers,
                            lookback_years=COINT_LOOKBACK_YEARS,
                            min_obs=COINT_MIN_OBS,
                            alpha=COINT_ALPHA):
    df_cluster = df_cluster.copy()
    df_cluster["Date"] = pd.to_datetime(df_cluster["Date"])

    max_date = df_cluster["Date"].max()
    start_cut = max_date - pd.Timedelta(days=365 * lookback_years)
    df_win = df_cluster[df_cluster["Date"] >= start_cut].copy()

    results = []
    good_pairs = []

    for t1, t2 in combinations(tickers, 2):
        s1 = df_win[df_win["ticker"] == t1][["Date", "Close"]]
        s2 = df_win[df_win["ticker"] == t2][["Date", "Close"]]

        merged = pd.merge(s1, s2, on="Date", how="inner", suffixes=("_1", "_2"))
        merged = merged.dropna()
        if merged.shape[0] < min_obs:
            continue

        y1 = np.log(merged["Close_1"].values)
        y2 = np.log(merged["Close_2"].values)

        try:
            stat, pvalue, crit = coint(y1, y2)
        except Exception as e:
            print(f"[warn] coint error {t1}-{t2}: {e}")
            continue

        results.append(
            {
                "ticker1": t1,
                "ticker2": t2,
                "pvalue": pvalue,
                "stat": stat,
            }
        )

        if pvalue < alpha:
            good_pairs.append((t1, t2, pvalue))

    res_df = pd.DataFrame(results).sort_values("pvalue") if results else pd.DataFrame()
    return res_df, good_pairs


def build_cluster_dataset(tickers):
    dfs = []
    for tk in tickers:
        df_tk = load_ohlcv(tk)
        if df_tk is None:
            continue
        df_tk = df_tk.copy()
        df_tk["ticker"] = tk
        dfs.append(df_tk)

    if not dfs:
        return None

    df_all = pd.concat(dfs, ignore_index=True)
    df_all = df_all.sort_values(["Date", "ticker"]).reset_index(drop=True)
    return df_all[["Date", "ticker", "Open", "High", "Low", "Close", "Volume"]]
