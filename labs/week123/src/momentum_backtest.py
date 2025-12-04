from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any

import numpy as np
import pandas as pd

from momentum_signals import (
    compute_momentum_scores,
    build_long_short_weights,
    split_long_short_returns,
)


@dataclass
class MomentumBacktestResult:
    monthly_returns: pd.DataFrame
    weights: pd.DataFrame
    summary: Dict[str, Any]


def backtest_cross_sectional_momentum(
    log_returns: pd.DataFrame,
    lookback_months: int = 1,
    skip_recent_months: int = 0,
    n_long: int = 20,
    n_short: int = 20,
    long_capital: float = 0.5,
    short_capital: float = 0.5,
) -> MomentumBacktestResult:
    """
    Cross sectional momentum backtest on monthly data.

    Steps
      1. Compute momentum scores from log returns.
      2. Each month, rank stocks by score and form long short portfolio.
      3. Use scores at month t to trade from t to t+1 (weights are shifted by 1).
      4. Portfolio return is (Long leg profit + Short leg profit) / 2.

    Parameters
    ----------
    log_returns : pd.DataFrame
        Date x Symbol monthly log returns.
    lookback_months : int
        Window length for momentum score.
    skip_recent_months : int
        How many recent months to skip in the score.
    n_long : int
        Number of stocks on the long side.
    n_short : int
        Number of stocks on the short side.
    long_capital : float
        Capital allocated to long leg (sum of positive weights).
    short_capital : float
        Capital allocated to short leg (absolute sum of negative weights).

    Returns
    -------
    MomentumBacktestResult
    """
    # 1. Momentum scores
    scores = compute_momentum_scores(
        log_returns,
        lookback_months=lookback_months,
        skip_recent_months=skip_recent_months,
    )

    # 2. Raw weights at each date, to be used for next period
    raw_weights = build_long_short_weights(
        scores,
        n_long=n_long,
        n_short=n_short,
        long_capital=long_capital,
        short_capital=short_capital,
    )

    # 3. Use previous month weights for current month returns (no look ahead)
    weights_lagged = raw_weights.shift(1)

    # Convert log returns to simple returns for composition
    simple_returns = np.exp(log_returns) - 1.0

    long_ret, short_ret, portfolio_ret = split_long_short_returns(
        weights_lagged,
        simple_returns,
    )

    monthly = pd.DataFrame(
        {
            "long_return": long_ret,
            "short_return": short_ret,
            "portfolio_return": portfolio_ret,
        }
    )

    # Drop leading NaNs where we did not have enough history
    monthly = monthly.dropna(how="all")

    # Cumulative performance and stats
    monthly["cum_return"] = (1.0 + monthly["portfolio_return"]).cumprod() - 1.0

    if len(monthly) > 1:
        mean_monthly = monthly["portfolio_return"].mean()
        std_monthly = monthly["portfolio_return"].std(ddof=1)

        ann_factor = 12.0
        ann_return = (1.0 + mean_monthly) ** ann_factor - 1.0
        ann_vol = std_monthly * np.sqrt(ann_factor)
        sharpe = ann_return / ann_vol if ann_vol > 0 else np.nan

        # Simple t statistic of mean return
        t_stat = mean_monthly / (std_monthly / np.sqrt(len(monthly))) if std_monthly > 0 else np.nan
    else:
        mean_monthly = 0.0
        std_monthly = 0.0
        ann_return = 0.0
        ann_vol = 0.0
        sharpe = np.nan
        t_stat = np.nan

    summary = {
        "n_periods": int(len(monthly)),
        "mean_monthly_return": float(mean_monthly),
        "std_monthly_return": float(std_monthly),
        "annualized_return": float(ann_return),
        "annualized_volatility": float(ann_vol),
        "sharpe_ratio": float(sharpe),
        "t_stat_mean_return": float(t_stat),
        "final_cumulative_return": float(monthly["cum_return"].iloc[-1]) if len(monthly) else 0.0,
    }

    return MomentumBacktestResult(
        monthly_returns=monthly,
        weights=weights_lagged,
        summary=summary,
    )
