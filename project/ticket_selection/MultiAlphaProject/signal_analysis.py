"""
Signal Analysis & Next Trade Recommendations
============================================
Detailed alpha signal breakdown and position recommendations.
"""

import pandas as pd
import numpy as np
import streamlit as st
import plotly.graph_objects as go

def get_latest_signals_from_data(data, cluster_name):
    """
    Extract latest alpha signals for a cluster
    
    Returns dict with latest values for each alpha
    """
    if cluster_name not in data['signals']:
        return None
    
    signals_df = data['signals'][cluster_name]
    
    # Get latest row
    latest = signals_df.iloc[-1]
    
    # Organize by alpha
    alphas = {}
    for col in signals_df.columns:
        # Column format: Alpha_Ticker (e.g., MR_BAC, Mom_JPM)
        parts = col.split('_')
        if len(parts) >= 2:
            alpha_name = parts[0]
            ticker = '_'.join(parts[1:])
            
            if alpha_name not in alphas:
                alphas[alpha_name] = {}
            
            alphas[alpha_name][ticker] = latest[col]
    
    return alphas

def explain_alpha_signal(alpha_name, value):
    """
    Provide human-readable explanation of alpha signal
    """
    explanations = {
        'MR': {
            'positive': 'Price below fair value → Mean reversion opportunity',
            'negative': 'Price above fair value → Overvalued',
            'neutral': 'Price near fair value → No signal'
        },
        'Mom': {
            'positive': 'Strong upward trend → Momentum long',
            'negative': 'Downward trend → Momentum short/avoid',
            'neutral': 'No clear trend → Sideways'
        },
        'VB': {
            'positive': 'Volatility expanding → Breakout potential',
            'negative': 'Volatility contracting → Range-bound',
            'neutral': 'Normal volatility → No regime change'
        },
        'XSR': {
            'positive': 'Oversold → Reversal up expected',
            'negative': 'Overbought → Reversal down expected',
            'neutral': 'Neutral positioning'
        },
        'Val': {
            'positive': 'Near 52-week low → Value buy',
            'negative': 'Near 52-week high → Expensive',
            'neutral': 'Mid-range → Fair value'
        }
    }
    
    if alpha_name not in explanations:
        return "Unknown signal"
    
    # Classify value
    if value > 0.3:
        category = 'positive'
    elif value < -0.3:
        category = 'negative'
    else:
        category = 'neutral'
    
    return explanations[alpha_name][category]

def calculate_combined_score(alpha_values, model_weights):
    """
    Calculate combined score from individual alphas
    
    Parameters:
    - alpha_values: dict of {alpha_name: value}
    - model_weights: dict of {alpha_name: weight}
    
    Returns:
    - combined_score: float
    - breakdown: dict showing contribution of each alpha
    """
    combined = 0
    breakdown = {}
    
    alpha_order = ['MR', 'Mom', 'VB', 'XSR', 'Val']
    
    for alpha in alpha_order:
        if alpha in alpha_values and alpha in model_weights:
            contrib = alpha_values[alpha] * model_weights[alpha]
            combined += contrib
            breakdown[alpha] = contrib
    
    return combined, breakdown

def recommend_action(combined_score, vol_adjustment=1.0):
    """
    Recommend trading action based on combined score
    
    Returns:
    - action: str (STRONG BUY, BUY, HOLD, SELL, STRONG SELL)
    - color: str (for UI)
    - size_pct: float (position size %)
    """
    # Adjust thresholds by volatility
    threshold_high = 0.4 * vol_adjustment
    threshold_mid = 0.15 * vol_adjustment
    
    if combined_score > threshold_high:
        action = "STRONG BUY"
        color = "green"
        size_pct = 0.30  # 30%
    elif combined_score > threshold_mid:
        action = "BUY"
        color = "blue"
        size_pct = 0.20  # 20%
    elif combined_score > -threshold_mid:
        action = "HOLD"
        color = "gray"
        size_pct = 0.0
    elif combined_score > -threshold_high:
        action = "REDUCE"
        color = "orange"
        size_pct = -0.10  # Reduce 10%
    else:
        action = "SELL"
        color = "red"
        size_pct = -0.20  # Sell 20%
    
    return action, color, size_pct

