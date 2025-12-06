import numpy as np
import pandas as pd

def detect_market_regime(df_close, win_short=20, win_long=60):
    '''Xác định chế độ thị trường (MVB)'''
    market_index = df_close.mean(axis=1)
    ret = np.log(market_index / market_index.shift(1))
    
    vol_20 = ret.rolling(win_short).std()
    vol_60 = ret.rolling(win_long).std()
    
    mvb = vol_20 / (vol_60 + 1e-6)
    return mvb

def calculate_final_weights(scores_dict, mvb_series):
    '''Trộn weight dựa trên Regime'''
    dates = mvb_series.index
    tickers = list(scores_dict['MR'].columns)
    final_weights = pd.DataFrame(0.0, index=dates, columns=tickers)
    
    # Bảng hệ số lambda [MR, Mom, VB, XSR, Val]
    lambda_low  = np.array([0.20, 0.50, 0.10, 0.10, 0.10])
    lambda_high = np.array([0.45, 0.20, 0.20, 0.10, 0.05])
    lambda_med  = np.array([0.30, 0.30, 0.20, 0.10, 0.10])
    
    for t in dates:
        mvb = mvb_series.loc[t]
        
        if pd.isna(mvb): w_k = lambda_med
        elif mvb < 0.9:  w_k = lambda_low
        elif mvb > 1.1:  w_k = lambda_high
        else:            w_k = lambda_med
            
        # Tổng hợp Score
        # scores_dict keys: 'MR', 'Mom', 'VB', 'XSR', 'Val'
        # w_k indices:       0     1      2     3      4
        
        w_t = (w_k[0] * np.nan_to_num(scores_dict['MR'].loc[t].values) +
               w_k[1] * np.nan_to_num(scores_dict['Mom'].loc[t].values) +
               w_k[2] * np.nan_to_num(scores_dict['VB'].loc[t].values) +
               w_k[3] * np.nan_to_num(scores_dict['XSR'].loc[t].values) +
               w_k[4] * np.nan_to_num(scores_dict['Val'].loc[t].values))
               
        final_weights.loc[t] = w_t
        
    return final_weights