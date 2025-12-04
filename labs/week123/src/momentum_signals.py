from __future__ import annotations

from typing import Tuple

import numpy as np
import pandas as pd


def compute_momentum_scores(
    log_returns: pd.DataFrame,
    lookback_months: int = 1,
    skip_recent_months: int = 0,
) -> pd.DataFrame:
    """
    Compute cross sectional momentum scores from monthly log returns.

    Momentum score at time t is the sum of log returns over a window:
      - lookback_months: how many months of history to use
      - skip_recent_months: how many most recent months to skip
        (for example, classical 12-1 momentum uses lookback=12, skip_recent=1)

    Parameters
    ----------
    log_returns : pd.DataFrame
        Date x Symbol monthly log returns.
    lookback_months : int
        Window length in months.
    skip_recent_months : int
        Number of recent months to exclude.

    Returns
    -------
    scores : pd.DataFrame
        Date x Symbol momentum scores.
    """
    if lookback_months < 1:
        raise ValueError("lookback_months must be at least 1.")
    if skip_recent_months < 0:
        raise ValueError("skip_recent_months must be non negative.")

    # Shift to skip recent months if desired
    shifted = log_returns.shift(skip_recent_months)

    # Rolling sum over the lookback window
    scores = shifted.rolling(window=lookback_months, min_periods=lookback_months).sum()
    return scores


def build_long_short_weights(
    scores: pd.DataFrame,
    n_long: int,
    n_short: int,
    long_capital: float = 0.5,
    short_capital: float = 0.5,
) -> pd.DataFrame:
    """
    Build equal weighted long short portfolio weights from momentum scores.

    Each rebalance date:
      - Rank stocks by momentum score
      - Long the top n_long names
      - Short the bottom n_short names
      - Long leg total weight = +long_capital (default 0.5)
      - Short leg total weight = -short_capital (default 0.5)

    Parameters
    ----------
    scores : pd.DataFrame
        Date x Symbol momentum scores.
    n_long : int
        Number of stocks in the long leg.
    n_short : int
        Number of stocks in the short leg.
    long_capital : float
        Total positive weight assigned to long leg.
    short_capital : float
        Total negative weight assigned to short leg (absolute value).

    Returns
    -------
    weights : pd.DataFrame
        Date x Symbol of portfolio weights that will be used
        for the *next* period's returns after a shift.
    """
    if n_long <= 0 or n_short <= 0:
        raise ValueError("n_long and n_short must be positive integers.")

    weights = pd.DataFrame(0.0, index=scores.index, columns=scores.columns)

    for date, row in scores.iterrows():
        row = row.dropna()
        if row.empty:
            continue

        # If there are fewer available stocks than desired, scale n_long/n_short down
        available = len(row)
        n_long_eff = min(n_long, available // 2)
        n_short_eff = min(n_short, available // 2)

        if n_long_eff == 0 or n_short_eff == 0:
            continue

        sorted_idx = row.sort_values(ascending=False).index
        long_idx = sorted_idx[:n_long_eff]
        short_idx = sorted_idx[-n_short_eff:]

        long_w = long_capital / float(n_long_eff)
        short_w = -short_capital / float(n_short_eff)

        weights.loc[date, long_idx] = long_w
        weights.loc[date, short_idx] = short_w

    return weights


def split_long_short_returns(
    weights: pd.DataFrame,
    simple_returns: pd.DataFrame,
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Given weights and simple returns, compute long, short, and total portfolio returns.

    Note: weights are assumed to be the lagged weights already aligned with returns.

    Returns
    -------
    long_ret : pd.Series
        Average return of the long leg.
    short_ret : pd.Series
        Average return of the short leg (asset return, not profit).
    portfolio_ret : pd.Series
        Return of the combined portfolio, equal to:
            0.5 * long_leg_profit + 0.5 * short_leg_profit
        when long and short capital are both 0.5.
    """
    # Long and short masks
    long_w = weights.clip(lower=0.0)
    short_w = weights.clip(upper=0.0)

    long_total = long_w.sum(axis=1)
    short_total = -short_w.sum(axis=1)

    # Avoid division by zero
    long_total = long_total.replace(0.0, np.nan)
    short_total = short_total.replace(0.0, np.nan)

    # Average asset returns in each leg
    long_ret = (long_w * simple_returns).sum(axis=1) / long_total
    short_ret = (short_w * simple_returns).sum(axis=1) / short_total

    # Short leg profit is minus the asset return
    long_profit = long_ret
    short_profit = -short_ret

    # Final portfolio return is average of long and short leg profits
    portfolio_ret = 0.5 * long_profit + 0.5 * short_profit

    return long_ret, short_ret, portfolio_ret
