# Lab: Week 1 to Week 3
## 1. Collect Price–Volume Data

Download historical OHLC data: open, high, low, close

Include adjusted close and trading volume

### Yfinance Library
Dataset: [Kaggle](https://www.kaggle.com/datasets/hoanggvo/computational-finance)

This is our full-crawled version, contains the full ticket combined and each ticket price in separated, in 10 years period, those are not anything that having on the internet. 

There are samples in data/yfinance/per_symbol

If you refer VNese ticket, please checkout this version (we currently not using this for out main stream): [Kaggle](https://www.kaggle.com/datasets/khanhkdn/vietnam-stock-market-as-of-september-11-2025?select=all_stocks.csv)

## 2. Collect Fundamental Data

Download fundamental datasets (nếu có nguồn miễn phí)

Ví dụ: EPS, P/E, P/B, ROE, revenue, etc.

Job has been done: Using simfin (free public API key) to download Fundamental Data. 
Please check the codes in notebooks/simfin_demo.ipynb
The demo results are in data/simfin

## 3. Study Technical Indicators

Tham khảo sách, tài liệu online, blog, Google Search

Một số chỉ báo phổ biến: MA, EMA, RSI, MACD, Bollinger Bands, OBV, v.v.

## 4. Design Technical-Based Trading Strategies

Chuyển ý tưởng hoặc giả thuyết giao dịch thành biểu thức toán học / code

Xây dựng chiến lược dựa trên các technical indicators

Kiểm tra mô hình bằng dữ liệu giá – khối lượng lịch sử

## 5. Design Fundamental-Based Trading Strategies (Optional)

Xây dựng chiến lược dựa trên dữ liệu cơ bản (nếu có)

Gợi ý: phân loại growth stocks và value stocks bằng các tỷ số tài chính

## 6. Build Momentum Strategies

Thiết kế chiến lược momentum dựa trên dữ liệu price–volume



