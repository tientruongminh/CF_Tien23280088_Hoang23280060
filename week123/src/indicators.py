from __future__ import annotations

import pandas as pd


def sma(series: pd.Series, window: int, min_periods: int | None = None) -> pd.Series:
    """
    Simple moving average over a rolling window.
    """
    if min_periods is None:
        min_periods = window
    return series.rolling(window=window, min_periods=min_periods).mean()


def rolling_std(series: pd.Series, window: int, min_periods: int | None = None) -> pd.Series:
    """
    Rolling standard deviation over a window.
    """
    if min_periods is None:
        min_periods = window
    return series.rolling(window=window, min_periods=min_periods).std(ddof=1)


def bollinger_bands(
    series: pd.Series,
    window: int = 20,
    num_std: float = 2.0,
    min_periods: int | None = None,
) -> pd.DataFrame:
    """
    Compute Bollinger Bands for a price series.

    Returns a DataFrame with columns:
      - sma
      - bb_upper
      - bb_lower
    """
    ma = sma(series, window=window, min_periods=min_periods)
    sigma = rolling_std(series, window=window, min_periods=min_periods)

    bb_upper = ma + num_std * sigma
    bb_lower = ma - num_std * sigma

    out = pd.DataFrame(
        {
            "sma": ma,
            "bb_upper": bb_upper,
            "bb_lower": bb_lower,
        }
    )
    return out
