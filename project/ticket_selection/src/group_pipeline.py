# pair_cluster/group_pipeline.py

import pandas as pd

from .config import (
    VOL_DECILES_KEEP,
    BETA_TOL,
    RET_LOOKBACK_YEARS,
    DV_BAND_LOW,
    DV_BAND_HIGH,
    TOP_K_BY_CORR,
    COINT_LOOKBACK_YEARS,
    COINT_MIN_OBS,
    COINT_ALPHA,
)
from .returns_volume import (
    build_price_dict,
    build_common_return_matrix,
    compute_avg_dollar_volume,
)
from .cointegration import find_cointegrated_pairs, build_cluster_dataset

"""
Pipeline xử lý một group (sectorKey, industryKey).
"""


def process_group(sector, industry, df_group):
    """
    Chạy pipeline cho một cặp (sectorKey, industryKey).
    df_group: subset của universe với các cột ticker, vol_decile, beta_spy.
    Trả về df_cluster_coint cuối cùng (hoặc None nếu fail).
    """
    # 1. Lọc volatile mid decile
    sub = df_group[df_group["vol_decile"].isin(VOL_DECILES_KEEP)].copy()
    if sub.shape[0] < 2:
        return None

    # 2. Lọc theo beta gần median
    beta_center = sub["beta_spy"].median()
    mask_beta = sub["beta_spy"].between(beta_center - BETA_TOL,
                                        beta_center + BETA_TOL)
    sub_beta = sub[mask_beta].copy()
    if sub_beta.shape[0] < 2:
        return None

    tickers = sub_beta["ticker"].unique().tolist()

    # 3. Build price data và return matrix
    price_data = build_price_dict(tickers)
    if len(price_data) < 2:
        return None

    df_returns, range_start, range_end = build_common_return_matrix(
        price_data,
        lookback_years=RET_LOOKBACK_YEARS,
    )
    if df_returns is None or df_returns.shape[1] <= 2:
        return None

    # 4. Dollar volume band
    df_dv = compute_avg_dollar_volume(price_data, range_start, range_end)
    if df_dv.empty:
        return None

    median_dv = df_dv["avg_dollar_vol"].median()
    lower = median_dv * DV_BAND_LOW
    upper = median_dv * DV_BAND_HIGH

    dv_band = df_dv[
        (df_dv["avg_dollar_vol"] >= lower) & (df_dv["avg_dollar_vol"] <= upper)
    ]
    band_tickers = set(dv_band["ticker"].tolist())
    if len(band_tickers) < 2:
        return None

    # 5. Correlation và chọn top tickers theo mean corr
    ret_mat = df_returns.drop(columns=["Date"])
    valid_cols = [c for c in ret_mat.columns if c in band_tickers]
    if len(valid_cols) < 2:
        return None

    corr_band = ret_mat[valid_cols].corr()

    mean_corr_per_ticker = {}
    for tk in valid_cols:
        s = corr_band[tk].drop(tk)
        mean_corr_per_ticker[tk] = s.mean()

    top_sorted = sorted(
        mean_corr_per_ticker,
        key=mean_corr_per_ticker.get,
        reverse=True,
    )
    k = min(TOP_K_BY_CORR, len(top_sorted))
    cluster_tickers = top_sorted[:k]

    # 6. Build cluster dataset và cointegration
    df_cluster = build_cluster_dataset(cluster_tickers)
    if df_cluster is None:
        return None

    res_df, good_pairs = find_cointegrated_pairs(
        df_cluster,
        cluster_tickers,
        lookback_years=COINT_LOOKBACK_YEARS,
        min_obs=COINT_MIN_OBS,
        alpha=COINT_ALPHA,
    )

    if not good_pairs:
        return None

    cointegrated_tickers = sorted(
        set([t1 for t1, t2, _ in good_pairs] + [t2 for t1, t2, _ in good_pairs])
    )

    df_cluster_coint = df_cluster[df_cluster["ticker"].isin(cointegrated_tickers)].copy()
    df_cluster_coint = (
        df_cluster_coint.sort_values(["Date", "ticker"]).reset_index(drop=True)
    )

    return df_cluster_coint
