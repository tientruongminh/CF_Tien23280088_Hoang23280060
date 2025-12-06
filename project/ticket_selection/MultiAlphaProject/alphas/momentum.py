import numpy as np
import pandas as pd

def calculate_mom_score(df_close, window):
    '''Momentum: Risk-Adjusted Return'''
    # Return tích lũy
    log_ret = np.log(df_close / df_close.shift(window))
    
    # Volatility hàng ngày
    daily_ret = np.log(df_close / df_close.shift(1))
    vol = daily_ret.rolling(window=window).std() * np.sqrt(252)
    
    # Risk-adjusted Momentum
    raw_mom = log_ret / (vol + 1e-6)
    
    # Cross-sectional Rank [-1, 1]
    mom_score = raw_mom.rank(axis=1, pct=True) * 2 - 1
    return mom_score.fillna(0)