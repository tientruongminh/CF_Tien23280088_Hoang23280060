import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

def train_lambda_model(scores_dict, df_close, alpha=1.0, horizon=1, min_history=252):
    """
    Train model Ridge để tìm trọng số tối ưu cho các Alpha.
    Sử dụng phương pháp Vectorized (không dùng vòng lặp for) để tăng tốc độ.
    """
    print("  ⚙️ Preparing ML training data...")
    
    # 1. Chuẩn bị Target (y): Forward Return
    # Shift(-horizon) để lấy giá tương lai so với hiện tại
    fwd_ret = df_close.shift(-horizon) / df_close - 1.0
    
    # 2. Xếp chồng dữ liệu (Stacking) để tạo bảng dài (Long format)
    # Biến đổi từ DataFrame (Date x Ticker) thành Series (MultiIndex: Date, Ticker)
    # Cách này giúp align dữ liệu tự động
    
    # FIXED: Use dynamic feature names from scores_dict
    feature_names = list(scores_dict.keys())
    
    # Gom tất cả alpha thành 1 DataFrame lớn
    # stack() sẽ chuyển cột Ticker thành index cấp 2
    X_list = [scores_dict[name].stack().rename(name) for name in feature_names]
    X_all = pd.concat(X_list, axis=1)
    
    y_all = fwd_ret.stack().rename("target")
    
    # 3. Gộp X và y lại
    # join='inner' sẽ tự động loại bỏ những ngày/mã không khớp nhau
    dataset = pd.concat([X_all, y_all], axis=1)
    
    # 4. Làm sạch dữ liệu (Drop NaN)
    # Bước này cực quan trọng để Ridge không bị lỗi
    dataset = dataset.dropna()
    
    if dataset.empty:
        print("⚠️ Warning: Dataset rỗng sau khi dropna. Kiểm tra lại dữ liệu đầu vào.")
        # Trả về dummy model để không crash code
        model = Ridge(alpha=alpha)
        model.coef_ = np.array([0.2, 0.2, 0.2, 0.2, 0.2]) # Default weights
        return model

    # 5. Tách X, y để train
    X_train = dataset[feature_names].values
    y_train = dataset["target"].values
    
    # 6. Fit Model
    model = Ridge(alpha=alpha, fit_intercept=False) # fit_intercept=False vì alpha thường đã chuẩn hóa
    model.fit(X_train, y_train)
    
    print(f"  🔧 ML-learned lambdas: {dict(zip(feature_names, np.round(model.coef_, 4)))}")
    
    return model


def predict_combined_score(scores_dict, model):
    """
    Dùng trọng số đã học (model.coef_) để tính điểm tổng hợp.
    Nhanh hơn model.predict vì dùng phép nhân ma trận trực tiếp trên Pandas.
    """
    # FIXED: Use dynamic feature names
    feature_names = list(scores_dict.keys())
    
    # Lấy mẫu form từ alpha đầu tiên
    first_alpha = scores_dict["MR"]
    combined = pd.DataFrame(0.0, index=first_alpha.index, columns=first_alpha.columns)
    
    # Lấy hệ số từ model
    # model.coef_ là mảng [w1, w2, w3, w4, w5]
    weights = dict(zip(feature_names, model.coef_))
    
    # Tính tổng có trọng số: Score = w1*MR + w2*Mom + ...
    for name in feature_names:
        if name in scores_dict:
            # QUAN TRỌNG: fillna(0) để những chỗ thiếu dữ liệu không làm hỏng kết quả
            # 0 ở đây nghĩa là "trung lập", không mua không bán
            combined += scores_dict[name].fillna(0) * weights[name]
            
    # ---------------------------------------------------------
    # Chuẩn hóa đầu ra (Ranking & Scaling)
    # Bước này giúp đưa score về dạng phân phối đều [-1, 1]
    # ---------------------------------------------------------
    
    # 1. Cross-sectional Median Centering (Trừ đi trung vị của ngày hôm đó)
    # Để đảm bảo luôn có mã mua (dương) và mã bán (âm)
    combined = combined.subtract(combined.median(axis=1), axis=0)
    
    # 2. Scaling bằng Robust Sigmoid hoặc chia cho Quantile
    # Ở đây dùng cách chia cho 90th percentile (như code cũ của bạn)
    denom = combined.abs().quantile(0.9, axis=1) + 1e-6
    combined = combined.div(denom, axis=0)
    
    # 3. Clip về [-1, 1] để tránh các giá trị quá dị biệt
    combined = combined.clip(-1, 1)

    combined.name = "ML_Combined_Score"
    return combined