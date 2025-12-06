# Multi-Alpha Cointegration Trading System

> **Hệ thống giao dịch tự động kết hợp 5 chiến lược (Alpha) sử dụng Machine Learning để tối ưu trọng số**

---

## 📚 Mục Lục
1. [Tổng Quan Dự Án](#1-tổng-quan-dự-án)
2. [Tại Sao Kết Hợp 5 Alpha?](#2-tại-sao-kết-hợp-5-alpha-thay-vì-chạy-riêng-lẻ)
3. [Lý Thuyết Toán Học Từng Alpha](#3-lý-thuyết-toán-học-từng-alpha)
4. [Phương Pháp Kết Hợp ML](#4-phương-pháp-kết-hợp-bằng-machine-learning)
5. [Backtest Là Gì & Đánh Giá Chiến Lược](#5-backtest-là-gì--đánh-giá-chiến-lược)
6. [Giải Thích Output](#6-giải-thích-output)
7. [Kết Luận](#7-kết-luận)

---

## 1. Tổng Quan Dự Án

### 1.1 Mục Tiêu
Xây dựng hệ thống giao dịch **pair trading** trong các cụm cổ phiếu (cluster) có tính **cointegration** (đồng liên kết), kết hợp nhiều chiến lược để:
- Đa dạng hóa nguồn alpha (lợi nhuận vượt trội)
- Giảm drawdown bằng cách không phụ thuộc vào một chiến lược duy nhất
- Tự động học trọng số tối ưu cho từng giai đoạn thị trường

### 1.2 Kiến Trúc 3 Lớp (3-Layer Architecture)

```
┌─────────────────────────────────────────────────────────────────┐
│                        LAYER 1: ALPHA GENERATION                │
│   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│   │   MR    │ │   Mom   │ │   VB    │ │   XSR   │ │   Val   │   │
│   │[-1,+1]  │ │[-1,+1]  │ │[-1,+1]  │ │[-1,+1]  │ │[-1,+1]  │   │
│   └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘   │
└────────┼───────────┼───────────┼───────────┼───────────┼────────┘
         │           │           │           │           │
         ▼           ▼           ▼           ▼           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LAYER 2: ML COMBINATION                      │
│           Ridge Regression: y = w₁·MR + w₂·Mom + ...            │
│                      ↓                                          │
│              Combined Score [-1, +1]                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LAYER 3: EXECUTION                           │
│        Score > threshold → LONG    Score < -threshold → SHORT  │
│                      ↓                                          │
│              Portfolio Returns → Performance Metrics            │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Tại Sao Kết Hợp 5 Alpha Thay Vì Chạy Riêng Lẻ?

### 2.1 Vấn Đề Của Chiến Lược Đơn Lẻ

| Chiến Lược | Hoạt Động Tốt Khi | Hoạt Động Kém Khi |
|------------|-------------------|-------------------|
| Mean Reversion | Thị trường sideway, low vol | Trending mạnh |
| Momentum | Trending rõ ràng | Sideway, choppy |
| Volatility Breakout | Vol expansion | Vol contraction |
| Reversal | Overreaction | Trending tiếp tục |
| Value | Mean regression dài hạn | Bubble/Crash |

**Kết luận:** Không có chiến lược nào hoạt động tốt trong MỌI điều kiện thị trường.

### 2.2 Lợi Ích Kết Hợp (Ensemble Effect)

```
Ví dụ: Ngày thị trường trending mạnh
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
• MR Score = -0.5 (sai hướng, lỗ)
• Mom Score = +0.8 (đúng hướng, lãi)
• VB Score = +0.6 (đúng hướng, lãi)
• XSR Score = -0.3 (sai hướng, nhỏ)
• Val Score = 0.0 (trung lập)

Combined = 0.15×(-0.5) + 0.35×(+0.8) + 0.10×(+0.6) + 0.25×(-0.3) + 0.15×(0)
         = -0.075 + 0.28 + 0.06 - 0.075 + 0
         = +0.19 → VẪN CÓ LÃI NHỎ thay vì lỗ nếu chỉ dùng MR
```

### 2.3 Diversification Ratio

Theo **Markowitz Portfolio Theory**, kết hợp các chiến lược có **correlation thấp** sẽ:
- Giảm variance tổng thể
- Cải thiện Sharpe Ratio

```
σ²_portfolio = Σ wᵢ²σᵢ² + Σ Σ wᵢwⱼρᵢⱼσᵢσⱼ
                 ↑              ↑
            Variance riêng   Covariance (giảm nếu ρ < 1)
```

---

## 3. Lý Thuyết Toán Học Từng Alpha

### 3.1 Mean Reversion (Johansen Cointegration)

#### Ý Tưởng
Các cổ phiếu trong cùng cluster có xu hướng **di chuyển cùng nhau** trong dài hạn. Khi một cổ phiếu đi chệch khỏi "cân bằng", nó sẽ **quay về**.

#### Công Thức

**Bước 1: Tìm Cointegration Vector (Johansen Test)**
```
Giả sử portfolio có n cổ phiếu với log prices: P₁, P₂, ..., Pₙ

Johansen Test tìm vector w = [w₁, w₂, ..., wₙ] sao cho:
    Spread = w₁·log(P₁) + w₂·log(P₂) + ... + wₙ·log(Pₙ)
    
với Spread là stationary (ADF test < critical value)
```

**Bước 2: Tính Z-Score**
```
Z-Score(t) = [Spread(t) - μ_rolling] / σ_rolling

Với:
    μ_rolling = Mean của Spread trong 60 ngày qua
    σ_rolling = Std của Spread trong 60 ngày qua
```

**Bước 3: Tạo Signal**
```
Score_i = -sign(wᵢ) × clip(Z-Score, -2, +2) / 2

Giải thích:
• Z-Score = +2 (Spread quá cao) → Mã có wᵢ > 0 bị ĐỊNH GIÁ CAO → Score < 0 → SHORT
• Z-Score = -2 (Spread quá thấp) → Mã có wᵢ > 0 bị ĐỊNH GIÁ THẤP → Score > 0 → LONG
```

#### Tại Sao Công Thức Này?
- **Johansen Test** tìm linear combination có tính mean-reverting mạnh nhất
- **Z-Score** chuẩn hóa để so sánh được qua thời gian
- **-sign(wᵢ)** đảm bảo logic: mua rẻ bán đắt

---

### 3.2 Momentum (Risk-Adjusted)

#### Ý Tưởng
Cổ phiếu đang tăng có xu hướng **tiếp tục tăng** (Jegadeesh & Titman, 1993).

#### Công Thức
```
Raw_Momentum(t) = log(P_t / P_{t-60})   # Return 60 ngày

Volatility(t) = std(daily_returns, window=60) × √252

Risk_Adj_Mom(t) = Raw_Momentum(t) / Volatility(t)

Score = cross_sectional_rank(Risk_Adj_Mom) × 2 - 1   # Về [-1, +1]
```

#### Tại Sao Risk-Adjusted?
- **Momentum thuần** dễ bị nhiễu bởi volatility cao
- Cổ phiếu A tăng 10% với vol 5% **tốt hơn** cổ phiếu B tăng 10% với vol 20%
- Đây chính là **Sharpe Ratio của từng cổ phiếu**

---

### 3.3 Volatility Breakout

#### Ý Tưởng
Khi volatility ngắn hạn **vượt** volatility dài hạn, thị trường đang có **trend mới**.

#### Công Thức
```
Vol_Short = std(daily_returns, window=20) 
Vol_Long = std(daily_returns, window=60)

VB_Ratio = (Vol_Short / Vol_Long) - 1

Score = cross_sectional_rank(VB_Ratio) × 2 - 1
```

#### Tại Sao?
- **Vol_Short > Vol_Long** → Thị trường đang "phá vỡ" cân bằng
- Kết hợp với Momentum để xác nhận trend

---

### 3.4 Cross-Sectional Reversal (XSR)

#### Ý Tưởng
Cổ phiếu tăng mạnh **trong ngày hôm qua** có xu hướng **giảm nhẹ hôm nay** (overnight reversal).

#### Công Thức
```
Daily_Return = (P_t - P_{t-1}) / P_{t-1}

Raw_XSR = -Daily_Return   # Đảo dấu: tăng hôm qua → bearish hôm nay

Score = cross_sectional_rank(Raw_XSR) × 2 - 1
```

#### Tại Sao Đảo Dấu?
- **Behavioral Finance**: Overreaction → Mean Reversion ngắn hạn
- Hoạt động tốt trong thị trường choppy

---

### 3.5 Value (52-Week Range Position)

#### Ý Tưởng
Cổ phiếu gần **đáy 52 tuần** được coi là "rẻ" và có tiềm năng hồi phục.

#### Công Thức
```
Low_52w = min(Close, window=252)
High_52w = max(Close, window=252)

%B = (Close - Low_52w) / (High_52w - Low_52w)   # 0% = đáy, 100% = đỉnh

Raw_Value = -%B   # Đảo: Gần đáy = Score cao

Score = cross_sectional_rank(Raw_Value) × 2 - 1
```

#### Tại Sao?
- **Contrarian**: Mua khi rẻ (gần đáy), bán khi đắt (gần đỉnh)
- Proxy cho fundamental value khi không có dữ liệu tài chính

---

## 4. Phương Pháp Kết Hợp Bằng Machine Learning

### 4.1 Tại Sao Không Dùng Trọng Số Cố Định?

| Phương pháp | Nhược điểm |
|-------------|------------|
| Equal Weight (1/5 mỗi alpha) | Không tối ưu, bỏ lỡ alpha mạnh |
| Expert Judgment | Subjective, khó tune |
| Regime-based | Cần xác định regime chính xác |

**Giải pháp:** Để **dữ liệu tự quyết định** trọng số tối ưu thông qua **Ridge Regression**.

### 4.2 Ridge Regression

#### Bài Toán
```
Tìm weights [w_MR, w_Mom, w_VB, w_XSR, w_Val] sao cho:

    ŷ = w_MR·Score_MR + w_Mom·Score_Mom + ... 

Minimize:
    L = Σ(y - ŷ)² + α·||w||²
           ↑            ↑
      MSE Loss    Regularization
```

#### Tại Sao Ridge Thay Vì OLS?
- **OLS** (không có regularization) dễ **overfit** khi các alpha có correlation cao
- **Ridge** (L2 penalty) giữ weights **nhỏ và ổn định**
- Hyperparameter α = 1.0 là mặc định hợp lý

### 4.3 Post-Processing

```python
# 1. Median Centering: Đảm bảo zero-mean (có cả long và short)
combined = combined - combined.median(axis=1)

# 2. Scaling: Robust normalization
combined = combined / combined.abs().quantile(0.9)

# 3. Clipping: Tránh outliers
combined = combined.clip(-1, 1)
```

---

## 5. Backtest Là Gì & Đánh Giá Chiến Lược

### 5.1 Backtest Là Gì?

**Backtest** = Mô phỏng chiến lược trên **dữ liệu lịch sử** để đánh giá hiệu quả.

```
Quy trình:
1. Lấy dữ liệu quá khứ (2015-2024)
2. Chạy chiến lược như thể là thời gian thực
3. Ghi lại tất cả giao dịch và PnL
4. Tính toán metrics đánh giá
```

### 5.2 Tại Sao Cần Backtest?

| Mục đích | Giải thích |
|----------|------------|
| **Validate Logic** | Kiểm tra code đúng, không bug |
| **Performance Estimation** | Ước tính return, risk trong tương lai |
| **Parameter Tuning** | Tối ưu hyperparameters (window, threshold) |
| **Risk Assessment** | Hiểu max drawdown, tail risks |

### 5.3 Các Metrics Quan Trọng

#### A. Return Metrics

| Metric | Công Thức | Ý Nghĩa | Ngưỡng Tốt |
|--------|-----------|---------|------------|
| **Total Return** | (Final_Value / Initial_Value) - 1 | Lợi nhuận tổng | > 50% (5 năm) |
| **Annual Return (CAGR)** | (Total_Return + 1)^(1/years) - 1 | Lãi kép hàng năm | > 10% |

#### B. Risk-Adjusted Metrics

| Metric | Công Thức | Ý Nghĩa | Ngưỡng Tốt |
|--------|-----------|---------|------------|
| **Sharpe Ratio** | (Return - Risk_Free) / Volatility × √252 | Return per unit of risk | > 1.0 |
| **Sortino Ratio** | Return / Downside_Volatility × √252 | Chỉ tính risk khi thua | > 1.5 |
| **Calmar Ratio** | Annual_Return / Max_Drawdown | Return per unit of max loss | > 1.0 |

**Tại Sao Sharpe quan trọng nhất?**
- Chuẩn hóa để so sánh được giữa các chiến lược
- Tính đến cả return VÀ risk
- Industry standard

#### C. Drawdown Metrics

| Metric | Công Thức | Ý Nghĩa | Ngưỡng Tốt |
|--------|-----------|---------|------------|
| **Max Drawdown** | max((Peak - Trough) / Peak) | Mức lỗ tối đa từ đỉnh | < 20% |
| **Avg Drawdown** | mean(all drawdowns) | Mức lỗ trung bình | < 10% |

**Tại Sao DD quan trọng?**
- Sharpe cao nhưng DD = 50% → Không thể chịu được trong thực tế
- Nhà đầu tư thường thoát lệnh khi DD > 20-30%

#### D. Trade Metrics

| Metric | Công Thức | Ý Nghĩa | Ngưỡng Tốt |
|--------|-----------|---------|------------|
| **Win Rate** | #Winning_Days / #Total_Days | Tỷ lệ ngày thắng | > 50% |
| **Profit Factor** | Gross_Profit / Gross_Loss | Lời/Lỗ ratio | > 1.5 |
| **Avg Win / Avg Loss** | - | Risk-reward ratio | > 1.0 |

---

## 6. Giải Thích Output

### 6.1 File `result_cluster_*.csv`

```csv
Date,Weight_CRTO,Weight_STGW,Pos_CRTO,Pos_STGW,Close_CRTO,Close_STGW
2016-01-05,0.5,-0.5,0.5,-0.5,37.52,18.94
```

| Cột | Ý Nghĩa |
|-----|---------|
| Weight_* | Trọng số mục tiêu từ ML Combined Score |
| Pos_* | Vị thế thực tế sau khi áp threshold |
| Close_* | Giá đóng cửa |

### 6.2 File `signals_cluster_*.csv`

```csv
Date,MR_CRTO,MR_STGW,Mom_CRTO,Mom_STGW,VB_CRTO,VB_STGW,...
2016-01-05,0.62,-0.62,0.0,0.0,0.0,0.0,...
```

| Cột | Ý Nghĩa |
|-----|---------|
| MR_* | Mean Reversion Score [-1, +1] |
| Mom_* | Momentum Score |
| VB_* | Volatility Breakout Score |
| XSR_* | Cross-Section Reversal Score |
| Val_* | Value Score |

### 6.3 File `Final_Report.csv`

```csv
Total_Return,Sharpe_Ratio,Win_Rate,File
5.83,1.41,0.54,cluster_financial-services_banks-regional.csv
```

---

## 7. Kết Luận

### 7.1 Tóm Tắt

| Component | Lựa Chọn | Lý Do |
|-----------|----------|-------|
| **5 Alphas** | MR + Mom + VB + XSR + Val | Diversification, cover nhiều market regimes |
| **Combination** | Ridge Regression | Data-driven, tránh overfit |
| **Threshold** | 0.05-0.20 | Lọc noise, giảm trading cost |
| **Backtest** | Full historical | Validate strategy trước khi live |

### 7.2 Limitations

- **Look-ahead bias**: Cẩn thận khi tính forward return
- **Survivorship bias**: Chỉ có data của cổ phiếu còn sống
- **Transaction costs**: Chưa tính phí giao dịch, slippage
- **Regime change**: Weights học từ quá khứ có thể outdated

### 7.3 Next Steps

1. Thêm transaction cost vào backtest
2. Walk-forward optimization thay vì train/test split cố định
3. Live paper trading trước khi deploy thực

---

*Tài liệu được tạo tự động bởi MultiAlpha System*
