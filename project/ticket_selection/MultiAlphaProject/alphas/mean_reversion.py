import numpy as np
import pandas as pd
from statsmodels.tsa.vector_ar.vecm import coint_johansen
import warnings

def calculate_mr_score(df_close, window_coint, window_z):
    '''Mean Reversion: Johansen Test + Z-Score'''
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        log_price = np.log(df_close)
        
        # 1. Johansen Test (Tìm weights)
        train_len = min(len(log_price), window_coint)
        X_train = log_price.iloc[:train_len].values
        
        try:
            # det_order=0, k_ar_diff=1
            jores = coint_johansen(X_train, 0, 1)
            w = jores.evec[:, 0]
            if w[-1] != 0: w = w / w[-1]
        except:
            # Fallback weight
            w = np.ones(df_close.shape[1])
            w[1:] = -1/(df_close.shape[1]-1)

        # 2. Tính Spread & Z-Score
        spread = log_price @ w
        roll_mean = spread.rolling(window=window_z).mean()
        roll_std = spread.rolling(window=window_z).std()
        
        # Tránh chia cho 0
        z_score = (spread - roll_mean) / (roll_std + 1e-6)
        
        # 3. Map sang Score từng mã
        # Logic: Score_i = -sign(w_i) * Z_score
        z_clipped = z_score.clip(-2, 2) / 2.0 # Chuẩn hóa về [-1, 1]
        signs = np.sign(w)
        
        # Broadcast vector
        mr_scores = -np.outer(z_clipped.values, signs)
        
        return pd.DataFrame(mr_scores, index=df_close.index, columns=df_close.columns)