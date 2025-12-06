import pandas as pd
import numpy as np
import os

def run_backtest(df_weights, df_close, threshold):
    '''Mô phỏng PnL với positions'''
    positions = pd.DataFrame(0.0, index=df_weights.index, columns=df_weights.columns)
    positions[df_weights > threshold] = 1
    positions[df_weights < -threshold] = -1
    
    daily_ret = df_close.pct_change()
    pnl = positions.shift(1) * daily_ret
    
    # Portfolio Return
    num_active = positions.abs().sum(axis=1)
    port_ret = pnl.sum(axis=1) / num_active.replace(0, 1)
    cum_ret = (1 + port_ret).cumprod()
    
    return positions, port_ret, cum_ret


def calculate_metrics(port_ret, cum_ret):
    """
    Tính đầy đủ các metrics đánh giá chiến lược.
    
    Returns dict với các metrics:
    - Return metrics: Total Return, Annual Return (CAGR)
    - Risk-adjusted: Sharpe, Sortino, Calmar
    - Drawdown: Max Drawdown, Avg Drawdown
    - Trade: Win Rate, Profit Factor, Avg Win/Loss
    """
    if cum_ret.empty or len(cum_ret) < 2:
        return {}
    
    # ==================== RETURN METRICS ====================
    total_return = cum_ret.iloc[-1] - 1
    
    # Annualized Return (CAGR)
    n_years = len(cum_ret) / 252
    if n_years > 0 and total_return > -1:
        annual_return = (1 + total_return) ** (1 / n_years) - 1
    else:
        annual_return = 0
    
    # ==================== RISK METRICS ====================
    daily_std = port_ret.std()
    annual_vol = daily_std * np.sqrt(252) if daily_std > 0 else 0
    
    # Sharpe Ratio (assuming risk-free = 0)
    sharpe = (port_ret.mean() / daily_std * np.sqrt(252)) if daily_std > 0 else 0
    
    # Sortino Ratio (chỉ tính downside volatility)
    downside_ret = port_ret[port_ret < 0]
    downside_std = downside_ret.std() if len(downside_ret) > 0 else 0
    sortino = (port_ret.mean() / downside_std * np.sqrt(252)) if downside_std > 0 else 0
    
    # ==================== DRAWDOWN METRICS ====================
    # Max Drawdown
    rolling_max = cum_ret.cummax()
    drawdown = (cum_ret - rolling_max) / rolling_max
    max_drawdown = drawdown.min()
    avg_drawdown = drawdown[drawdown < 0].mean() if (drawdown < 0).any() else 0
    
    # Calmar Ratio
    calmar = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0
    
    # ==================== TRADE METRICS ====================
    # Win Rate
    win_rate = (port_ret > 0).mean()
    
    # Profit Factor
    gross_profit = port_ret[port_ret > 0].sum()
    gross_loss = abs(port_ret[port_ret < 0].sum())
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else np.inf
    
    # Average Win / Average Loss
    avg_win = port_ret[port_ret > 0].mean() if (port_ret > 0).any() else 0
    avg_loss = abs(port_ret[port_ret < 0].mean()) if (port_ret < 0).any() else 0
    win_loss_ratio = avg_win / avg_loss if avg_loss > 0 else np.inf
    
    return {
        # Return Metrics
        'Total_Return': round(total_return, 4),
        'Annual_Return_CAGR': round(annual_return, 4),
        'Annual_Volatility': round(annual_vol, 4),
        
        # Risk-Adjusted Metrics  
        'Sharpe_Ratio': round(sharpe, 4),
        'Sortino_Ratio': round(sortino, 4),
        'Calmar_Ratio': round(calmar, 4),
        
        # Drawdown Metrics
        'Max_Drawdown': round(max_drawdown, 4),
        'Avg_Drawdown': round(avg_drawdown, 4),
        
        # Trade Metrics
        'Win_Rate': round(win_rate, 4),
        'Profit_Factor': round(profit_factor, 4),
        'Win_Loss_Ratio': round(win_loss_ratio, 4),
        
        # Additional Info
        'Total_Days': len(cum_ret),
        'Trading_Years': round(n_years, 2)
    }


