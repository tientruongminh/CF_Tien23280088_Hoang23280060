# pair_cluster/sector_industry.py

import os
import pandas as pd

from .config import SECTOR_FILE

"""
Lấy bảng sectorKey, industryKey cho toàn bộ tickers.
"""

try:
    from yahooquery import Ticker as YQTicker
except ImportError:
    YQTicker = None


def get_sector_industry(tickers, sector_file=SECTOR_FILE):
    """
    Lấy bảng sectorKey, industryKey cho toàn bộ tickers.
    Nếu đã có sector_file thì đọc, nếu chưa có và YQTicker khả dụng thì fetch từ yahooquery.
    """
    if os.path.exists(sector_file):
        df_sector = pd.read_csv(sector_file)
        return df_sector

    if YQTicker is None:
        raise RuntimeError(
            "sector_industry.csv không tồn tại và yahooquery không khả dụng. "
            "Cài đặt yahooquery hoặc tạo sector_industry.csv trước."
        )

    t = YQTicker(tickers)
    profiles = t.asset_profile

    rows = []
    for symbol, info in profiles.items():
        if not isinstance(info, dict):
            continue
        rows.append(
            {
                "ticker": symbol,
                "sectorKey": info.get("sectorKey"),
                "industryKey": info.get("industryKey"),
            }
        )

    df_sector = pd.DataFrame(rows)
    df_sector = df_sector[~df_sector["sectorKey"].isna()]
    df_sector.to_csv(sector_file, index=False)
    return df_sector
