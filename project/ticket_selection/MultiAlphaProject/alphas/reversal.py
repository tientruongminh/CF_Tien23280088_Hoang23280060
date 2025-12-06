import pandas as pd

def calculate_xsr_score(df_close):
    '''Cross-Sectional Reversal: Short-term mean reversion (FIXED)'''
    # Daily return
    daily_ret = df_close.pct_change()
    
    # FIX 1: Fill NaN with 0 (neutral signal when no data)
    daily_ret = daily_ret.fillna(0)
    
    # Reversal: negative of daily return
    raw_xsr = -daily_ret
    
    # Cross-sectional rank
    xsr_score = raw_xsr.rank(axis=1, pct=True) * 2 - 1
    
    # FIX 2: First 20 days = neutral (insufficient history)
    xsr_score.iloc[:20] = 0
    
    return xsr_score.fillna(0)