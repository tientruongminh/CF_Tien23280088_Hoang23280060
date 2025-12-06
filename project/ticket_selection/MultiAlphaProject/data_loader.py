import pandas as pd
import os

def load_data(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing file: {path}")
    df = pd.read_csv(path)
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values(["Date", "ticker"])
    df_close = df.pivot(index="Date", columns="ticker", values="Close")
    return df_close.fillna(method='ffill').fillna(method='bfill')