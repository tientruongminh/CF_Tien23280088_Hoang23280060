# backtest.py

from typing import Dict
import os

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


def backtest_from_positions(
    df: pd.DataFrame,
    ret_col: str = "log_return",
    pos_col: str = "position",
    fee_bps: float = 0.0,
) -> pd.DataFrame:
    """
    Backtest chiến lược dựa trên:
      - ret_col: log return
      - pos_col: position_t (long/short/flat)

    fee_bps: phí mỗi lần thay đổi position, tính theo basis points.
             5 bps = 0.0005.
    """
    df = df.copy()

    df["position_shifted"] = df[pos_col].shift(1).fillna(0.0)

    df["strategy_ret"] = df["position_shifted"] * df[ret_col]

    df["trade"] = df["position_shifted"].diff().abs()
    fee_per_unit = fee_bps / 10_000.0
    df["fee"] = df["trade"] * fee_per_unit

    df["strategy_ret_net"] = df["strategy_ret"] - df["fee"]
    df["equity_curve"] = df["strategy_ret_net"].cumsum().apply(np.exp)

    return df


def performance_summary(df: pd.DataFrame, ret_col: str = "strategy_ret_net") -> Dict[str, float]:
    """
    Thống kê cơ bản hàng năm cho cột ret_col.
    """
    r = df[ret_col].dropna()
    if r.empty:
        return {
            "n_periods": 0,
            "mean_daily": 0.0,
            "vol_daily": 0.0,
            "ann_return": 0.0,
            "ann_vol": 0.0,
            "sharpe": 0.0,
        }

    mean_daily = r.mean()
    vol_daily = r.std()
    ann_return = mean_daily * 252.0
    ann_vol = vol_daily * np.sqrt(252.0)
    sharpe = ann_return / ann_vol if ann_vol > 0 else 0.0

    return {
        "n_periods": int(len(r)),
        "mean_daily": float(mean_daily),
        "vol_daily": float(vol_daily),
        "ann_return": float(ann_return),
        "ann_vol": float(ann_vol),
        "sharpe": float(sharpe),
    }


def plot_equity_curves(
    curves: Dict[str, pd.Series],
    title: str,
    symbol: str,
    save_dir: str = "plots",
    show: bool = True,
) -> str:
    """
    Vẽ nhiều equity curve trên cùng một hình và lưu ra file.

    curves: dict {model_name: equity_series}
    symbol: dùng đặt tên file, ví dụ ATLO
    """
    os.makedirs(save_dir, exist_ok=True)
    filepath = os.path.join(save_dir, f"equity_curves_{symbol}.png")

    plt.figure(figsize=(12, 4))
    for name, series in curves.items():
        series.plot(label=name)
    plt.legend()
    plt.grid(True)
    plt.title(title)
    plt.tight_layout()
    plt.savefig(filepath, dpi=300)

    if show:
        plt.show()
    else:
        plt.close()

    print(f"[PLOT] Saved equity curves to: {filepath}")
    return filepath
