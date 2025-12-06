# Multi-Alpha Trading System - Pipeline Diagram

## Sơ Đồ Toàn Bộ Hệ Thống

```mermaid
flowchart TD
    subgraph INPUT["1. DỮ LIỆU ĐẦU VÀO"]
        A1[("Dữ liệu giá<br/>Historical Prices")]
        A2[("Cluster Files<br/>6 nhóm ngành")]
    end

    subgraph ALPHA["2. TÍNH ALPHA SIGNALS"]
        B1["MR - Mean Reversion<br/>Z-Score của giá"]
        B2["Mom - Momentum<br/>Lợi nhuận 60 ngày"]
        B3["VB - Volatility<br/>Z-Score biến động"]
        B4["XSR - Cross-Sectional Reversal<br/>Đảo chiều ngắn hạn"]
        B5["Val - Value<br/>Vị trí 52-week"]
    end

    subgraph ML["3. KẾT HỢP ML"]
        C1["Ridge Regression<br/>Alpha = 1.0"]
        C2["Học trọng số<br/>từ dữ liệu lịch sử"]
        C3["Combined Score<br/>= Σ(weight × alpha)"]
    end

    subgraph STRATEGY["4. CHIẾN LƯỢC GIAO DỊCH"]
        D1["Score → Target Weight"]
        D2["Position Sizing<br/>Max 30% mỗi vị thế"]
        D3["Tạo tín hiệu<br/>BUY / SELL / HOLD"]
    end

    subgraph BACKTEST["5. KIỂM THỬ"]
        E1["Backtest Engine<br/>10 năm dữ liệu"]
        E2["Tính lợi nhuận<br/>hàng ngày"]
        E3["Tính 13 metrics<br/>đánh giá"]
    end

    subgraph OUTPUT["6. KẾT QUẢ"]
        F1[("equity_*.csv<br/>Equity curve")]
        F2[("result_*.csv<br/>Metrics")]
        F3[("trades_*.csv<br/>Lịch sử GD")]
        F4[("signals_*.csv<br/>Tín hiệu")]
    end

    subgraph DASHBOARD["7. DASHBOARD"]
        G1["Tab 1: Đánh Giá<br/>Grade A-F"]
        G2["Tab 2: Hiệu Suất<br/>Charts + Insights"]
        G3["Tab 3: Tín Hiệu<br/>Next Trade"]
    end

    A1 --> B1 & B2 & B3 & B4 & B5
    A2 --> B1

    B1 & B2 & B3 & B4 & B5 --> C1
    C1 --> C2 --> C3

    C3 --> D1 --> D2 --> D3

    D3 --> E1 --> E2 --> E3

    E3 --> F1 & F2 & F3 & F4

    F1 & F2 & F3 & F4 --> G1 & G2 & G3
```

---

## Chi Tiết Từng Bước

### 1. Dữ Liệu Đầu Vào
```
clusters/
├── cluster_financial-services_banks-regional.csv
├── cluster_technology_software-application.csv
├── cluster_consumer-cyclical_furnishings.csv
├── cluster_healthcare_biotechnology.csv
├── cluster_communication-services_advertising.csv
└── cluster_technology_semiconductors.csv
```

### 2. Tính Alpha Signals

```mermaid
flowchart LR
    subgraph MR["Mean Reversion"]
        MR1["Cointegration Test"] --> MR2["Z-Score"]
        MR2 --> MR3["Signal: Giá dưới fair value?"]
    end

    subgraph MOM["Momentum"]
        MOM1["Return 60 ngày"] --> MOM2["Cross-Sectional Rank"]
        MOM2 --> MOM3["Signal: Xu hướng mạnh?"]
    end

    subgraph VB["Volatility Breakout"]
        VB1["Vol ngắn hạn / Vol dài hạn"] --> VB2["Z-Score"]
        VB2 --> VB3["Signal: Vol đang tăng?"]
    end

    subgraph XSR["Short-Term Reversal"]
        XSR1["Return 5 ngày"] --> XSR2["Cross-Sectional"]
        XSR2 --> XSR3["Signal: Oversold/Overbought?"]
    end

    subgraph VAL["Value"]
        VAL1["Vị trí trong 52-week range"] --> VAL2["Normalize"]
        VAL2 --> VAL3["Signal: Gần low hay high?"]
    end
```

