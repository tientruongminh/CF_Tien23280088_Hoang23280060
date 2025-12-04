from __future__ import annotations

import os
import argparse

from data_loader import load_price_data
from signals import bollinger_reversion_signals
from backtest import backtest_long_only


def run_example(
    csv_path: str,
    window: int = 20,
    num_std: float = 2.0,
    initial_capital: float = 10_000.0,
) -> None:
    """
    Example pipeline:
      - load price data
      - compute Bollinger Bands and signals
      - run a long only backtest
      - print summary
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Could not find CSV file at '{csv_path}'.")

    prices = load_price_data(csv_path)

    data_with_signals = bollinger_reversion_signals(
        prices,
        price_col="Close",
        window=window,
        num_std=num_std,
    )

    result = backtest_long_only(
        data_with_signals,
        initial_capital=initial_capital,
    )

    print("Backtest summary:")
    for k, v in result.summary.items():
        if isinstance(v, float):
            print(f"  {k}: {v:.4f}")
        else:
            print(f"  {k}: {v}")


def parse_args():
    parser = argparse.ArgumentParser(description="Run Bollinger Band backtest example")

    parser.add_argument(
        "--csv_path",
        type=str,
        required=True,
        help="Path to input CSV file containing price data"
    )

    parser.add_argument(
        "--window",
        type=int,
        default=20,
        help="Rolling window size for SMA and std"
    )

    parser.add_argument(
        "--num_std",
        type=float,
        default=2.0,
        help="Number of standard deviations for Bollinger Bands"
    )

    parser.add_argument(
        "--initial_capital",
        type=float,
        default=10_000.0,
        help="Initial portfolio capital"
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_example(
        csv_path=args.csv_path,
        window=args.window,
        num_std=args.num_std,
        initial_capital=args.initial_capital,
    )
