# main.py -- phiên bản ML-learning Lambda, đầy đủ 3 Layer + Backtest + Enhanced Metrics

import os
import pandas as pd
import config

from data_loader import load_data
from backtest_engine import (
    calculate_metrics, 
    save_detailed_results,
    print_metrics_summary
)

# Import alphas
from alphas import (
    calculate_mr_score, calculate_mom_score,
    calculate_vb_score, calculate_xsr_score,
    calculate_val_score,
    train_lambda_model, predict_combined_score
)

# Risk management removed per user request

# -----------------------------------------------------
# LAYER 3: Score → Weight → Backtest
# -----------------------------------------------------

def score_to_target_weight(score, max_gross=1.0):
    """Convert combined ML score → portfolio weights"""
    abs_s = score.abs()
    row_sum = abs_s.sum(axis=1).replace(0, 1)

    w = score.div(row_sum, axis=0) * max_gross
    return w


def backtest_from_weights(target_w, df_close, trade_threshold=0.05):
    """Entry / Exit = threshold, weighted returns."""
    daily_ret = df_close.pct_change()

    # Positions: 1 = Long, -1 = Short, 0 = No position
    positions = pd.DataFrame(0.0, index=target_w.index, columns=target_w.columns)
    positions[target_w > trade_threshold] = 1
    positions[target_w < -trade_threshold] = -1
    
    # PnL calculation
    pnl = positions.shift(1) * daily_ret
    port_ret = pnl.sum(axis=1)
    cum_ret = (1 + port_ret).cumprod()

    return positions, port_ret, cum_ret


# -----------------------------------------------------
# MAIN PIPELINE
# -----------------------------------------------------

def main():
    if not os.path.exists(config.OUTPUT_DIR):
        os.makedirs(config.OUTPUT_DIR)

    files = [f for f in os.listdir(config.INPUT_DIR) if f.endswith(".csv")]
    summary = []

    print(f"🚀 Bắt đầu xử lý {len(files)} cụm...")
    print(f"📁 Input:  {config.INPUT_DIR}")
    print(f"📁 Output: {config.OUTPUT_DIR}")

    for f in files:
        try:
            cluster_name = f.replace('.csv', '')
            print(f"\n{'='*60}")
            print(f"📌 PROCESSING CLUSTER: {cluster_name}")
            print(f"{'='*60}")
            
            path = os.path.join(config.INPUT_DIR, f)

            # ===========================
            # 1. LOAD DATA
            # ===========================
            df_close = load_data(path)
            print(f"   📊 Loaded {len(df_close)} days, {len(df_close.columns)} tickers")
            
            if len(df_close) < config.WINDOW_VALUE:
                print("   ⚠️ Not enough data, skipping...")
                continue

            # ===========================
            # 2. LAYER 1: TÍNH TỪNG ALPHA (With VB Redesigned)
            # ===========================
            print("   🔢 Computing Alpha Signals...")
            scores = {
                "MR":  calculate_mr_score(df_close, config.WINDOW_COINT, config.WINDOW_Z_SCORE),
                "Mom": calculate_mom_score(df_close, config.WINDOW_MOM),
                "VB":  calculate_vb_score(df_close, config.WINDOW_VOL_SHORT, config.WINDOW_VOL_LONG),  
                # ↑ RE-ENABLED: VB redesigned with Vol Z-Score (independent from Mom)
                "XSR": calculate_xsr_score(df_close),  # Fixed NaN handling
                "Val": calculate_val_score(df_close, config.WINDOW_VALUE),
            }

            # Xuất raw signals
            all_signal = pd.concat([
                scores["MR"].add_prefix("MR_"),
                scores["Mom"].add_prefix("Mom_"),
                scores["VB"].add_prefix("VB_"),  # RE-ADDED
                scores["XSR"].add_prefix("XSR_"),
                scores["Val"].add_prefix("Val_"),
            ], axis=1)

            all_signal.to_csv(os.path.join(config.OUTPUT_DIR, f"signals_{f}"))
            print("   ✔ Saved all alpha signals")

            # ===========================
            # 3. LAYER 2: KẾT HỢP ALPHAS VỚI ML
            # ===========================
            print("  ⚙️ Preparing ML training data...")
            model = train_lambda_model(
                scores_dict=scores,
                df_close=df_close,
                alpha=1.0,
                horizon=1,
                min_history=252  # Fixed: use 252 directly
            )

            combined_score = predict_combined_score(scores, model)
            print("   ✔ Combined score từ ML-learning λ")

            # ===========================
            # 4. CHUYỂN SCORE → WEIGHT (Full exposure - no limits)
            # ===========================
            target_w = score_to_target_weight(combined_score, max_gross=1.0)  # 100% exposure
            positions, port_ret, cum_ret = backtest_from_weights(
                target_w,
                df_close,
                trade_threshold=config.THRESHOLD_ENTRY
            )

            # Save detailed results với scores_dict để tạo trade signals
            save_detailed_results(
                df_weights=target_w, 
                positions=positions, 
                df_close=df_close, 
                filename=f, 
                output_dir=config.OUTPUT_DIR,
                scores_dict=scores,
                port_ret=port_ret,
                cum_ret=cum_ret
            )

            # Calculate và in metrics
            stats = calculate_metrics(port_ret, cum_ret)
            stats["File"] = f
            summary.append(stats)

            # In tóm tắt metrics
            print_metrics_summary(stats, cluster_name)

        except Exception as e:
            import traceback
            print(f"❌ ERROR in {f}: {e}")
            traceback.print_exc()

    # ===========================
    # 5. SUMMARY TOÀN BỘ CLUSTERS
    # ===========================
    if summary:
        summary_df = pd.DataFrame(summary)
        
        # Sắp xếp theo Sharpe Ratio giảm dần
        summary_df = summary_df.sort_values('Sharpe_Ratio', ascending=False)
        
        summary_df.to_csv(
            os.path.join(config.OUTPUT_DIR, "Final_Report.csv"),
            index=False
        )
        
        print("\n" + "="*60)
        print("🏆 FINAL RANKING BY SHARPE RATIO")
        print("="*60)
        for i, row in summary_df.iterrows():
            sharpe = row.get('Sharpe_Ratio', 0)
            total_ret = row.get('Total_Return', 0)
            max_dd = row.get('Max_Drawdown', 0)
            file_name = row.get('File', 'Unknown')
            
            # Emoji based on Sharpe
            if sharpe > 1.0:
                emoji = "⭐"
            elif sharpe > 0.5:
                emoji = "✅"
            elif sharpe > 0:
                emoji = "😐"
            else:
                emoji = "❌"
            
            print(f"{emoji} {file_name[:45]:45} | Sharpe: {sharpe:6.2f} | Return: {total_ret*100:7.1f}% | MaxDD: {max_dd*100:6.1f}%")
        
        print("="*60)
        print("🎉 HOÀN TẤT TOÀN BỘ CỤM!")


if __name__ == "__main__":
    main()
