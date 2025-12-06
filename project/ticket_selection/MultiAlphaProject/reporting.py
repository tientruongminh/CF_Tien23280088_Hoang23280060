import pandas as pd
import numpy as np
import os

def generate_full_breakdown(scores_dict, final_weights, close_prices, cluster_name, capital=1_000_000_000):
    """
    Tạo bảng chi tiết giải thích lý do vào lệnh cho từng mã.
    """
    df_list = []
    tickers = final_weights.columns
    
    for ticker in tickers:
        df_i = pd.DataFrame()
        df_i['Close'] = close_prices[ticker]
        # Lấy score từ các module alpha
        df_i['Score_MR'] = scores_dict['MR'][ticker]
        df_i['Score_Mom'] = scores_dict['Mom'][ticker]
        df_i['Score_VB'] = scores_dict['VB'][ticker]
        df_i['Score_XSR'] = scores_dict['XSR'][ticker]
        df_i['Score_Val'] = scores_dict['Val'][ticker]
        
        df_i['Final_Weight'] = final_weights[ticker]
        df_i['Ticker'] = ticker
        df_i['Cluster'] = cluster_name
        
        df_list.append(df_i)
        
    full_df = pd.concat(df_list).sort_index()
    
    # Logic xác định hành động (Action)
    full_df['Prev_Weight'] = full_df.groupby('Ticker')['Final_Weight'].shift(1)
    threshold = 0.2 
    
    conditions = [
        (full_df['Final_Weight'] > threshold) & (full_df['Prev_Weight'] <= threshold), # Mua Mới
        (full_df['Final_Weight'] < -threshold) & (full_df['Prev_Weight'] >= -threshold), # Bán Khống Mới
        (full_df['Final_Weight'].abs() <= threshold) & (full_df['Prev_Weight'].abs() > threshold), # Đóng Lệnh
        (full_df['Final_Weight'] > threshold), # Giữ Long
        (full_df['Final_Weight'] < -threshold) # Giữ Short
    ]
    choices = ['OPEN_LONG', 'OPEN_SHORT', 'CLOSE_POSITION', 'HOLD_LONG', 'HOLD_SHORT']
    
    full_df['Action'] = np.select(conditions, choices, default='WAIT')
    
    # Tính số lượng cổ phiếu (Position Sizing)
    # Vốn phân bổ = Weight * Tổng Vốn
    full_df['Allocated_Value'] = full_df['Final_Weight'] * capital
    full_df['Shares_Qty'] = (full_df['Allocated_Value'] / full_df['Close']).fillna(0).astype(int)
    
    return full_df

def save_daily_signal_report(full_df, output_dir):
    """Lưu file báo cáo tín hiệu giao dịch"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # 1. Lưu tín hiệu ngày mới nhất (Today's Action)
    last_date = full_df.index.max()
    latest_df = full_df[full_df.index == last_date].copy()
    
    # Chỉ lấy những mã CÓ HÀNH ĐỘNG hoặc ĐANG GIỮ
    active_df = latest_df[latest_df['Action'] != 'WAIT']
    
    report_name = f"Trade_Signals_{last_date.date()}.csv"
    report_path = os.path.join(output_dir, report_name)
    
    cols = ['Cluster', 'Ticker', 'Action', 'Shares_Qty', 'Close', 'Final_Weight', 
            'Score_MR', 'Score_Mom', 'Score_Val']
    
    # Append nếu file đã tồn tại (để gộp nhiều cụm vào 1 file báo cáo ngày)
    if os.path.exists(report_path):
        active_df[cols].to_csv(report_path, mode='a', header=False)
    else:
        active_df[cols].to_csv(report_path)
        
    print(f"   > 📝 Đã cập nhật tín hiệu giao dịch vào: {report_name}")
    return report_path