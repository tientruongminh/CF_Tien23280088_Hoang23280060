from __future__ import annotations

from typing import Optional
import pandas as pd


def load_price_data(path: str, symbol: Optional[str] = None) -> pd.DataFrame:
    """
    Load daily price data from a CSV file.

    The function expects at least the following columns:
      - "Date"
      - "Open"
      - "High"
      - "Low"
      - "Close"
      - "Volume"

    It will:
      - parse the Date column to datetime
      - convert price and volume columns to numeric
      - drop rows with invalid dates or missing Close
      - optionally filter by symbol
      - sort by Date and set Date as index
    """
    df = pd.read_csv(path)

    # Parse dates; drop rows where date parsing fails
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"])

    # Convert numeric columns
    numeric_cols = ["Open", "High", "Low", "Close", "Volume"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Drop rows without Close price
    df = df.dropna(subset=["Close"])

    # Optional symbol filter
    if symbol is not None and "Symbol" in df.columns:
        df = df[df["Symbol"] == symbol]

    # Sort by date and set as index
    df = df.sort_values("Date").set_index("Date")
    df.index.name = "Date"

    return df
