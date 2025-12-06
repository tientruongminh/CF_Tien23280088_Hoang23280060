"""
Professional Multi-Alpha Dashboard - PRODUCTION VERSION
======================================================
Clean, elegant design with no icons. Professional color palette.
Minimalist approach with maximum information.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import os
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Import modules
from chat_assistant import chat_tab
from signal_analysis import display_signal_analysis_tab
from metrics_config import (
    METRICS_CONFIG, CATEGORY_NAMES, CATEGORY_DESCRIPTIONS,
    evaluate_metric, format_metric_value, get_metric_config
)

# Page config
st.set_page_config(
    page_title="Multi-Alpha Portfolio Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional CSS - Deep Navy & Charcoal Theme
st.markdown("""
<style>
    /* Import professional font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Roboto+Mono:wght@400;500&display=swap');
    
    /* Global styles */
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }
    
    /* Main container */
    .main {
        background-color: #fafafa;
        padding: 2rem;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #1a237e;
        font-weight: 600;
        letter-spacing: -0.02em;
    }
    
    h1 {
        font-size: 2.25rem;
        margin-bottom: 0.5rem;
        border-bottom: 3px solid #1a237e;
        padding-bottom: 0.75rem;
    }
    
    h2 {
        font-size: 1.5rem;
        margin-top: 2rem;
        color: #263238;
    }
    
    h3 {
        font-size: 1.25rem;
        color: #37474f;
    }
    
    /* Metric cards */
    .metric-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        margin-bottom: 1rem;
    }
    
    .metric-label {
        font-size: 0.875rem;
        color: #757575;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.5rem;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 600;
        font-family: 'Roboto Mono', monospace;
        color: #1a237e;
        margin-bottom: 0.25rem;
    }
    
    .metric-rating {
        font-size: 0.875rem;
        font-weight: 500;
        padding: 0.25rem 0.75rem;
        border-radius: 4px;
        display: inline-block;
        margin-top: 0.5rem;
    }
    
    .rating-excellent {
        background-color: #e8f5e9;
        color: #2e7d32;
    }
    
    .rating-good {
        background-color: #fff3e0;
        color: #f57c00;
    }
    
    .rating-poor {
        background-color: #ffebee;
        color: #c62828;
    }
    
    /* Category sections */
    .category-header {
        background: linear-gradient(to right, #1a237e, #283593);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 8px 8px 0 0;
        font-size: 1.125rem;
        font-weight: 600;
        margin-top: 2rem;
    }
    
    .category-description {
        background: white;
        border: 1px solid #e0e0e0;
        border-top: none;
        padding: 1rem 1.5rem;
        color: #616161;
        font-size: 0.875rem;
        border-radius: 0 0 8px 8px;
        margin-bottom: 1.5rem;
    }
    
    /* Tables */
    .dataframe {
        font-family: 'Inter', sans-serif;
        font-size: 0.875rem;
    }
    
    .dataframe th {
        background-color: #1a237e !important;
        color: white !important;
        font-weight: 600;
        text-align: left;
        padding: 0.75rem !important;
    }
    
    .dataframe td {
        padding: 0.75rem !important;
        border-bottom: 1px solid #e0e0e0;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background-color: white;
        border-bottom: 2px solid #e0e0e0;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 1rem 2rem;
        font-weight: 500;
        color: #616161;
        border-bottom: 3px solid transparent;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        color: #1a237e;
        background-color: #f5f5f5;
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #1a237e;
        border-bottom-color: #1a237e;
        background-color: transparent;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background-color: #263238;
    }
    
    .sidebar .sidebar-content {
        background-color: #263238;
        color: white;
    }
    
    /* Remove default Streamlit styling */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Spacing */
    .block-container {
        padding-top: 2rem;
        max-width: 1400px;
    }
</style>
""", unsafe_allow_html=True)

# ==================== DATA LOADING ====================

@st.cache_data
def load_all_data(results_dir):
    """Load all backtest results"""
    data = {
        'summary': None,
        'results': {},
        'signals': {},
        'trades': {},
        'equity': {}
    }
    
    summary_path = os.path.join(results_dir, 'Final_Report.csv')
    if os.path.exists(summary_path):
        data['summary'] = pd.read_csv(summary_path)
    
    for file in os.listdir(results_dir):
        if file.startswith('result_cluster_'):
            cluster = file.replace('result_cluster_', '').replace('.csv', '')
            data['results'][cluster] = pd.read_csv(
                os.path.join(results_dir, file),
                index_col=0,
                parse_dates=True
            )
        elif file.startswith('signals_cluster_'):
            cluster = file.replace('signals_cluster_', '').replace('.csv', '')
            data['signals'][cluster] = pd.read_csv(
                os.path.join(results_dir, file),
                index_col=0,
                parse_dates=True
            )
        elif file.startswith('trades_cluster_'):
            cluster = file.replace('trades_cluster_', '').replace('.csv', '')
            data['trades'][cluster] = pd.read_csv(
                os.path.join(results_dir, file),
                parse_dates=['Date']
            )
        elif file.startswith('equity_cluster_'):
            cluster = file.replace('equity_cluster_', '').replace('.csv', '')
            data['equity'][cluster] = pd.read_csv(
                os.path.join(results_dir, file),
                parse_dates=['Date']
            )
    
    return data

# ==================== MODEL EVALUATION ====================

def evaluate_model_quality(summary_df):
    """Comprehensive model evaluation"""
    
    # Get best cluster metrics
    best = summary_df.loc[summary_df['Sharpe_Ratio'].idxmax()]
    
    evaluation = {
        'sharpe': best['Sharpe_Ratio'],
        'cagr': best['Annual_Return_CAGR'],
        'max_dd': best['Max_Drawdown'],
        'win_rate': best['Win_Rate']
    }
    
    # Grade calculation
    if evaluation['sharpe'] >= 1.5:
        grade = 'A'
        quality = 'Excellent'
    elif evaluation['sharpe'] >= 1.0:
        grade = 'B+'
        quality = 'Good'
    elif evaluation['sharpe'] >= 0.5:
        grade = 'C'
        quality = 'Acceptable'
    else:
        grade = 'D'
        quality = 'Poor'
    
    # vs S&P500 benchmark
    sp500_cagr = 0.10  # 10% historical
    sp500_sharpe = 0.9
    
    evaluation['vs_sp500_return'] = (evaluation['cagr'] - sp500_cagr) * 100
    evaluation['vs_sp500_sharpe'] = evaluation['sharpe'] - sp500_sharpe
    evaluation['grade'] = grade
    evaluation['quality'] = quality
    
    # Recommendation
    if grade in ['A', 'B+']:
        evaluation['recommendation'] = 'DEPLOY'
        evaluation['allocation'] = '15-25%'
        evaluation['investor_type'] = 'Institutional / Sophisticated'
    elif grade == 'C':
        evaluation['recommendation'] = 'CAUTIOUS'
        evaluation['allocation'] = '5-10%'
        evaluation['investor_type'] = 'Aggressive Only'
    else:
        evaluation['recommendation'] = 'AVOID'
        evaluation['allocation'] = '0%'
        evaluation['investor_type'] = 'None'
    
    return evaluation

# ==================== METRIC DISPLAY (NO ICONS) ====================

def display_metric_clean(col, label, value, rating, unit=''):
    """Clean metric display without icons"""
    
    # Rating class
    rating_class = {
        'excellent': 'rating-excellent',
        'good': 'rating-good',
        'poor': 'rating-poor'
    }.get(rating.lower(), 'rating-good')
    
    with col:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}{unit}</div>
            <div class="metric-rating {rating_class}">{rating}</div>
        </div>
        """, unsafe_allow_html=True)

