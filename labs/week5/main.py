# main.py

import argparse
import json
import os
from typing import Dict

import pandas as pd

from data import load_single_stock_csv, add_volatility_features
from backtest import backtest_from_positions, performance_summary, plot_equity_curves

from models_full import (
    adf_test,
    historical_volatility,
    ewma_volatility,
    fit_garch_11,
    build_signals_ar_ma_arima,
    bollinger_signal,
    volatility_position_sizing,
    kalman_filter_trend,
    particle_filter_signal,
    position_size_risk,
    lstm_signal,
)


def save_summary_to_json(
    model_summaries: Dict[str, Dict[str, float]],
    diagnostics: Dict[str, object],
    csv_path: str,
) -> str:
    """
    Lưu toàn bộ kết quả ra 1 file JSON:
      - per model: metrics
      - diagnostics: ADF, volatility, GARCH, position sizing demo
    """
    base = os.path.basename(csv_path)
    symbol = base.replace(".csv", "")
    out_path = f"results_{symbol}.json"

    to_save = {
        "symbol": symbol,
        "models": model_summaries,
        "diagnostics": diagnostics,
    }

    with open(out_path, "w") as f:
        json.dump(to_save, f, indent=2)

    print(f"[JSON] Saved summary to: {out_path}")
    return out_path


