import argparse
import json
import os
from typing import Dict

import pandas as pd

from data import load_single_stock_csv, add_volatility_features
from models import (
    bollinger_mean_reversion_signal,
    volatility_position_sizing,
    build_signals_ar_ma_arima,
    kalman_filter_trend,
    particle_filter_signal,
)
from backtest import backtest_from_positions, performance_summary, plot_equity_curves


def save_summary_to_json(summary_dict: dict, csv_path: str) -> None:
    """
    Save all strategy performance summaries into a single JSON file.
    File name: results_<symbol>.json where symbol is derived from csv_path.
    """
    # Extract symbol name from file path
    base = os.path.basename(csv_path)
    symbol = base.replace(".csv", "")

    out_path = f"results_{symbol}.json"

    # Convert numpy types to native Python types for JSON
    cleaned = {}
    for strategy_name, metrics in summary_dict.items():
        cleaned[strategy_name] = {}
        for k, v in metrics.items():
            if hasattr(v, "item"):
                cleaned[strategy_name][k] = float(v)
            else:
                cleaned[strategy_name][k] = v

    with open(out_path, "w") as f:
        json.dump(cleaned, f, indent=4)

    print(f"\nSaved JSON summary to {out_path}")


def run_all_models(csv_path: str, fee_bps: float = 5.0) -> None:
    df = load_single_stock_csv(csv_path)
    df = add_volatility_features(df, window=20)

    curves: Dict[str, pd.Series] = {}

    # 1. Bollinger mean reversion
    df["position_bb"] = bollinger_mean_reversion_signal(df)
    res_bb = backtest_from_positions(df, pos_col="position_bb", fee_bps=fee_bps)
    perf_bb = performance_summary(res_bb)
    curves["Bollinger"] = res_bb["equity_curve"]

    # 2. Volatility position sizing on sign of return
    sign_return = df["log_return"].apply(
        lambda x: 1.0 if x > 0 else (-1.0 if x < 0 else 0.0)
    )
    df["position_vol"] = volatility_position_sizing(df) * sign_return
    res_vol = backtest_from_positions(df, pos_col="position_vol", fee_bps=fee_bps)
    perf_vol = performance_summary(res_vol)
    curves["Vol sized trend"] = res_vol["equity_curve"]

    # 3. AR, MA, ARIMA
    perf_arima: Dict[str, dict] = {}
    signals_arima = build_signals_ar_ma_arima(df)
    for name, sig in signals_arima.items():
        df_tmp = df.copy()
        df_tmp["position"] = sig.reindex(df_tmp.index).fillna(0.0)
        res = backtest_from_positions(df_tmp, pos_col="position", fee_bps=fee_bps)
        perf_arima[name] = performance_summary(res)
        curves[f"ARIMA {name}"] = res["equity_curve"]

    # 4. Kalman trend
    _, sig_kalman = kalman_filter_trend(df["Close"])
    df_tmp = df.copy()
    df_tmp["position"] = sig_kalman.reindex(df_tmp.index).fillna(0.0)
    res_kalman = backtest_from_positions(df_tmp, pos_col="position", fee_bps=fee_bps)
    perf_kalman = performance_summary(res_kalman)
    curves["Kalman"] = res_kalman["equity_curve"]

    # 5. Particle filter
    sig_particle = particle_filter_signal(df["log_return"])
    df_tmp = df.copy()
    df_tmp["position"] = sig_particle.reindex(df_tmp.index).fillna(0.0)
    res_particle = backtest_from_positions(df_tmp, pos_col="position", fee_bps=fee_bps)
    perf_particle = performance_summary(res_particle)
    curves["Particle"] = res_particle["equity_curve"]

    # Build summary dict for all strategies
    summary = {}
    summary["Bollinger"] = perf_bb
    summary["Volatility Trend"] = perf_vol
    for name, perf in perf_arima.items():
        summary[f"ARIMA {name}"] = perf
    summary["Kalman"] = perf_kalman
    summary["Particle Filter"] = perf_particle

    # Print simple text summary
    print("=========================================")
    for strat_name, metrics in summary.items():
        print(strat_name, ":", metrics)

    # Save JSON summary
    save_summary_to_json(summary, csv_path)

    # Plot equity curves
    plot_equity_curves(curves, title=f"Equity curves for {csv_path}")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Run time series trading models on a single stock CSV"
    )
    p.add_argument(
        "--csv_path",
        type=str,
        required=True,
        help=(
            "Path to CSV file containing columns "
            "Date, Close, High, Low, Open, Volume, Symbol, Security Name"
        ),
    )
    p.add_argument(
        "--fee_bps",
        type=float,
        default=5.0,
        help="Transaction cost in basis points for each position change",
    )
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_all_models(args.csv_path, fee_bps=args.fee_bps)