def display_signal_analysis_tab(data, cluster_name, model_weights=None):
    """
    Display comprehensive signal analysis for a cluster
    """
    st.markdown(f'<h2>Signal Analysis: {cluster_name}</h2>', unsafe_allow_html=True)
    
    # Get latest signals
    alphas = get_latest_signals_from_data(data, cluster_name)
    
    if alphas is None:
        st.warning(f"No signal data available for {cluster_name}")
        return
    
    # Default model weights if not provided
    if model_weights is None:
        model_weights = {
            'MR': 0.0004,
            'Mom': -0.0003,
            'VB': 0.0004,
            'XSR': 0.0009,
            'Val': 0.0007
        }
    
    # For each ticker
    tickers = list(next(iter(alphas.values())).keys()) if alphas else []
    
    for ticker in tickers:
        with st.expander(f"📊 {ticker} - Detailed Analysis", expanded=True):
            
            # === SECTION 1: INDIVIDUAL ALPHAS ===
            st.markdown("### Individual Alpha Signals")
            
            alpha_data = []
            for alpha_name in ['MR', 'Mom', 'VB', 'XSR', 'Val']:
                if alpha_name in alphas and ticker in alphas[alpha_name]:
                    value = alphas[alpha_name][ticker]
                    explanation = explain_alpha_signal(alpha_name, value)
                    
                    alpha_data.append({
                        'Alpha': alpha_name,
                        'Value': f"{value:.3f}",
                        'Interpretation': explanation
                    })
            
            if alpha_data:
                df_alphas = pd.DataFrame(alpha_data)
                st.dataframe(df_alphas, use_container_width=True, hide_index=True)
            
            # === SECTION 2: ML COMBINATION ===
            st.markdown("### ML Combination")
            
            # Get alpha values for this ticker
            ticker_alphas = {
                alpha: alphas[alpha][ticker]
                for alpha in ['MR', 'Mom', 'VB', 'XSR', 'Val']
                if alpha in alphas and ticker in alphas[alpha]
            }
            
            # Calculate combined score
            combined, breakdown = calculate_combined_score(ticker_alphas, model_weights)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Combined Score", f"{combined:.4f}")
                
            with col2:
                # Formula
                formula_parts = []
                for alpha in ['MR', 'Mom', 'VB', 'XSR', 'Val']:
                    if alpha in model_weights:
                        formula_parts.append(f"{model_weights[alpha]:.4f}×{alpha}")
                
                st.code(f"Score = {' + '.join(formula_parts)}")
            
            # Breakdown chart
            if breakdown:
                fig = go.Figure(data=[
                    go.Bar(
                        x=list(breakdown.keys()),
                        y=list(breakdown.values()),
                        marker_color=['#2e7d32' if v > 0 else '#c62828' for v in breakdown.values()],
                        text=[f"{v:.4f}" for v in breakdown.values()],
                        textposition='outside'
                    )
                ])
                
                fig.update_layout(
                    title="Alpha Contribution Breakdown",
                    yaxis_title="Contribution to Combined Score",
                    height=300,
                    showlegend=False,
                    plot_bgcolor='white',
                    font=dict(family='Inter')
                )
                
                st.plotly_chart(fig, use_container_width=True)
            
            # === SECTION 3: POSITION SIZING ===
            st.markdown("### Position Sizing & Risk")
            
            # Estimate volatility (simplified)
            vol_estimate = 0.25  # 25% annualized (placeholder)
            vol_adjustment = 1.0 if vol_estimate < 0.30 else 0.85
            
            # Recommend action
            action, color, size_pct = recommend_action(combined, vol_adjustment)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(f"**Recommendation:**")
                st.markdown(f":{color}[**{action}**]")
            
            with col2:
                st.markdown("**Position Size:**")
                st.markdown(f"**{abs(size_pct)*100:.0f}%**")
            
            with col3:
                st.markdown("**Estimated Vol:**")
                st.markdown(f"**{vol_estimate*100:.0f}%**")
            
            # === SECTION 4: RATIONALE ===
            st.markdown("### Trade Rationale")
            
            # Find strongest signals
            sorted_alphas = sorted(
                ticker_alphas.items(),
                key=lambda x: abs(x[1]),
                reverse=True
            )
            
            rationale = []
            for alpha, value in sorted_alphas[:3]:  # Top 3
                if abs(value) > 0.2:  # Significant signal
                    direction = "positive" if value > 0 else "negative"
                    strength = "Strong" if abs(value) > 0.5 else "Moderate"
                    rationale.append(f"- **{alpha}** ({strength}, {value:.2f}): {explain_alpha_signal(alpha, value)}")
            
            if rationale:
                st.markdown("\n".join(rationale))
            else:
                st.info("No strong signals - HOLD recommended")
            
            # Risk warning
            if vol_estimate > 0.35:
                st.warning(f"⚠️ High volatility ({vol_estimate*100:.0f}%) - Reduce position size")
            
            st.markdown("---")

def create_portfolio_summary(data, cluster_name):
    """
    Create summary of all positions for next session
    """
    st.markdown("### Portfolio Summary - Next Session")
    
    # Placeholder for aggregated positions
    st.info("Aggregate portfolio view will show total allocations across all tickers")
    
    # TODO: Implement when we have actual position calculations
    summary_data = {
        'Total Exposure': '65%',
        'Cash Reserve': '35%',
        'Number of Positions': '3',
        'Estimated Portfolio Vol': '22%'
    }
    
    cols = st.columns(4)
    for i, (label, value) in enumerate(summary_data.items()):
        with cols[i]:
            st.metric(label, value)
