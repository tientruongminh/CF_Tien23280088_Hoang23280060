# ============================================================
# models_full.py
# Tổng hợp toàn bộ mô hình time-series cho Week 5:
# - AR/MA/ARIMA
# - Stationarity + ADF test
# - Volatility (historical, rolling, EWMA)
# - ARCH/GARCH
# - Bollinger, Volatility Position Sizing
# - Kalman Filter
# - Particle Filter
# - Position Sizing theo R, M
# - RNN/LSTM (extension)
# ============================================================

import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional

from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller


# ============================================================
# 1. LOG RETURN + ADF TEST
# ============================================================

def compute_log_returns(prices: pd.Series) -> pd.Series:
    """Tính log return r_t = ln(P_t / P_{t-1})."""
    return np.log(prices / prices.shift(1))


def adf_test(series: pd.Series, alpha: float = 0.05) -> Dict[str, object]:
    """ADF stationarity test với giải thích."""
    series = series.dropna()

    test_stat, pval, nlags, nobs, crit, _ = adfuller(series)

    return {
        "test_stat": float(test_stat),
        "pvalue": float(pval),
        "n_lags": int(nlags),
        "n_obs": int(nobs),
        "critical_values": crit,
        "alpha": alpha,
        "is_stationary": pval <= alpha
    }


# ============================================================
# 2. ARIMA / AR / MA
# ============================================================

def arima_forecast_signal(
    returns: pd.Series,
    order: Tuple[int, int, int],
    train_ratio: float = 0.7,
) -> pd.Series:
    """Tín hiệu trading = sign(forecast_ARIMA)."""
    r = returns.dropna().copy()
    r.index = range(len(r))

    split = int(len(r) * train_ratio)
    train = r[:split]
    test = r[split:]

    model = ARIMA(train, order=order).fit()
    forecast = model.get_forecast(len(test)).predicted_mean

    signal = pd.concat([
        pd.Series(0.0, index=train.index),
        np.sign(forecast)
    ])
    signal.name = f"arima_{order}"
    return signal


def build_signals_ar_ma_arima(df: pd.DataFrame) -> Dict[str, pd.Series]:
    r = df["log_return"]
    return {
        "ar1": arima_forecast_signal(r, (1, 0, 0)),
        "ma1": arima_forecast_signal(r, (0, 0, 1)),
        "arima_1_1_1": arima_forecast_signal(r, (1, 1, 1)),
    }


# ============================================================
# 3. VOLATILITY (Historical, Rolling, EWMA)
# ============================================================

def historical_volatility(returns: pd.Series) -> Tuple[float, float]:
    r = returns.dropna()
    sigma_daily = r.std()
    sigma_annual = sigma_daily * np.sqrt(252)
    return float(sigma_daily), float(sigma_annual)


def rolling_volatility(returns: pd.Series, window: int = 20) -> pd.Series:
    return returns.rolling(window).std()


def ewma_volatility(returns: pd.Series, span: int = 20) -> pd.Series:
    var = returns.ewm(span=span).var()
    return np.sqrt(var)


# ============================================================
# 4. ARCH / GARCH
# ============================================================

def fit_garch_11(returns: pd.Series):
    """Fit GARCH(1,1). Cần thư viện arch."""
    try:
        from arch import arch_model
    except ImportError:
        raise ImportError("pip install arch")

    r = returns.dropna() * 100
    model = arch_model(r, vol="GARCH", p=1, q=1)
    res = model.fit(disp="off")
    return model, res


# ============================================================
# 5. BOLLINGER BANDS + MEAN REVERSION
# ============================================================

def bollinger_signal(df: pd.DataFrame) -> pd.Series:
    cond_long = (
        (df["Close"].shift(1) < df["bb_lower"].shift(1)) &
        (df["Close"] > df["bb_lower"])
    )
    cond_short = (
        (df["Close"].shift(1) > df["bb_upper"].shift(1)) &
        (df["Close"] < df["bb_upper"])
    )

    pos = pd.Series(0.0, index=df.index)
    pos = pos.mask(cond_long, 1.0)
    pos = pos.mask(cond_short, -1.0)
    pos = pos.replace(0, np.nan).ffill().fillna(0)
    pos.name = "position_bb"
    return pos


