
import os
import yfinance as yf
import pandas as pd


# 2️⃣ Đặt đường dẫn tới thư mục Drive của bạn
drive_folder = '/workspaces/CF_Tien23280088_Hoang23280060/Data'  # đổi lại nếu cần

# 3️⃣ Tạo thư mục nếu chưa có
os.makedirs(drive_folder, exist_ok=True)

# 4️⃣ Danh sách cổ phiếu VN30
tickers = [
    "VNM.VN","HPG.VN","FPT.VN","VCB.VN","VIC.VN",
    "MWG.VN","CTG.VN","BID.VN","SAB.VN","VHM.VN",
    "SSI.VN","STB.VN","GAS.VN","NVL.VN","PLX.VN",
    "MSN.VN","TCB.VN","MBB.VN","VRE.VN","VJC.VN"
]

# 5️⃣ Tải dữ liệu 10 năm
data = yf.download(
    tickers,
    start="2015-01-01",
    end="2025-10-11",
    interval="1d",
    group_by="ticker",
    auto_adjust=True
)

rows = []
for t in tickers:
    df = data[t].reset_index().assign(Symbol=t)
    df = df[["Symbol", "Date", "Open", "High", "Low", "Close", "Volume"]]
    rows.append(df)

final_df = pd.concat(rows, ignore_index=True)

# 6️⃣ Lưu vào file Excel trong Drive
output_path = os.path.join(drive_folder, "stock_10y_data.xlsx")
final_df.to_excel(output_path, index=False)

print(f"✅ Đã lưu dữ liệu 10 năm qua vào: {output_path}")

with pd.ExcelWriter("/workspaces/CF_Tien23280088_Hoang23280060/Data/stock_10y_data.xlsx") as writer:
    for ticker in tickers:
        df = data[ticker].reset_index()
        df.to_excel(writer, sheet_name=ticker.replace(".VN", ""), index=False)