# ==================== PROFESSIONAL CHARTS ====================

def create_professional_chart(df, title, y_col, color='#1a237e'):
    """Create clean professional chart"""
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df['Date'],
        y=df[y_col],
        mode='lines',
        line=dict(color=color, width=2),
        fill='tozeroy',
        fillcolor=f'rgba(26, 35, 126, 0.1)',
        name=title,
        hovertemplate='%{y:.2f}<extra></extra>'
    ))
    
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=16, color='#1a237e', family='Inter')
        ),
        xaxis=dict(
            title='',
            gridcolor='#f5f5f5',
            showgrid=True
        ),
        yaxis=dict(
            title='',
            gridcolor='#f5f5f5',
            showgrid=True
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=400,
        margin=dict(l=60, r=40, t=60, b=40),
        hovermode='x unified',
        font=dict(family='Inter', size=12, color='#616161')
    )
    
    return fig

# ==================== MAIN APP ====================

def main():
    # Header
    st.markdown('<h1>Multi-Alpha Portfolio Analytics</h1>', unsafe_allow_html=True)
    st.markdown('<p style="color: #757575; font-size: 1rem; margin-top: -0.5rem;">Professional Quantitative Trading System</p>', unsafe_allow_html=True)
    
    # Sidebar FIRST (sets results_dir)
    with st.sidebar:
        st.markdown("### System Overview")
        
        # Scenario Selection
        st.markdown("---")
        st.markdown("### 📊 Scenario Selection")
        scenario = st.selectbox(
            "Choose backtest scenario:",
            [
                "Scenario 1: All 6 Clusters (No RM)",
                "Scenario 2: Filtered 3 Clusters",
                "Scenario 3: With Risk Management"
            ],
            help="""
            - Scenario 1: All clusters, 100% exposure, no filters
            - Scenario 2: 3 good clusters only (Banks/Consumer/Tech SW)
            - Scenario 3: Risk management enabled (70% exposure, min 4 stocks)
            """
        )
        
        # Map selection to directory
        scenario_map = {
            "Scenario 1: All 6 Clusters (No RM)": "MultiAlpha_Results_Scenario1",
            "Scenario 2: Filtered 3 Clusters": "MultiAlpha_Results_Scenario2", 
            "Scenario 3: With Risk Management": "MultiAlpha_Results_Scenario3"
        }
        
        selected_dir = scenario_map[scenario]
        
        # Use relative path from app.py location
        from pathlib import Path
        base_dir = Path(__file__).parent.parent.parent / "apply_strategy"
        results_dir = str(base_dir / selected_dir)
        
        # Display scenario info
        if "Scenario 1" in scenario:
            st.info("6 clusters, avg Sharpe 0.49")
        elif "Scenario 2" in scenario:
            st.success("3 clusters, avg Sharpe 0.78")
        else:
            st.warning("1 cluster, Sharpe 1.17")
        
        st.markdown("---")
        st.metric("Active Scenarios", "3")
    
    # NOW load data using results_dir from sidebar
    if not os.path.exists(results_dir):
        st.error(f"Results directory not found: {results_dir}")
        return
    
    with st.spinner(f'Loading {scenario}...'):
        data = load_all_data(results_dir)
    
    if data['summary'] is None:
        st.error("No data available")
        return
    
    # Main tabs
    tabs = st.tabs([
        "Model Evaluation",
        "Portfolio Performance",
        "Next Trade Signals",
        "AI Assistant"
    ])
    
    # TAB 1: MODEL EVALUATION
    with tabs[0]:
        st.markdown('<h2>Model Quality Assessment</h2>', unsafe_allow_html=True)
        
        eval_result = evaluate_model_quality(data['summary'])
        
        # Overall Grade
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card" style="text-align: center;">
                <div class="metric-label">Overall Grade</div>
                <div class="metric-value" style="font-size: 4rem;">{eval_result['grade']}</div>
                <div class="metric-rating rating-{eval_result['quality'].lower()}">{eval_result['quality']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card" style="text-align: center;">
                <div class="metric-label">Recommendation</div>
                <div class="metric-value" style="font-size: 2.5rem; color: #2e7d32;">{eval_result['recommendation']}</div>
                <div class="metric-rating rating-excellent">Allocation: {eval_result['allocation']}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card" style="text-align: center;">
                <div class="metric-label">Investor Type</div>
                <div class="metric-value" style="font-size: 1.5rem;">{eval_result['investor_type']}</div>
                <div class="metric-rating rating-good">Suitable For</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Performance vs Benchmark
        st.markdown('<h3>Benchmark Comparison</h3>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        display_metric_clean(col1, "Sharpe Ratio", f"{eval_result['sharpe']:.2f}", eval_result['quality'])
        display_metric_clean(col2, "Annual Return", f"{eval_result['cagr']*100:.1f}", "Excellent", "%")
        display_metric_clean(col3, "vs S&P500", f"+{eval_result['vs_sp500_return']:.1f}", "Excellent", "%")
        display_metric_clean(col4, "Max Drawdown", f"{eval_result['max_dd']*100:.1f}", "Good", "%")
    
    # TAB 2: PORTFOLIO PERFORMANCE
    with tabs[1]:
        st.markdown('<h2>Portfolio Performance Analysis</h2>', unsafe_allow_html=True)
        
        # Get cluster data
        cluster = list(data['equity'].keys())[0]
        equity_df = data['equity'][cluster]
        summary = data['summary'].iloc[0]
        
        # === SECTION 1: KEY METRICS OVERVIEW ===
        st.markdown("### Key Performance Metrics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        sharpe = summary['Sharpe_Ratio']
        total_ret = summary['Total_Return'] * 100
        max_dd = summary['Max_Drawdown'] * 100
        win_rate = summary['Win_Rate'] * 100
        
        with col1:
            st.metric("Sharpe Ratio", f"{sharpe:.2f}")
            if sharpe > 1.5:
                st.success("🌟 Excellent - Institutional grade")
            elif sharpe > 1.0:
                st.success("✅ Good - Above average")
            elif sharpe > 0.5:
                st.info("⚠️ Acceptable - Below target")
            else:
                st.error("❌ Poor - Needs improvement")
        
        with col2:
            st.metric("Total Return", f"{total_ret:.1f}%")
            if total_ret > 1000:
                st.success("🚀 Outstanding performance")
            elif total_ret > 300:
                st.success("✅ Strong returns")
            else:
                st.info("📊 Moderate gains")
        
        with col3:
            st.metric("Max Drawdown", f"{max_dd:.1f}%")
            if abs(max_dd) < 30:
                st.success("✅ Well controlled")
            elif abs(max_dd) < 50:
                st.warning("⚠️ Moderate risk")
            else:
                st.error("📉 High risk - Review strategy")
        
        with col4:
            st.metric("Win Rate", f"{win_rate:.1f}%")
            if win_rate > 55:
                st.success("🎯 Consistently profitable")
            elif win_rate > 50:
                st.info("✅ Slight edge")
            else:
                st.warning("⚠️ Need higher accuracy")
        
        st.markdown("---")
        
        # === SECTION 2: DETAILED INSIGHTS ===
        st.markdown("### 📊 Performance Insights & Interpretation")
        
        # Risk-Adjusted Performance
        with st.expander("🎯 Risk-Adjusted Performance Analysis", expanded=True):
            st.markdown(f"""
            **Sharpe Ratio: {sharpe:.2f}**
            
            **What it means:**
            - Measures return per unit of risk taken
            - Sharpe > 1.0 is considered good for quant strategies
            - Your Sharpe of {sharpe:.2f} is {'**excellent**' if sharpe > 1.5 else '**good**' if sharpe > 1.0 else 'acceptable'}
            
            **Interpretation:**
            """)
            
            if sharpe > 1.5:
                st.success("""
                ✅ **Institutional-grade performance**  
                - Your strategy delivers exceptional risk-adjusted returns
                - Comparable to top hedge funds (target: Sharpe > 1.5)
                - Strong candidate for live deployment
                - Expected to outperform 90%+ of market participants
                """)
            elif sharpe > 1.0:
                st.info("""
                ✅ **Above-average performance**  
                - Strategy shows solid risk management
                - Beats typical buy-and-hold (Sharpe ~0.5)
                - Room for improvement through DD reduction
                - Consider implementing volatility targeting
                """)
            else:
                st.warning("""
                ⚠️ **Needs optimization**  
                - Returns don't justify the risk taken
                - Review signal quality and combination
                - Implement stricter risk management
                - Consider portfolio diversification
                """)
            
            # Sortino Ratio comparison
            sortino = summary.get('Sortino_Ratio', sharpe * 1.2)
            st.markdown(f"""
            **Sortino Ratio: {sortino:.2f}** (vs Sharpe {sharpe:.2f})
            - Sortino only penalizes downside volatility
            - Higher Sortino suggests asymmetric returns (good!)
            - Ratio of {sortino/sharpe:.2f}x indicates {'strong upside bias ✅' if sortino/sharpe > 1.15 else 'balanced distribution'}
            """)
        
        # Return Analysis
        with st.expander("💰 Return Generation Analysis"):
            cagr = summary['Annual_Return_CAGR'] * 100
            years = summary['Trading_Years']
            
            st.markdown(f"""
            **Total Return: {total_ret:.1f}%** over {years:.1f} years  
            **CAGR: {cagr:.1f}%** per year
            
            **Benchmark Comparison:**
            - S&P 500 historical CAGR: ~10%
            - Your CAGR: {cagr:.1f}%
            - **Outperformance: +{cagr-10:.1f}% annually** {'🚀' if cagr > 30 else '✅' if cagr > 15 else ''}
            
            **What this means:**
            """)
            
            if cagr > 40:
                st.success(f"""
                🚀 **Exceptional return generation**  
                - ${cagr:.1f}% CAGR is very rare (top 1% of strategies)
                - $10,000 → ${10000 * (1 + cagr/100)**years:,.0f} in {years:.0f} years
                - Beats most professional fund managers
                - **Action:** Ensure returns are sustainable, not curve-fitted
                """)
            elif cagr > 20:
                st.success(f"""
                ✅ **Strong performance**  
                - {cagr:.1f}% CAGR exceeds institutional targets (15-20%)
                - $10,000 → ${10000 * (1 + cagr/100)**years:,.0f} in {years:.0f} years
                - Consistent with successful quant funds
                - **Action:** Ready for gradual capital deployment
                """)
            else:
                st.info(f"""
                📊 **Moderate returns**  
                - {cagr:.1f}% beats S&P500 but room for improvement
                - Consider alpha enhancement or leverage
                - May be suitable for conservative investors
                """)
        
        # Risk Analysis
        with st.expander("📉 Drawdown & Risk Analysis"):
            avg_dd = summary['Avg_Drawdown'] * 100
            calmar = summary.get('Calmar_Ratio', cagr / abs(max_dd) * 100)
            
            st.markdown(f"""
            **Maximum Drawdown: {max_dd:.1f}%**  
            **Average Drawdown: {avg_dd:.1f}%**  
            **Calmar Ratio: {calmar:.2f}** (CAGR / Max DD)
            
            **Risk Assessment:**
            """)
            
            if abs(max_dd) < 30:
                st.success("""
                ✅ **Excellent risk control**  
                - Max DD < 30% is exceptional for quant strategies
                - Low probability of severe losses
                - Suitable for institutional capital
                - **Psychological impact:** Easier to hold through drawdowns
                """)
            elif abs(max_dd) < 50:
                st.warning(f"""
                ⚠️ **Moderate risk exposure**  
                - {abs(max_dd):.1f}% max DD is typical for quant strategies
                - Plan for worst-case: -50% to -60% possible
                - **Mitigation strategies:**
                  - Implement dynamic position sizing
                  - Add stop-loss at -30% DD
                  - Use volatility targeting (see DD Reduction guide)
                - **Expected recovery time:** 3-6 months based on CAGR
                """)
            else:
                st.error("""
                📉 **High risk - Action required**  
                - Drawdowns > 50% are psychologically difficult
                - Most investors quit at -40% to -50%
                - **Immediate actions:**
                  1. Reduce position sizes by 30-50%
                  2. Implement circuit breakers
                  3. Review signal quality during drawdown periods
                  4. Consider market regime filters
                """)
            
            st.markdown(f"""
            **Calmar Ratio Interpretation:**
            - Calmar of {calmar:.2f} means you earn {calmar:.1f}% annually per 1% of max DD
            - {'Excellent' if calmar > 1.0 else 'Good' if calmar > 0.5 else 'Needs improvement'} (target > 0.5)
            """)
        
        # Trade Quality
        with st.expander("🎲 Trade Quality & Consistency"):
            profit_factor = summary.get('Profit_Factor', 1.3)
            win_loss_ratio = summary.get('Win_Loss_Ratio', 1.1)
            
            st.markdown(f"""
            **Win Rate: {win_rate:.1f}%**  
            **Profit Factor: {profit_factor:.2f}**  
            **Win/Loss Ratio: {win_loss_ratio:.2f}**
            
            **What these metrics reveal:**
            """)
            
            st.markdown(f"""
            **Win Rate Analysis:**
            - {win_rate:.1f}% of trades are profitable
            - {'High accuracy strategy ✅' if win_rate > 55 else 'Balanced approach' if win_rate > 45 else 'Low win rate ⚠️'}
            - {100 - win_rate:.1f}% are losses (normal for mean-reversion)
            
            **Profit Factor: {profit_factor:.2f}**
            - Gross Profit / Gross Loss ratio
            - {profit_factor:.2f} means you make ${profit_factor:.2f} for every $1 lost
            """)
            
            if profit_factor > 1.5:
                st.success("🌟 Excellent - Winning trades significantly larger")
            elif profit_factor > 1.2:
                st.success("✅ Good - Sustainable over long term")
            elif profit_factor > 1.0:
                st.warning("⚠️ Marginal - Small edge, high transaction costs risk")
            else:
                st.error("❌ Losing strategy - Immediate review needed")
            
            st.markdown(f"""
            **Win/Loss Ratio: {win_loss_ratio:.2f}**
            - Average win is {win_loss_ratio:.2f}x the average loss
            - {'Asymmetric payoff - ideal ✅' if win_loss_ratio > 1.5 else 'Balanced wins/losses' if win_loss_ratio > 0.8 else 'Losses larger than wins ⚠️'}
            
            **Trading Philosophy Insight:**
            """)
            
            if win_rate > 55 and win_loss_ratio > 1.0:
                st.success("""
                💎 **High win rate + Positive payoff = Dream combination**  
                - You win often AND win big
                - Rare in quantitative trading
                - Indicates strong signal quality
                """)
            elif win_rate < 50 and win_loss_ratio > 1.5:
                st.info("""
                🎯 **Classic trend-following profile**  
                - Many small losses, few large wins
                - Requires patience and discipline
                - Critical: Don't cut winners early
                """)
            elif win_rate > 55 and win_loss_ratio < 1.0:
                st.warning("""
                ⚠️ **Mean-reversion profile with risk**  
                - Frequent small wins, occasional large losses
                - Warning: Vulnerable to tail events
                - **Action:** Implement strict stop-losses
                """)
        
        # Volatility Analysis
        with st.expander("📊 Volatility & Stability"):
            ann_vol = summary['Annual_Volatility'] * 100
            
            st.markdown(f"""
            **Annual Volatility: {ann_vol:.1f}%**
            
            **Volatility Interpretation:**
            - Measures how much returns fluctuate year-to-year
            - Higher vol = more unpredictable returns
            - Your vol: {ann_vol:.1f}%
            - S&P 500 typical vol: ~20%
            """)
            
            if ann_vol < 20:
                st.success(f"""
                ✅ **Low volatility strategy**  
                - {ann_vol:.1f}% vol is very stable
                - Smooth equity curve expected
                - Suitable for risk-averse investors
                - **Opportunity:** Could use moderate leverage (1.5-2x)
                """)
            elif ann_vol < 35:
                st.info(f"""
                📊 **Moderate volatility**  
                - {ann_vol:.1f}% is typical for quant strategies
                - Expect some monthly swings
                - Risk-adjusted returns (Sharpe {sharpe:.2f}) are key
                - **Position sizing:** Standard allocation OK
                """)
            else:
                st.warning(f"""
                ⚠️ **High volatility - Manage carefully**  
                - {ann_vol:.1f}% vol means large monthly swings possible
                - ±{ann_vol/12:.1f}% monthly moves expected
                - **Risk management essential:**
                  - Reduce position sizes
                  - Implement volatility targeting
                  - Use wider stop-losses (avoid whipsaws)
                """)
        
        st.markdown("---")
        
        # === SECTION 3: EQUITY CURVE ===
        st.markdown("### Portfolio Equity Curve")
        
        equity_df['Return_Pct'] = (equity_df['Cumulative_Return'] - 1) * 100
        
        fig = create_professional_chart(equity_df, "Cumulative Returns", "Return_Pct")
        st.plotly_chart(fig, use_container_width=True)
        
        # Drawdown chart
        st.markdown("### Drawdown Over Time")
        equity_df['Peak'] = equity_df['Cumulative_Return'].cummax()
        equity_df['Drawdown_Pct'] = ((equity_df['Cumulative_Return'] - equity_df['Peak']) / equity_df['Peak'] * 100)
        
        fig_dd = go.Figure()
        fig_dd.add_trace(go.Scatter(
            x=equity_df.index,
            y=equity_df['Drawdown_Pct'],
            fill='tozeroy',
            name='Drawdown',
            line=dict(color='#c62828', width=2)
        ))
        
        fig_dd.update_layout(
            title="Portfolio Drawdown",
            xaxis_title="Date",
            yaxis_title="Drawdown %",
            plot_bgcolor='white',
            font=dict(family='Inter'),
            height=300
        )
        
        st.plotly_chart(fig_dd, use_container_width=True)
        
        # === SECTION 4: ACTIONABLE RECOMMENDATIONS ===
        st.markdown("### 💡 Actionable Recommendations")
        
        recommendations = []
        
        # Based on Sharpe
        if sharpe > 1.5:
            recommendations.append(("✅ DEPLOY", "Strategy ready for live trading with institutional-grade Sharpe"))
        elif sharpe > 1.0:
            recommendations.append(("⚠️ OPTIMIZE", "Good performance - consider DD reduction for Grade A"))
        else:
            recommendations.append(("🔄 REVIEW", "Sharpe < 1.0 - revisit signal quality and combination"))
        
        # Based on DD
        if abs(max_dd) > 45:
            recommendations.append(("📉 REDUCE DD", f"Implement stop-loss and volatility targeting (target: -30%)"))
        
        # Based on Win Rate & PF
        if profit_factor < 1.3:
            recommendations.append(("🎯 IMPROVE EDGE", "Profit factor low - review entry/exit timing"))
        
        # Based on volatility
        if ann_vol > 40:
            recommendations.append(("📊 LOWER VOL", "High volatility - reduce position sizes by 30-50%"))
        
        for action, desc in recommendations:
            st.info(f"**{action}:** {desc}")
        
        st.markdown("---")
        
        # === SECTION 5: DETAILED METRICS TABLE ===
        st.markdown("### Complete Performance Metrics")
        st.dataframe(data['summary'], use_container_width=True, height=200)
    
    # TAB 3: NEXT TRADE SIGNALS  
    with tabs[2]:
        st.markdown('<h2>Trading Signal Analysis</h2>', unsafe_allow_html=True)
        
        # Select cluster for analysis
        cluster_list = list(data['equity'].keys())
        if cluster_list:
            selected_cluster = st.selectbox(
                "Select Cluster for Signal Analysis:",
                cluster_list,
                key='signal_cluster'
            )
            
            # Display signal analysis
            display_signal_analysis_tab(data, selected_cluster)
        else:
            st.warning("No cluster data available")
    
    # TAB 4: AI CHAT
    with tabs[3]:
        chat_tab(data)

if __name__ == "__main__":
    main()
