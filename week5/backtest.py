from typing import Dict

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
    Backtest chiến lược dựa trên position và log_return.

    fee_bps: phí cho mỗi lần thay đổi position (basis points)
    ví dụ 5 bps tương đương 0.0005.
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
    Một số thống kê cơ bản hàng năm.
    """
    out: Dict[str, float] = {}
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

    out["n_periods"] = len(r)
    out["mean_daily"] = r.mean()
    out["vol_daily"] = r.std()

    out["ann_return"] = r.mean() * 252.0
    out["ann_vol"] = r.std() * np.sqrt(252.0)
    out["sharpe"] = out["ann_return"] / out["ann_vol"] if out["ann_vol"] > 0 else 0.0
    return out


def plot_equity_curves(curves: Dict[str, pd.Series], title: str = "Equity curves") -> None:
    """
    Vẽ nhiều equity curve trên cùng một hình.
    """
    plt.figure(figsize=(12, 4))
    for name, series in curves.items():
        series.plot(label=name)
    plt.legend()
    plt.grid(True)
    plt.title(title)
    plt.tight_layout()
    plt.show()
