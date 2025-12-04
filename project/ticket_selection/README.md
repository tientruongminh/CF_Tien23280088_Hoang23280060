# Ticket Selection
Phần này sẽ làm về cách chọn ticket để sử dụng chiến thuật Pair Trading và các signal khác. 

## 0. Overview

Hiện tại, những tài nguyên đã có:
- Từ ~/labs/week123, nhóm đã có được dữ liệu price-volumn dataset của hơn 1808 ticket trong period 10 năm. 
- Các dạng data khác (Không sử dụng chính trong phần project)

Công việc hiện tại nhóm quyết định: Định nghĩa riêng một mini-sector, để chọn nhiều nhóm cổ phiếu (khoảng 5 nhóm, mỗi nhóm khoảng 10 cổ phiếu) để thực hiện các phân tích sâu hơn.

## 1. Nguyên tắc

Một cụm tốt cho pair trading bao gồm các tiêu chí sau:

### 1.1. Cùng loại business / sector rộng
Không nhất thiết phải đúng 100% GICS, nhưng bản chất phải giống nhau:
- Cùng ngành ngân hàng, big tech, nhà bán lẻ, dầu khí, tiện ích, v.v.
- Ý nghĩa: các cổ phiếu cùng chịu tác động của những yếu tố vĩ mô và sector giống nhau, thuận lợi để khai thác chênh lệch tương đối.

### 1.2. Thống kê giá khá giống nhau

- Return, volatility, beta, drawdown, pattern biến động tương đồng.

- Để nếu có mispricing ngắn hạn, khi bạn long/short trong cụm, spread có cơ hội “mean-revert”.

### 1.3. Đủ thanh khoản và size tương đương

- Không ghép 1 midcap thanh khoản vừa với 1 microcap cạn thanh khoản.

- Trong 1 cụm, cổ phiếu nên có dollar volume cùng “level”.

### 1.4. Có lịch sử correlation/cointegration tương đối cao

- Trong 1 cụm, đa số cặp có correlation dương, tương đối cao trên returns.

- Ít nhất một số cặp có cointegration ổn nếu bạn làm pairs kiểu statistical arbitrage cổ điển.

## 2. Những đặc trưng (features) dùng để định nghĩa cụm

### 2.1. Nhóm đặc trưng “hành vi giá”

Làm trên log-return ngày:

- Mean daily return: trung bình log-return, có thể dùng thêm annualized.

- Volatility: độ lệch chuẩn daily return (annualized).

- Beta với thị trường: Lấy SPY hoặc S&P 500 index làm benchmark, chạy hồi quy để có beta.

- Idiosyncratic volatility: phần residual sau khi trừ beta*market return.

- Skewness, kurtosis (tuỳ chọn): phản ánh phân phối tail.

Ý nghĩa:
Cùng beta, cùng vol ⇒ phản ứng tương tự với market shock.
Idio vol tương tự ⇒ độ “noise” riêng từng mã tương đương.

2.2. Nhóm đặc trưng “thanh khoản và size”

Từ data price–volume:

- Average dollar volume: $avg_dollar_vol = mean(close * volume)$ trong 6–12 tháng gần nhất.

- Turnover ratio proxy: Không có số lượng cổ phiếu lưu hành thì khó chính xác, nhưng bạn có thể lấy turnover tương đối bằng cách chuẩn hóa volume/volatility hay volume/price.

Điều kiện lọc:

- Loại bỏ mã có avg dollar volume quá thấp (khó long/short).

- Trong cụm, các mã nên có dollar volume cùng “order of magnitude”.

### 2.3. Nhóm đặc trưng “tương đồng động học”

Đây là phần quan trọng với pair trading:

#### 2.3.1. Rolling correlation matrix

- Lấy return 2–3 năm gần nhất, tính correlation giữa mọi cặp.

- Với mỗi mã, có thể dùng:

    - Correlation trung bình với các mã cùng sector “thô” (theo label yfinance nếu có)

    - Hoặc embedding theo PCA trên ma trận correlation.

#### 2.3.2. Factor / PCA embedding

- Chạy PCA trên ma trận returns (hoặc on covariance matrix).

- Lấy 3–5 principal components đầu làm features.

- Mã nào có vector loading gần nhau ⇒ hành vi giá tương tự theo các yếu tố chung.

