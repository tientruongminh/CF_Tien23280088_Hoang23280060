import numpy as np
import pandas as pd


def load_single_stock_csv(csv_path: str) -> pd.DataFrame:
    """
    Load một file CSV dạng:

    Date,Close,High,Low,Open,Volume,Symbol,Security Name
    ,ATLO,ATLO,ATLO,ATLO,ATLO,,
    2015 11 09,...

    Bỏ dòng thứ hai, dùng Date làm index, sort theo thời gian,
    tạo cột log_return.
    """
    # Bỏ dòng thứ hai chứa ATLO,ATLO,...
    df = pd.read_csv(csv_path, skiprows=[1])

    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date").set_index("Date")

    # Đảm bảo các cột numeric
    for col in ["Close", "Open", "High", "Low", "Volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["Close"])
    df["log_return"] = np.log(df["Close"]).diff()
    df = df.dropna(subset=["log_return"])

    return df


def add_volatility_features(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """
    Thêm rolling volatility và Bollinger Bands.
    """
    df = df.copy()
    df["rolling_vol"] = df["log_return"].rolling(window=window).std()
    df["bb_ma"] = df["Close"].rolling(window=window).mean()
    df["bb_std"] = df["Close"].rolling(window=window).std()
    df["bb_upper"] = df["bb_ma"] + 2 * df["bb_std"]
    df["bb_lower"] = df["bb_ma"] - 2 * df["bb_std"]
    return df