# ============================================================
# 6. VOLATILITY POSITION SIZING
# ============================================================

def volatility_position_sizing(df: pd.DataFrame, target_vol: float = 0.15) -> pd.Series:
    vol = df["rolling_vol"] * np.sqrt(252)
    pos = (target_vol / vol).clip(-1, 1).fillna(0)
    pos.name = "position_vol_sizing"
    return pos


# ============================================================
# 7. KALMAN FILTER (Random Walk Model)
# ============================================================

def kalman_filter_trend(price: pd.Series) -> Tuple[pd.Series, pd.Series]:
    z = price.dropna()
    n = len(z)

    Q, R = 1e-4, 1e-2

    xhat = np.zeros(n)
    P = np.zeros(n)

    xhat[0] = z.iloc[0]
    P[0] = 1

    for t in range(1, n):
        x_minus = xhat[t-1]
        P_minus = P[t-1] + Q

        K = P_minus / (P_minus + R)

        xhat[t] = x_minus + K * (z.iloc[t] - x_minus)
        P[t] = (1 - K) * P_minus

    state = pd.Series(xhat, index=z.index, name="kalman_state")
    signal = np.sign(state.diff()).fillna(0)
    signal.name = "position_kalman"

    return state, signal


# ============================================================
# 8. PARTICLE FILTER
# ============================================================

def particle_filter_signal(
    returns: pd.Series,
    n_particles: int = 500,
    process_std: float = 0.01,
    obs_std: float = 0.02,
) -> pd.Series:

    r = returns.dropna()
    particles = np.zeros(n_particles)
    weights = np.ones(n_particles) / n_particles

    sig = []

    for y in r:
        particles += np.random.normal(0, process_std, n_particles)

        likelihood = (
            np.exp(-0.5 * ((y - particles) / obs_std)**2) /
            (obs_std * np.sqrt(2 * np.pi))
        )

        weights *= likelihood
        weights += 1e-12
        weights /= weights.sum()

        estimate = np.sum(particles * weights)
        sig.append(np.sign(estimate))

        neff = 1.0 / np.sum(weights**2)
        if neff < n_particles / 2:
            idx = np.random.choice(n_particles, n_particles, p=weights)
            particles = particles[idx]
            weights = np.ones(n_particles) / n_particles

    return pd.Series(sig, index=r.index, name="position_particle")


# ============================================================
# 9. POSITION SIZING THEO RISK (R, M)
# ============================================================

def position_size_risk(
    equity: float,
    risk_fraction: float,
    sigma_daily: float,
    M: float,
    last_price: float,
) -> Dict[str, float]:
    R = equity * risk_fraction
    dollar_vol = sigma_daily * M * last_price
    shares = R / dollar_vol

    return {
        "R_dollar": float(R),
        "dollar_vol_per_share": float(dollar_vol),
        "shares": float(shares),
    }


# ============================================================
# 10. RNN / LSTM (EXTENSION)
# ============================================================

import torch
import torch.nn as nn


class LSTMForecaster(nn.Module):
    def __init__(self, hidden=32):
        super().__init__()
        self.lstm = nn.LSTM(1, hidden, batch_first=True)
        self.fc = nn.Linear(hidden, 1)

    def forward(self, x):
        out, _ = self.lstm(x)
        return self.fc(out[:, -1])


def lstm_signal(returns: pd.Series, lookback=20, epochs=5) -> pd.Series:
    r = returns.dropna().values.astype(np.float32)
    X, y = [], []

    for i in range(len(r) - lookback):
        X.append(r[i:i+lookback])
        y.append(r[i+lookback])

    X = np.array(X)[:, :, None]
    y = np.array(y)[:, None]

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = LSTMForecaster().to(device)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = nn.MSELoss()

    X_t = torch.tensor(X).to(device)
    y_t = torch.tensor(y).to(device)

    for _ in range(epochs):
        opt.zero_grad()
        loss = loss_fn(model(X_t), y_t)
        loss.backward()
        opt.step()

    preds = model(X_t).detach().cpu().numpy().ravel()
    sig = np.sign(preds)

    idx = returns.dropna().index[lookback:]
    return pd.Series(sig, index=idx, name="position_lstm")