### 3. ML Combination

```mermaid
flowchart TD
    A["5 Alpha Scores"] --> B["Ridge Regression"]
    B --> C["Học Weights"]
    
    D["Weights Learned:"] --> E["MR: +0.0004"]
    D --> F["Mom: -0.0003"]
    D --> G["VB: +0.0004"]
    D --> H["XSR: +0.0009"]
    D --> I["Val: +0.0007"]
    
    E & F & G & H & I --> J["Combined = Σ weight × alpha"]
```

### 4. Strategy & Position Sizing

```mermaid
flowchart TD
    A["Combined Score"] --> B{Score > 0.3?}
    B -->|Yes| C["STRONG BUY<br/>30% position"]
    B -->|No| D{Score > 0.1?}
    D -->|Yes| E["BUY<br/>20% position"]
    D -->|No| F{Score > -0.1?}
    F -->|Yes| G["HOLD<br/>0%"]
    F -->|No| H{Score > -0.3?}
    H -->|Yes| I["REDUCE<br/>-10%"]
    H -->|No| J["SELL<br/>-20%"]
```

### 5. Backtest Engine

```mermaid
flowchart TD
    A["Load Signals"] --> B["For each day t"]
    B --> C["Get target weights"]
    C --> D["Calculate position changes"]
    D --> E["Apply transaction costs"]
    E --> F["Calculate daily return"]
    F --> G["Update equity curve"]
    G --> H{Last day?}
    H -->|No| B
    H -->|Yes| I["Calculate final metrics"]
```

### 6. Output Files

| File | Nội dung |
|------|----------|
| `equity_*.csv` | Equity curve theo ngày |
| `result_*.csv` | 13 performance metrics |
| `trades_*.csv` | Chi tiết từng giao dịch |
| `signals_*.csv` | Tín hiệu alpha theo ngày |
| `Final_Report.csv` | Tổng hợp tất cả clusters |

### 7. Dashboard Flow

```mermaid
flowchart LR
    A["User chọn Scenario"] --> B["Load dữ liệu"]
    B --> C["Tab 1: Grade"]
    B --> D["Tab 2: Charts"]
    B --> E["Tab 3: Signals"]
    
    C --> C1["Sharpe > 1.5 → A"]
    C --> C2["CAGR > 30% → Excellent"]
    
    D --> D1["Equity Curve"]
    D --> D2["Drawdown Chart"]
    D --> D3["Insights Chi Tiết"]
    
    E --> E1["Alpha Breakdown"]
    E --> E2["Next Trade Recommendation"]
```

---

## Metrics Đánh Giá

```mermaid
pie title Trọng Số Đánh Giá
    "Sharpe Ratio" : 40
    "CAGR" : 30
    "Max Drawdown" : 20
    "Win Rate" : 10
```

| Điểm | Grade | Ý Nghĩa |
|------|-------|---------|
| 90-100 | A+ | Xuất sắc |
| 80-89 | A | Tuyệt vời |
| 70-79 | B+ | Rất tốt |
| 60-69 | B | Tốt |
| 50-59 | C | Trung bình |
| < 50 | D | Cần cải thiện |

---

## Kết Quả Tốt Nhất

```
Cluster: Banks Regional
├── Sharpe Ratio: 1.58 (Grade A)
├── CAGR: 55.2%
├── Total Return: 7914%
├── Max Drawdown: -48.6%
└── Win Rate: 53.7%
```

---

*Pipeline hoàn chỉnh từ dữ liệu thô → Alpha signals → ML → Strategy → Backtest → Dashboard*
