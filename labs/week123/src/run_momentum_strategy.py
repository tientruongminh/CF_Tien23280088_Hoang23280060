from __future__ import annotations

import argparse
import os

from momentum_data import load_price_panel_from_files, to_monthly_prices, monthly_log_returns
from momentum_backtest import backtest_cross_sectional_momentum


def run_momentum_example(
    csv_paths: list,
    lookback_months: int = 1,
    skip_recent_months: int = 0,
    n_long: int = 10,
    n_short: int = 10,
    long_capital: float = 0.5,
    short_capital: float = 0.5,
) -> None:

    # 1. Load daily prices
    daily_prices = load_price_panel_from_files(csv_paths, price_col="Close", symbol_col="Symbol")

    # 2. Resample to month end
    monthly_prices = to_monthly_prices(daily_prices, method="last")

    # 3. Log returns
    log_ret = monthly_log_returns(monthly_prices)

    # 4. Backtest momentum
    result = backtest_cross_sectional_momentum(
        log_returns=log_ret,
        lookback_months=lookback_months,
        skip_recent_months=skip_recent_months,
        n_long=n_long,
        n_short=n_short,
        long_capital=long_capital,
        short_capital=short_capital,
    )

    print("Momentum backtest summary:")
    for k, v in result.summary.items():
        if isinstance(v, float):
            print(f"  {k}: {v:.4f}")
        else:
            print(f"  {k}: {v}")

    print("\nFirst few monthly portfolio returns:")
    print(result.monthly_returns.head())


def parse_args():
    parser = argparse.ArgumentParser(description="Run cross sectional momentum backtest")

    parser.add_argument(
        "--csv_paths",
        type=str,
        nargs="+",
        required=True,
        help="Path to input CSV that contains daily prices"
    )

    parser.add_argument("--lookback_months", type=int, default=1, help="Momentum lookback window in months")
    parser.add_argument("--skip_recent_months", type=int, default=0, help="Number of recent months to skip")
    parser.add_argument("--n_long", type=int, default=10, help="Number of long positions")
    parser.add_argument("--n_short", type=int, default=10, help="Number of short positions")
    parser.add_argument("--long_capital", type=float, default=0.5, help="Fraction of capital allocated to long side")
    parser.add_argument("--short_capital", type=float, default=0.5, help="Fraction of capital allocated to short side")

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_momentum_example(
        csv_paths=args.csv_paths,
        lookback_months=args.lookback_months,
        skip_recent_months=args.skip_recent_months,
        n_long=args.n_long,
        n_short=args.n_short,
        long_capital=args.long_capital,
        short_capital=args.short_capital,
    )