#### 2.3.3 Cointegration score 

- Không nhất thiết dùng cho toàn bộ 1808 mã, nhưng có thể: Sau khi đã có cụm thô, test cointegration trong cụm để chọn cặp.

- Trong định nghĩa cụm, chỉ cần đảm bảo: trong cụm, tỷ lệ cặp cointegrated đủ tốt.

## 3. Định nghĩa cụm đề xuất

Một cụm là một tập từ 2 cổ phiếu ${s_1, s_2, ..., s_{n}}$

#### • Điều kiện về ngành
- Các mã thuộc **cùng một sector/industry rộng**  
  (theo GICS, ICB, hoặc label từ *yfinance*).

#### • Điều kiện về đặc tính thống kê
- **Volatility** nằm trong cùng một dải  
  (ví dụ cùng một **decile** trong toàn universe).
- **Beta với SPY** không chênh lệch quá một ngưỡng  
  (ví dụ: `|βᵢ − βⱼ| < 0.2`).
- **Bình quân pairwise correlation** của daily returns (2–3 năm gần nhất) trong cụm **> 0.5**.
- **Average dollar volume** của các mã không chênh nhau quá lớn  
  (tỷ lệ `max/min < 5`).

#### • Điều kiện về cointegration 
- Trong cụm tồn tại ít nhất vài cặp `(i, j)` có **p-value cointegration test < 0.05**.

---

### Như vậy “cụm” được đặc trưng bởi:
- **Giống nhau về economic exposure** (sector)  
- **Giống nhau về hành vi thống kê** (beta, volatility, factor loading)  
- **Có background correlation cao**  
- **Thanh khoản hợp lý**

## 4. Quá trình thực hiện

### 4.1. Lấy thông tin sector/industry của cổ phiếu

Sử dụng thư viện `yahooquery` để lấy thông tin của mã.
Notebook: notebooks/retrieve_sector_industry.ipynb

Output: sector_industry.csv

Visualization: 

![Ticket_Per_Sector](visualization/ticket_per_sector.png)

![Top_20_Industries](visualization/top_20_industries.png)


Nhận xét:
- Sector phân bố khá rộng: healthcare ~ 370, financial-services ~ 317, technology ~ 287, industrials ~ 174, consumer-cyclical ~ 149

- Industry cũng phân bố tương ứng khá chi tiết: biotechnology ~ 214, banks-regional ~ 197, software-application, asset-management, semiconductors, medical-devices…

Ở đây, nhóm quyết định tập trung vào nhóm sector $healthcare$ và industry $biotechnology$. Output file chi tiết filter ra nằm ở dataset/biotech_healthcare_tickers.csv

### 4.2. Volatility Calculation

#### 4.2.1. Định nghĩa Volatility

- Dùng log return ngày trên Close (Close ~ Adj Close)
- Lấy 252 phiên gần nhất (xấp xỉ 1 năm giao dịch)
- Volatility 1 năm:
$
\sigma_{\text{1y}} = \text{std}(\text{daily log return}) \times \sqrt{252}
$

#### 4.2.2 Code thực hiện && Kết quả

Notebook: notebooks/calculate_volatility.ipynb

Output: dataset/biotech_mid_vol.csv

### 4.3. Beta vs Spy

#### 4.3.1 Beta
Beta phản ánh mức độ nhạy của một cổ phiếu trước "thị trường chung".

Công thức tính cơ bản:
$$
\beta_i = \frac{\text{Cov}(r_i, r_m)}{\text{Var}(r_m)}
$$

Trong đó:
- $r_i$ = return của cổ phiếu i
- $r_m$ = return của **thị trường (market factor)**

Vì beta đo “mức độ biến động tương quan với thị trường”, nên ta cần phải có dữ liệu thị trường để đo:
- Cổ phiếu biotech A tăng 1%, thị trường tăng 0.5% → beta cao
- Cổ phiếu biotech B tăng 1%, thị trường giảm → beta khác

Nhóm quyết định sử dụng cổ phiếu SPY để đại diện cho thị trường.

#### 4.3.2. SPY

SPY = SPDR S&P 500 ETF Trust

→ Một quỹ ETF mô phỏng chỉ số S&P 500 (500 công ty lớn nhất nước Mỹ theo vốn hóa).



