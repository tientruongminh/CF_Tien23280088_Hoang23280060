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
        st.markdown('<h2>Portfolio Performance</h2>', unsafe_allow_html=True)
        
        # Equity curve
        cluster = list(data['equity'].keys())[0]
        equity_df = data['equity'][cluster]
        
        equity_df['Return_Pct'] = (equity_df['Cumulative_Return'] - 1) * 100
        
        fig = create_professional_chart(equity_df, "Cumulative Returns", "Return_Pct")
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed metrics table
        st.markdown('<h3>Performance Metrics</h3>', unsafe_allow_html=True)
        st.dataframe(data['summary'], use_container_width=True, height=300)
    
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
