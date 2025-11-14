from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List

import numpy as np
import pandas as pd


@dataclass
class BacktestResult:
    equity_curve: pd.DataFrame
    trades: pd.DataFrame
    summary: Dict[str, Any]


def backtest_long_only(
    df: pd.DataFrame,
    initial_capital: float = 10_000.0,
    commission_per_trade: float = 0.0,
    slippage_bps: float = 0.0,
    price_col_close: str = "Close",
    price_col_open: str = "Open",
    signal_col: str = "signal",
) -> BacktestResult:
    """
    Simple long only backtest based on entry and exit signals.

    Parameters
    ----------
    df : pd.DataFrame
        Must contain:
          - price_col_open
          - price_col_close
          - signal_col
        Index should be dates in ascending order.
    initial_capital : float
        Starting capital.
    commission_per_trade : float
        Flat commission charged per buy or sell.
    slippage_bps : float
        Slippage in basis points applied to trade prices.

    Returns
    -------
    BacktestResult
        Contains equity curve, trade list, and summary statistics.
    """
    if signal_col not in df.columns:
        raise KeyError(f"Signal column '{signal_col}' not found in DataFrame.")

    if price_col_open not in df.columns:
        raise KeyError(f"Open price column '{price_col_open}' not found in DataFrame.")

    if price_col_close not in df.columns:
        raise KeyError(f"Close price column '{price_col_close}' not found in DataFrame.")

    # Ensure data sorted by index (dates)
    data = df.copy().sort_index()

    dates = data.index
    opens = data[price_col_open]
    closes = data[price_col_close]
    signals = data[signal_col]

    cash = initial_capital
    position = 0  # number of shares
    portfolio_values: List[float] = []
    cash_series: List[float] = []
    position_series: List[int] = []
    trades: List[Dict[str, Any]] = []

    slippage_factor_buy = 1.0 + slippage_bps / 10_000.0
    slippage_factor_sell = 1.0 - slippage_bps / 10_000.0

    # Loop, execute trades at today's open based on yesterday signal
    for i in range(len(data)):
        date = dates[i]

        if i > 0:
            prev_signal = signals.iloc[i - 1]
        else:
            prev_signal = 0

        open_price = float(opens.iloc[i])

        if prev_signal == 1 and position == 0:
            # Enter long
            trade_price = open_price * slippage_factor_buy
            available_cash = cash - commission_per_trade
            if available_cash > trade_price:
                shares = int(available_cash // trade_price)
            else:
                shares = 0

            if shares > 0:
                cost = shares * trade_price + commission_per_trade
                cash -= cost
                position += shares

                trades.append(
                    {
                        "date": date,
                        "type": "BUY",
                        "shares": shares,
                        "price": trade_price,
                        "commission": commission_per_trade,
                        "cash_after": cash,
                        "position_after": position,
                    }
                )

        elif prev_signal == -1 and position > 0:
            # Exit long
            trade_price = open_price * slippage_factor_sell
            proceeds = position * trade_price - commission_per_trade
            cash += proceeds

            trades.append(
                {
                    "date": date,
                    "type": "SELL",
                    "shares": position,
                    "price": trade_price,
                    "commission": commission_per_trade,
                    "cash_after": cash,
                    "position_after": 0,
                }
            )
            position = 0

        # Portfolio value at the close of this day
        market_value = position * float(closes.iloc[i])
        total_value = cash + market_value

        cash_series.append(cash)
        position_series.append(position)
        portfolio_values.append(total_value)

    equity = pd.DataFrame(
        {
            "cash": cash_series,
            "position": position_series,
            "holdings_value": np.array(portfolio_values) - np.array(cash_series),
            "total_equity": portfolio_values,
            "close": closes.values,
            "signal": signals.values,
        },
        index=dates,
    )

    # Daily returns and cumulative returns
    equity["daily_return"] = equity["total_equity"].pct_change().fillna(0.0)
    equity["cumulative_return"] = (1.0 + equity["daily_return"]).cumprod() - 1.0

    # Drawdown
    roll_max = equity["total_equity"].cummax()
    equity["drawdown"] = equity["total_equity"] / roll_max - 1.0

    n_days = len(equity)
    if n_days > 1:
        total_return = equity["total_equity"].iloc[-1] / equity["total_equity"].iloc[0] - 1.0
        ann_factor = 252.0 / n_days
        ann_return = (1.0 + total_return) ** ann_factor - 1.0
        ann_vol = equity["daily_return"].std(ddof=1) * np.sqrt(252.0)
        sharpe = ann_return / ann_vol if ann_vol > 0 else np.nan
        max_dd = equity["drawdown"].min()
    else:
        total_return = 0.0
        ann_return = 0.0
        ann_vol = 0.0
        sharpe = np.nan
        max_dd = 0.0

    summary = {
        "initial_capital": float(initial_capital),
        "final_equity": float(equity["total_equity"].iloc[-1]),
        "total_return": float(total_return),
        "annualized_return": float(ann_return),
        "annualized_volatility": float(ann_vol),
        "sharpe_ratio": float(sharpe),
        "max_drawdown": float(max_dd),
        "n_days": int(n_days),
        "n_trades": len(trades),
    }

    trades_df = (
        pd.DataFrame(trades).set_index("date")
        if trades
        else pd.DataFrame(
            columns=["date", "type", "shares", "price", "commission", "cash_after", "position_after"]
        )
    )

    return BacktestResult(equity_curve=equity, trades=trades_df, summary=summary)
