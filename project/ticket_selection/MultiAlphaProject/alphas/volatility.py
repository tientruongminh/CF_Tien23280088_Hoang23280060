import numpy as np
import pandas as pd

def calculate_vb_score(df_close, win_short=20, win_long=60):
    '''
    Volatility Breakout REDESIGNED: Vol Regime Change (Independent from Mom)
    
    Uses statistical volatility regime detection instead of simple ratio.
    This measures PURE volatility expansion/contraction without price direction.
    '''
    daily_ret = np.log(df_close / df_close.shift(1))
    
    # Short-term and long-term volatility
    vol_short = daily_ret.rolling(window=win_short).std()
    vol_long = daily_ret.rolling(window=win_long).std()
    
    # Vol ratio
    vol_ratio = vol_short / (vol_long + 1e-6)
    
    # NEW: Z-score of vol ratio (regime change detection)
    # This makes it independent from price momentum
    vol_mean = vol_ratio.rolling(window=60).mean()
    vol_std = vol_ratio.rolling(window=60).std()
    
    vol_zscore = (vol_ratio - vol_mean) / (vol_std + 1e-6)
    
    # Normalize: clip to [-2, 2] then scale to [-1, 1]
    # >2: High vol regime (expansion)
    # <-2: Low vol regime (contraction)
    vb_score = vol_zscore.clip(-2, 2) / 2
    
    return vb_score.fillna(0)