def run_all_models(csv_path: str, fee_bps: float) -> None:
    print("===========================================")
    print(f"[INFO] Loading data from: {csv_path}")
    print("===========================================")

    df = load_single_stock_csv(csv_path)
    df = add_volatility_features(df, window=20)

    # ==============================
    # Diagnostics: ADF, volatility, GARCH
    # ==============================
    print("[INFO] Running diagnostics (ADF, volatility, GARCH)")

    adf_result = adf_test(df["log_return"])
    sigma_daily, sigma_annual = historical_volatility(df["log_return"])
    ewma_vol = ewma_volatility(df["log_return"], span=20)

    garch_info = {}
    try:
        model_garch, res_garch = fit_garch_11(df["log_return"])
        garch_info["params"] = {k: float(v) for k, v in res_garch.params.items()}
        garch_info["aic"] = float(res_garch.aic)
        garch_info["bic"] = float(res_garch.bic)
    except Exception as e:
        garch_info["error"] = str(e)

    diagnostics = {
        "adf": adf_result,
        "historical_vol": {
            "sigma_daily": sigma_daily,
            "sigma_annual": sigma_annual,
        },
        "ewma_example": {
            "last_ewma_vol_daily": float(ewma_vol.iloc[-1]) if not ewma_vol.empty else 0.0,
        },
        "garch_11": garch_info,
    }

    print("[LOG] ADF result:")
    print(f"  test_stat    : {adf_result['test_stat']:.6f}")
    print(f"  pvalue       : {adf_result['pvalue']:.6f}")
    print(f"  is_stationary: {adf_result['is_stationary']}")
    print()

    print("[LOG] Historical volatility:")
    print(f"  sigma_daily : {sigma_daily:.6f}")
    print(f"  sigma_annual: {sigma_annual:.6f}")
    print()

    # Demo position sizing theo R, M (log ra thôi)
    try:
        from models_full import position_size_risk
        ps_demo = position_size_risk(
            equity=100_000.0,
            risk_fraction=0.01,
            sigma_daily=sigma_daily if sigma_daily > 0 else 0.02,
            M=2.0,
            last_price=float(df["Close"].iloc[-1]),
        )
        diagnostics["position_sizing_demo"] = ps_demo
        print("[LOG] Position sizing demo (equity=100k, risk=1 percent, M=2):")
        print(f"  R_dollar            : {ps_demo['R_dollar']:.2f}")
        print(f"  dollar_vol_per_share: {ps_demo['dollar_vol_per_share']:.4f}")
        print(f"  shares              : {ps_demo['shares']:.2f}")
        print()
    except Exception as e:
        print(f"[WARN] Position sizing demo failed: {e}")

    # ==============================
    # Trading models
    # ==============================

    curves: Dict[str, pd.Series] = {}
    summaries: Dict[str, Dict[str, float]] = {}

    # 1. Classical AR, MA, ARIMA on log_return
    print("===========================================")
    print("[INFO] Running classical AR MA ARIMA models")
    print("===========================================")

    arima_signals = build_signals_ar_ma_arima(df)
    for name, sig in arima_signals.items():
        model_name = f"TS_{name}"
        df_tmp = df.copy()
        df_tmp["position"] = sig.reindex(df_tmp.index).fillna(0.0)

        bt = backtest_from_positions(df_tmp, pos_col="position", fee_bps=fee_bps)
        perf = performance_summary(bt)

        summaries[model_name] = perf
        curves[model_name] = bt["equity_curve"]

        print(f"[MODEL] {model_name}")
        for k, v in perf.items():
            print(f"  {k}: {v:.6f}")
        print()

    # 2. Bollinger mean reversion
    print("===========================================")
    print("[INFO] Running Bollinger mean reversion model")
    print("===========================================")

    df["position_bb"] = bollinger_signal(df)
    bt_bb = backtest_from_positions(df, pos_col="position_bb", fee_bps=fee_bps)
    perf_bb = performance_summary(bt_bb)
    summaries["Bollinger"] = perf_bb
    curves["Bollinger"] = bt_bb["equity_curve"]

    print("[MODEL] Bollinger")
    for k, v in perf_bb.items():
        print(f"  {k}: {v:.6f}")
    print()

    # 3. Volatility sized trend (sign(return) scaled by volatility)
    print("===========================================")
    print("[INFO] Running volatility sized trend model")
    print("===========================================")

    sign_return = df["log_return"].apply(lambda x: 1.0 if x > 0 else (-1.0 if x < 0 else 0.0))
    vol_pos = volatility_position_sizing(df, target_vol=0.15)
    df["position_vol_trend"] = vol_pos * sign_return

    bt_vol = backtest_from_positions(df, pos_col="position_vol_trend", fee_bps=fee_bps)
    perf_vol = performance_summary(bt_vol)
    summaries["VolatilitySizedTrend"] = perf_vol
    curves["VolatilitySizedTrend"] = bt_vol["equity_curve"]

    print("[MODEL] VolatilitySizedTrend")
    for k, v in perf_vol.items():
        print(f"  {k}: {v:.6f}")
    print()

    # 4. Kalman filter trend
    print("===========================================")
    print("[INFO] Running Kalman filter trend model")
    print("===========================================")

    state_kf, sig_kf = kalman_filter_trend(df["Close"])
    df_tmp = df.copy()
    df_tmp["position"] = sig_kf.reindex(df_tmp.index).fillna(0.0)
    bt_kf = backtest_from_positions(df_tmp, pos_col="position", fee_bps=fee_bps)
    perf_kf = performance_summary(bt_kf)
    summaries["KalmanTrend"] = perf_kf
    curves["KalmanTrend"] = bt_kf["equity_curve"]

    print("[MODEL] KalmanTrend")
    for k, v in perf_kf.items():
        print(f"  {k}: {v:.6f}")
    print()

    # 5. Particle filter on expected return
    print("===========================================")
    print("[INFO] Running Particle filter model")
    print("===========================================")

    sig_pf = particle_filter_signal(df["log_return"])
    df_tmp = df.copy()
    df_tmp["position"] = sig_pf.reindex(df_tmp.index).fillna(0.0)
    bt_pf = backtest_from_positions(df_tmp, pos_col="position", fee_bps=fee_bps)
    perf_pf = performance_summary(bt_pf)
    summaries["ParticleFilter"] = perf_pf
    curves["ParticleFilter"] = bt_pf["equity_curve"]

    print("[MODEL] ParticleFilter")
    for k, v in perf_pf.items():
        print(f"  {k}: {v:.6f}")
    print()

    # 6. LSTM demo (extension)
    print("===========================================")
    print("[INFO] Running LSTM demo model (if torch available)")
    print("===========================================")

    try:
        sig_lstm = lstm_signal(df["log_return"], lookback=20, epochs=5)
        df_tmp = df.copy()
        df_tmp["position"] = sig_lstm.reindex(df_tmp.index).fillna(0.0)
        bt_lstm = backtest_from_positions(df_tmp, pos_col="position", fee_bps=fee_bps)
        perf_lstm = performance_summary(bt_lstm)
        summaries["LSTM_Demo"] = perf_lstm
        curves["LSTM_Demo"] = bt_lstm["equity_curve"]

        print("[MODEL] LSTM_Demo")
        for k, v in perf_lstm.items():
            print(f"  {k}: {v:.6f}")
        print()
    except Exception as e:
        print(f"[WARN] LSTM demo not run: {e}")

    # ==============================
    # Save JSON + Plot
    # ==============================
    save_summary_to_json(summaries, diagnostics, csv_path)

    symbol = os.path.basename(csv_path).replace(".csv", "")
    plot_equity_curves(
        curves=curves,
        title=f"Equity curves for {symbol}",
        symbol=symbol,
        save_dir="plots",
        show=True,
    )

    print("===========================================")
    print("[DONE] All models finished")
    print("===========================================")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run time series trading models on a single stock CSV"
    )
    parser.add_argument(
        "--csv_path",
        type=str,
        required=True,
        help="Path to CSV with columns Date, Open, High, Low, Close, Volume, Symbol, Security Name",
    )
    parser.add_argument(
        "--fee_bps",
        type=float,
        default=5.0,
        help="Transaction cost per position change in basis points",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_all_models(args.csv_path, fee_bps=args.fee_bps)
