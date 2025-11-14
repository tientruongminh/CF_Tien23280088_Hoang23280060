from typing import Tuple, Dict

import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA


# =========================
#  AR, MA, ARIMA
# =========================

def arima_forecast_signal(
    returns: pd.Series,
    order: Tuple[int, int, int],
    train_ratio: float = 0.7,
) -> pd.Series:
    """
    Fit ARIMA trên phần train, forecast phần test,
    dùng sign của forecast làm tín hiệu trading.

    order = (p, d, q)
    returns là log_return.
    """
    returns = returns.dropna().copy()
    n = len(returns)
    if n == 0:
        raise ValueError("Chuỗi returns rỗng")

    # Dùng index integer để tránh warning về date index trong statsmodels
    returns.index = pd.RangeIndex(start=0, stop=n, step=1)

    split = int(n * train_ratio)
    if split <= 5:
        raise ValueError("Chuỗi quá ngắn so với train_ratio")

    train = returns.iloc[:split]
    test = returns.iloc[split:]

    if len(train) < max(order[0], order[2]) + order[1] + 5:
        raise ValueError("Chuỗi quá ngắn so với order ARIMA")

    model = ARIMA(train, order=order)
    fitted = model.fit()

    forecast_res = fitted.get_forecast(steps=len(test))
    mean_forecast = forecast_res.predicted_mean

    # sign của forecast dùng làm tín hiệu
    signal_test = np.sign(mean_forecast)

    signal = pd.concat(
        [
            pd.Series(0.0, index=train.index),
            pd.Series(signal_test, index=test.index),
        ]
    )
    signal.name = f"position_arima_{order}"
    return signal


def build_signals_ar_ma_arima(df: pd.DataFrame) -> Dict[str, pd.Series]:
    """
    Tạo các tín hiệu:
    - AR(1)  tương đương ARIMA(1,0,0)
    - MA(1)  tương đương ARIMA(0,0,1)
    - ARIMA(1,1,1)
    """
    r = df["log_return"]
    signals: Dict[str, pd.Series] = {}

    signals["ar1"] = arima_forecast_signal(r, order=(1, 0, 0))
    signals["ma1"] = arima_forecast_signal(r, order=(0, 0, 1))
    signals["arima_1_1_1"] = arima_forecast_signal(r, order=(1, 1, 1))

    return signals


# =========================
#  Bollinger và volatility
# =========================

def bollinger_mean_reversion_signal(df: pd.DataFrame) -> pd.Series:
    """
    Chiến lược mean reversion với Bollinger Bands:
    - Buy khi giá từ dưới lower band cắt lên
    - Short khi giá từ trên upper band cắt xuống
    Giữ vị thế cho đến khi có tín hiệu trái ngược.
    """
    df = df.copy()

    cond_long = (
        (df["Close"].shift(1) < df["bb_lower"].shift(1))
        & (df["Close"] > df["bb_lower"])
    )
    cond_short = (
        (df["Close"].shift(1) > df["bb_upper"].shift(1))
        & (df["Close"] < df["bb_upper"])
    )

    position = pd.Series(0.0, index=df.index)
    position = position.where(~cond_long, 1.0)
    position = position.where(~cond_short, -1.0)

    # Giữ vị thế cho đến khi có tín hiệu khác
    # Sửa FutureWarning: dùng replace 0.0 -> NaN rồi ffill
    position = position.replace(0.0, np.nan).ffill().fillna(0.0)
    position.name = "position_bb"
    return position


def volatility_position_sizing(df: pd.DataFrame, target_vol: float = 0.15) -> pd.Series:
    """
    Position sizing dựa trên volatility:
    position khoảng target_vol chia cho rolling_vol annualized.
    Cắt trong khoảng [-1, 1].
    """
    df = df.copy()
    pos = target_vol / (df["rolling_vol"] * np.sqrt(252))
    pos = pos.clip(lower=-1.0, upper=1.0)
    pos = pos.fillna(0.0)
    pos.name = "position_vol_size"
    return pos


# =========================
#  Kalman filter
# =========================

def kalman_filter_trend(price: pd.Series) -> Tuple[pd.Series, pd.Series]:
    """
    Kalman filter một chiều cho giá với mô hình random walk:

    x_t = x_{t 1} + w_t
    y_t = x_t + v_t

    Trả về:
    - state_filtered: ước lượng giá mượt
    - signal: sign của slope state làm tín hiệu long hoặc short
    """
    z = price.dropna()
    n = len(z)
    if n == 0:
        raise ValueError("Chuỗi giá rỗng")

    Q = 1e-4
    R = 1e-2

    xhat = np.zeros(n)
    P = np.zeros(n)
    xhat_minus = np.zeros(n)
    P_minus = np.zeros(n)
    K = np.zeros(n)

    xhat[0] = z.iloc[0]
    P[0] = 1.0

    for k in range(1, n):
        # Predict
        xhat_minus[k] = xhat[k - 1]
        P_minus[k] = P[k - 1] + Q

        # Update
        K[k] = P_minus[k] / (P_minus[k] + R)
        xhat[k] = xhat_minus[k] + K[k] * (z.iloc[k] - xhat_minus[k])
        P[k] = (1.0 - K[k]) * P_minus[k]

    state_filtered = pd.Series(xhat, index=z.index, name="kalman_state")
    slope = state_filtered.diff()
    signal = np.sign(slope).fillna(0.0)
    signal.name = "position_kalman"

    return state_filtered, signal


# =========================
#  Particle filter
# =========================

def particle_filter_signal(
    returns: pd.Series,
    n_particles: int = 500,
    process_std: float = 0.01,
    obs_std: float = 0.02,
) -> pd.Series:
    """
    Particle filter đơn giản cho expected return.
    Mỗi particle chứa một giá trị expected_return.
    """

    r = returns.dropna()
    n = len(r)
    if n == 0:
        raise ValueError("Chuỗi returns rỗng")

    particles = np.zeros((n_particles,))
    weights = np.ones((n_particles,)) / n_particles

    signal = []

    for _, y in r.items():
        # Dự đoán state mới
        particles += np.random.normal(0, process_std, size=n_particles)

        # Likelihood của quan sát
        likelihoods = (
            1.0
            / (np.sqrt(2.0 * np.pi) * obs_std)
            * np.exp(-0.5 * ((y - particles) / obs_std) ** 2)
        )

        weights *= likelihoods
        weights += 1e-12
        weights /= weights.sum()

        est = np.sum(particles * weights)
        signal.append(np.sign(est))

        # Resample nếu degeneracy
        effective_n = 1.0 / np.sum(weights ** 2)
        if effective_n < n_particles / 2:
            idx = np.random.choice(
                np.arange(n_particles), size=n_particles, replace=True, p=weights
            )
            particles = particles[idx]
            weights = np.ones((n_particles,)) / n_particles

    signal = pd.Series(signal, index=r.index, name="position_particle")
    return signal
