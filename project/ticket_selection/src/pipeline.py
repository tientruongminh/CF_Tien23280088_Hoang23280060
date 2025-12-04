# pair_cluster/pipeline.py

import os

from config import (
    DATA_DIR,
    SPY_PATH,
    SECTOR_FILE,
    OUTPUT_DIR,
    MIN_GROUP_SIZE,
)
from data_loader import list_tickers, compute_spy_returns
from sector_industry import get_sector_industry
from volatility import compute_all_vols
from beta import compute_all_betas
from group_pipeline import process_group

"""
Full pair trading cluster pipeline trên toàn universe:

1) Lấy danh sách ticker từ folder per_symbol (price volume).
2) Lấy sectorKey, industryKey bằng yahooquery (hoặc đọc từ sector_industry.csv nếu đã có).
3) Tính volatility 1 năm cho toàn bộ universe, chia decile.
4) Tính beta với SPY cho toàn bộ universe.
5) Với từng cặp (sectorKey, industryKey) có >= MIN_GROUP_SIZE:
   - Lọc theo volatility decile (mid vol).
   - Lọc theo beta gần nhau (median ± BETA_TOL).
   - Tính return 3 năm, average dollar volume và chọn dv band.
   - Chọn top tickers theo mean pairwise correlation trong band.
   - Test cointegration tất cả cặp trong cụm con, lấy các mã có pvalue < COINT_ALPHA.
   - Xuất file csv cuối cùng với OHLCV sạch cho các mã cointegrated.

Output: một folder OUTPUT_DIR chứa các file:
  cluster_{sectorKey}_{industryKey}.csv
"""


def run_full_pipeline():
    # 1. Universe tickers
    tickers = list_tickers(DATA_DIR)
    print("Total tickers from per_symbol:", len(tickers))

    # 2. Sector industry
    df_sector = get_sector_industry(tickers, sector_file=SECTOR_FILE)

    # 3. Volatility 1y
    print("Computing 1y volatility...")
    df_vol = compute_all_vols(tickers)

    # 4. Beta vs SPY
    print("Computing beta vs SPY...")
    spy_ret = compute_spy_returns(SPY_PATH)
    df_beta = compute_all_betas(tickers, spy_ret)

    # 5. Universe merged
    universe = (
        df_sector.merge(df_vol, on="ticker", how="inner")
        .merge(df_beta, on="ticker", how="inner")
    )

    print("Universe after merge:", universe.shape)

    # 6. Group by sectorKey, industryKey
    grouped = universe.groupby(["sectorKey", "industryKey"])

    for (sector, industry), df_group in grouped:
        if df_group.shape[0] < MIN_GROUP_SIZE:
            continue

        print(
            f"\nProcessing group: sector={sector}, industry={industry}, "
            f"n={df_group.shape[0]}"
        )

        df_cluster_coint = process_group(sector, industry, df_group)

        if df_cluster_coint is None or df_cluster_coint.empty:
            print("  No final cluster for this group.")
            continue

        fname = f"cluster_{sector}_{industry}.csv"
        fname = fname.replace(" ", "_")
        out_path = os.path.join(OUTPUT_DIR, fname)
        df_cluster_coint.to_csv(out_path, index=False)
        print(
            f"  Saved final cluster for {sector}/{industry} "
            f"with {df_cluster_coint['ticker'].nunique()} tickers "
            f"to {out_path}"
        )


if __name__ == "__main__":
    run_full_pipeline()
