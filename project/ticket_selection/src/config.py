# pair_cluster/config.py

import os

"""
Config và tham số toàn bộ pipeline.
"""

# Thư mục chứa các file price volume per symbol
DATA_DIR = "/kaggle/input/computational-finance/yfinance/yfinance/per_symbol"

# File SPY riêng
SPY_PATH = "/kaggle/input/computational-finance/SPY.csv"

# File sector industry (nếu đã tạo trước)
SECTOR_FILE = "sector_industry.csv"

# Folder output cuối cùng
OUTPUT_DIR = "clusters"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Ngưỡng và tham số
MIN_GROUP_SIZE = 50          # số mã tối thiểu cho một cặp sector industry
VOL_MIN_OBS = 200             # số quan sát tối thiểu để tính vol 1y
VOL_LOOKBACK_DAYS = 252       # số ngày gần nhất để tính vol 1y
VOL_DECILES_KEEP = [4, 5, 6]  # dải volatility giữ lại

BETA_MIN_OBS = 200
BETA_TOL = 0.2                # beta gần median ± 0.2

RET_LOOKBACK_YEARS = 3        # số năm lookback cho return, corr, dollar vol
RET_MIN_OBS = 200

DV_BAND_LOW = 0.5             # chọn mã có avg dollar volume trong [0.5, 2] * median
DV_BAND_HIGH = 2.0

TOP_K_BY_CORR = 10            # chọn tối đa 10 mã có mean corr cao nhất trong band dv

COINT_LOOKBACK_YEARS = 3
COINT_MIN_OBS = 200
COINT_ALPHA = 0.05            # pvalue < 0.05 thì coi là cointegrated