def generate_trade_signals(df_weights, positions, df_close, scores_dict, cluster_name, capital=1_000_000_000):
    """
    Tạo bảng tín hiệu giao dịch chi tiết với:
    Date, Cluster, Ticker, Action, Shares_Qty, Close, Final_Weight, Score_MR, Score_Mom, Score_Val
    """
    tickers = df_weights.columns.tolist()
    records = []
    
    # Tạo previous position để xác định action
    prev_positions = positions.shift(1).fillna(0)
    
    for date in df_weights.index:
        for ticker in tickers:
            weight = df_weights.loc[date, ticker]
            pos = positions.loc[date, ticker]
            prev_pos = prev_positions.loc[date, ticker]
            close = df_close.loc[date, ticker]
            
            # Xác định Action
            if pos > 0 and prev_pos <= 0:
                action = "OPEN_LONG"
            elif pos < 0 and prev_pos >= 0:
                action = "OPEN_SHORT"
            elif pos == 0 and prev_pos != 0:
                action = "CLOSE"
            elif pos > 0:
                action = "HOLD_LONG"
            elif pos < 0:
                action = "HOLD_SHORT"
            else:
                action = "WAIT"
            
            # Tính số lượng cổ phiếu
            allocated_value = abs(weight) * capital
            shares_qty = int(allocated_value / close) if close > 0 else 0
            
            # Lấy scores từ từng alpha
            score_mr = scores_dict['MR'].loc[date, ticker] if 'MR' in scores_dict else np.nan
            score_mom = scores_dict['Mom'].loc[date, ticker] if 'Mom' in scores_dict else np.nan
            score_vb = scores_dict['VB'].loc[date, ticker] if 'VB' in scores_dict else np.nan
            score_xsr = scores_dict['XSR'].loc[date, ticker] if 'XSR' in scores_dict else np.nan
            score_val = scores_dict['Val'].loc[date, ticker] if 'Val' in scores_dict else np.nan
            
            records.append({
                'Date': date,
                'Cluster': cluster_name,
                'Ticker': ticker,
                'Action': action,
                'Shares_Qty': shares_qty,
                'Close': round(close, 2),
                'Final_Weight': round(weight, 4),
                'Position': pos,
                'Score_MR': round(score_mr, 4) if not pd.isna(score_mr) else np.nan,
                'Score_Mom': round(score_mom, 4) if not pd.isna(score_mom) else np.nan,
                'Score_VB': round(score_vb, 4) if not pd.isna(score_vb) else np.nan,
                'Score_XSR': round(score_xsr, 4) if not pd.isna(score_xsr) else np.nan,
                'Score_Val': round(score_val, 4) if not pd.isna(score_val) else np.nan
            })
    
    return pd.DataFrame(records)


def save_detailed_results(df_weights, positions, df_close, filename, output_dir, 
                          scores_dict=None, port_ret=None, cum_ret=None):
    '''Lưu kết quả chi tiết ra file CSV'''
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    cluster_name = filename.replace('.csv', '')
        
    # 1. Lưu file result cơ bản (như cũ)
    res_path = os.path.join(output_dir, f"result_{filename}")
    export_df = pd.concat([
        df_weights.add_prefix("Weight_"),
        positions.add_prefix("Pos_"),
        df_close.add_prefix("Close_")
    ], axis=1)
    export_df.to_csv(res_path)
    print(f"💾 Đã lưu file kết quả: {res_path}")
    
    # 2. Lưu file trade signals chi tiết (NẾU có scores_dict)
    if scores_dict is not None:
        signals_df = generate_trade_signals(
            df_weights, positions, df_close, scores_dict, cluster_name
        )
        signals_path = os.path.join(output_dir, f"trades_{filename}")
        signals_df.to_csv(signals_path, index=False)
        print(f"📊 Đã lưu trade signals: {signals_path}")
    
    # 3. Lưu equity curve (NẾU có cum_ret)
    if cum_ret is not None:
        equity_df = pd.DataFrame({
            'Date': cum_ret.index,
            'Cumulative_Return': cum_ret.values,
            'Daily_Return': port_ret.values if port_ret is not None else np.nan
        })
        equity_path = os.path.join(output_dir, f"equity_{filename}")
        equity_df.to_csv(equity_path, index=False)
        print(f"📈 Đã lưu equity curve: {equity_path}")


def print_metrics_summary(metrics, cluster_name):
    """In tóm tắt metrics ra console"""
    print(f"\n{'='*60}")
    print(f"📊 BACKTEST SUMMARY: {cluster_name}")
    print(f"{'='*60}")
    
    print(f"\n💰 RETURN METRICS:")
    print(f"   Total Return:     {metrics.get('Total_Return', 0)*100:.2f}%")
    print(f"   Annual Return:    {metrics.get('Annual_Return_CAGR', 0)*100:.2f}%")
    print(f"   Annual Volatility:{metrics.get('Annual_Volatility', 0)*100:.2f}%")
    
    print(f"\n⚖️ RISK-ADJUSTED METRICS:")
    print(f"   Sharpe Ratio:     {metrics.get('Sharpe_Ratio', 0):.2f}")
    print(f"   Sortino Ratio:    {metrics.get('Sortino_Ratio', 0):.2f}")
    print(f"   Calmar Ratio:     {metrics.get('Calmar_Ratio', 0):.2f}")
    
    print(f"\n📉 DRAWDOWN METRICS:")
    print(f"   Max Drawdown:     {metrics.get('Max_Drawdown', 0)*100:.2f}%")
    print(f"   Avg Drawdown:     {metrics.get('Avg_Drawdown', 0)*100:.2f}%")
    
    print(f"\n🎯 TRADE METRICS:")
    print(f"   Win Rate:         {metrics.get('Win_Rate', 0)*100:.2f}%")
    print(f"   Profit Factor:    {metrics.get('Profit_Factor', 0):.2f}")
    print(f"   Win/Loss Ratio:   {metrics.get('Win_Loss_Ratio', 0):.2f}")
    
    print(f"\n📅 PERIOD: {metrics.get('Total_Days', 0)} days ({metrics.get('Trading_Years', 0)} years)")
    print(f"{'='*60}\n")