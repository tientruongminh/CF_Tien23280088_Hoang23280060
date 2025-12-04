from __future__ import annotations

import pandas as pd

from indicators import bollinger_bands


def bollinger_reversion_signals(
    df: pd.DataFrame,
    price_col: str = "Close",
    window: int = 20,
    num_std: float = 2.0,
) -> pd.DataFrame:
    """
    Add Bollinger Bands and trading signals to a price DataFrame.

    Rules:
      - Buy signal (signal = +1) when price moves up into the band
        after being below the lower band.
      - Sell signal (signal = -1) when price moves down into the band
        after being above the upper band.

    Signals are based on the column given by price_col.
    """
    if price_col not in df.columns:
        raise KeyError(f"Price column '{price_col}' not found in DataFrame.")

    price = df[price_col]

    bb = bollinger_bands(price, window=window, num_std=num_std)
    out = df.copy()
    out[["sma", "bb_upper", "bb_lower"]] = bb[["sma", "bb_upper", "bb_lower"]]

    # Inside band today
    inside_today = (price >= out["bb_lower"]) & (price <= out["bb_upper"])

    # Yesterday price relative to bands
    below_lower_yesterday = price.shift(1) < out["bb_lower"].shift(1)
    above_upper_yesterday = price.shift(1) > out["bb_upper"].shift(1)

    # Simple inflection filters
    rising_today = price > price.shift(1)
    falling_today = price < price.shift(1)

    buy_cond = below_lower_yesterday & inside_today & rising_today
    sell_cond = above_upper_yesterday & inside_today & falling_today

    signal = pd.Series(0, index=out.index, dtype=int)
    signal = signal.mask(buy_cond, 1)
    signal = signal.mask(sell_cond, -1)

    out["signal"] = signal

    return out
