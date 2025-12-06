import pandas as pd

def calculate_val_score(df_close, window):
    '''Value Proxy: Vị trí trong biên độ 52 tuần'''
    roll_low = df_close.rolling(window=window).min()
    roll_high = df_close.rolling(window=window).max()
    
    # %B indicator
    pct_b = (df_close - roll_low) / (roll_high - roll_low + 1e-6)
    
    # Invert: Rẻ (gần Low) -> Tốt (Score cao)
    raw_val = -pct_b 
    
    # Rank [-1, 1]
    val_score = raw_val.rank(axis=1, pct=True) * 2 - 1
    return val_score.fillna(0)