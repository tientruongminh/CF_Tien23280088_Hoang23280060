# pair_cluster/data_loader.py

import os
import numpy as np
import pandas as pd

from config import DATA_DIR, SPY_PATH, VOL_LOOKBACK_DAYS

"""
Các hàm đọc dữ liệu cơ bản:
- list_tickers
- load_ohlcv cho từng mã
- load_spy, compute_spy_returns
"""


def list_tickers(data_dir=DATA_DIR):
    return sorted(
        [name.split(".")[0] for name in os.listdir(data_dir) if name.endswith(".csv")]
    )


def load_ohlcv(ticker, data_dir=DATA_DIR):
    """
    Đọc file 1 ticker, trả về DataFrame với cột:
      Date (datetime), Open, High, Low, Close, Volume (numeric)
    Tự xử lý một số kiểu header noise (dòng đầu chứa ticker, v.v.).
    """
    path = os.path.join(data_dir, f"{ticker}.csv")
    if not os.path.exists(path):
        print(f"[warn] missing file: {path}")
        return None

    try:
        df = pd.read_csv(path)
    except Exception as e:
        print(f"[warn] read error {ticker}: {e}")
        return None

    # Cột ngày
    if "Date" in df.columns:
        date_col = "Date"
    elif "date" in df.columns:
        date_col = "date"
    else:
        # fallback kiểu file SPY dạng Price + dòng Date (ít gặp với per_symbol)
        if "Price" in df.columns and str(df.loc[1, "Price"]).lower() == "date":
            df = df.iloc[2:].copy()
            df = df.rename(columns={"Price": "Date"})
            date_col = "Date"
        else:
            print(f"[warn] no date col {ticker}")
            return None

    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col])
    if df.empty:
        print(f"[warn] empty after date parse {ticker}")
        return None

    df = df.sort_values(date_col)

    # Map cột
    col_map = {"Open": None, "High": None, "Low": None, "Close": None, "Volume": None}

    for col in ["Open", "open"]:
        if col in df.columns:
            col_map["Open"] = col
            break
    for col in ["High", "high"]:
        if col in df.columns:
            col_map["High"] = col
            break
    for col in ["Low", "low"]:
        if col in df.columns:
            col_map["Low"] = col
            break
    for col in ["Adj Close", "Adj_Close", "adj_close", "Close", "close"]:
        if col in df.columns:
            col_map["Close"] = col
            break
    for col in ["Volume", "volume", "Vol", "vol"]:
        if col in df.columns:
            col_map["Volume"] = col
            break

    if col_map["Close"] is None or col_map["Volume"] is None:
        print(f"[warn] missing Close or Volume for {ticker}")
        return None

    # Convert numeric
    for key, col in col_map.items():
        if col is not None:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=[col_map["Close"], col_map["Volume"]])
    if df.empty:
        print(f"[warn] empty after numeric {ticker}")
        return None

    out = pd.DataFrame(
        {
            "Date": df[date_col],
            "Open": df[col_map["Open"]] if col_map["Open"] is not None else np.nan,
            "High": df[col_map["High"]] if col_map["High"] is not None else np.nan,
            "Low": df[col_map["Low"]] if col_map["Low"] is not None else np.nan,
            "Close": df[col_map["Close"]],
            "Volume": df[col_map["Volume"]],
        }
    )

    return out


def load_spy(spy_path=SPY_PATH):
    """
    Load SPY với các format tương tự file riêng:
    cột Price, Close, High, Low, Open, Volume với hai dòng đầu là header noise.
    """
    df = pd.read_csv(spy_path)

    if "Date" in df.columns or "date" in df.columns:
        date_col = "Date" if "Date" in df.columns else "date"
    elif "Price" in df.columns and str(df.loc[1, "Price"]).lower() == "date":
        df = df.iloc[2:].copy()
        df = df.rename(columns={"Price": "Date"})
        date_col = "Date"
    else:
        return None

    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = df.dropna(subset=[date_col])
    df = df.sort_values(date_col)

    # Chọn cột giá
    price_col = None
    for col in ["Adj Close", "Adj_Close", "adj_close", "Close", "close"]:
        if col in df.columns:
            price_col = col
            break
    if price_col is None:
        return None

    df[price_col] = pd.to_numeric(df[price_col], errors="coerce")
    df = df.dropna(subset=[price_col])
    if df.empty:
        return None

    df = df[[date_col, price_col]].rename(columns={date_col: "Date", price_col: "Close"})
    return df


def compute_spy_returns(spy_path=SPY_PATH, lookback_days=VOL_LOOKBACK_DAYS):
    df_spy = load_spy(spy_path)
    if df_spy is None or df_spy.empty:
        raise RuntimeError("Không load được SPY")

    df_spy = df_spy.sort_values("Date").tail(lookback_days).copy()
    df_spy["r_m"] = np.log(df_spy["Close"]).diff()
    spy_ret = df_spy[["Date", "r_m"]].dropna().reset_index(drop=True)
    return spy_ret
