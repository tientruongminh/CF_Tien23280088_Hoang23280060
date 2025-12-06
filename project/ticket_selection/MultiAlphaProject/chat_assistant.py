"""
Gemini AI Chat Assistant for Multi-Alpha Dashboard
==================================================
Google Gemini integration with model selection.
"""

import streamlit as st
import pandas as pd
import google.generativeai as genai

def init_chat():
    """Initialize chat history"""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'gemini_api_key' not in st.session_state:
        st.session_state.gemini_api_key = None
    if 'gemini_model' not in st.session_state:
        st.session_state.gemini_model = 'gemini-1.5-pro'

def create_data_context(data):
    """Create context string from backtest data for Gemini"""
    context = "# Multi-Alpha Portfolio Backtest Data\n\n"
    
    # Summary statistics
    if data['summary'] is not None:
        context += "## Portfolio Summary:\n"
        for _, row in data['summary'].iterrows():
            context += f"- {row['File']}: Sharpe={row['Sharpe_Ratio']:.2f}, Return={row['Total_Return']*100:.1f}%, MaxDD={row['Max_Drawdown']*100:.1f}%\n"
        context += "\n"
    
    # Available clusters
    context += f"## Available Clusters: {', '.join(data['equity'].keys())}\n\n"
    
    # Recent performance
    for cluster, equity_df in list(data['equity'].items())[:3]:
        if len(equity_df) > 0:
            recent_return = (equity_df['Cumulative_Return'].iloc[-1] - 1) * 100
            context += f"- {cluster}: Recent total return = {recent_return:.2f}%\n"
    
    return context

def chat_tab(data):
    """Render Gemini chat interface"""
    st.markdown('<h2>AI Assistant (Google Gemini)</h2>', unsafe_allow_html=True)
    
    init_chat()
    
    # API Key and Model Configuration
    with st.expander("Configure Gemini API", expanded=not st.session_state.gemini_api_key):
        col1, col2 = st.columns(2)
        
        with col1:
            api_key = st.text_input(
                "Gemini API Key:",
                type="password",
                value=st.session_state.gemini_api_key or "",
                help="Get free key from https://makersuite.google.com/app/apikey"
            )
        
        with col2:
            model_choice = st.selectbox(
                "Model:",
                ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-1.0-pro"],
                help="""
                - gemini-1.5-pro: Most capable (RECOMMENDED)
                - gemini-1.5-flash: Fastest, good for simple queries
                - gemini-1.0-pro: Stable legacy model
                """
            )
        
        if api_key:
            st.session_state.gemini_api_key = api_key
            st.session_state.gemini_model = model_choice
            st.success(f"✅ Configured: {model_choice}")
            
            # Model info
            model_info = {
                'gemini-1.5-pro': {
                    'context': '2M tokens',
                    'speed': 'Fast',
                    'cost': 'Free tier: 50 RPD'
                },
                'gemini-1.5-flash': {
                    'context': '1M tokens',
                    'speed': 'Very Fast',
                    'cost': 'Free tier: 1500 RPD'
                },
                'gemini-1.0-pro': {
                    'context': '30K tokens',
                    'speed': 'Medium',
                    'cost': 'Free tier: 60 RPM'
                }
            }
            
            info = model_info.get(model_choice, {})
            st.info(f"**{model_choice}** - Context: {info.get('context', 'N/A')}, Speed: {info.get('speed', 'N/A')}")
    
    if not st.session_state.gemini_api_key:
        st.warning("⚠️ Please enter your Gemini API key to use the chat feature.")
        st.info("""
        **Example questions:**
        - Is my model good enough to deploy?
        - What does Sharpe 1.17 mean?
        - Why did VB need redesign?
        - Should I allocate 15% or 25%?
        - Explain the adaptive risk management system
        """)
        return
    
    # Configure Gemini
    try:
        genai.configure(api_key=st.session_state.gemini_api_key)
        model = genai.GenerativeModel(st.session_state.gemini_model)
    except Exception as e:
        st.error(f"Configuration error: {str(e)}")
        return
    
    # Data context for Gemini
    data_context = create_data_context(data)
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask about your portfolio strategy..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get Gemini response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # System prompt with data context
                    system_message = f"""{data_context}

You are an expert financial analyst specializing in quantitative trading strategies.
Answer questions about the Multi-Alpha portfolio backtest data shown above.

Key concepts:
- **Sharpe Ratio**: Risk-adjusted return (>1.0 good, >1.5 excellent)
- **Max Drawdown**: Worst peak-to-trough decline
- **Mean Reversion (MR)**: Betting on price convergence
- **Momentum (Mom)**: Trend-following
- **Volatility Breakout (VB)**: Vol regime changes (redesigned with Z-score)
- **Cross-Sectional Reversal (XSR)**: Short-term mean reversion
- **Value (Val)**: 52-week range positioning

The system uses:
- Ridge regression to combine alpha signals
- 4-layer adaptive risk management (correlation-based diversification, inverse-vol sizing, volatility targeting, ATR trailing stop)
- Professional dashboard with model evaluation (Grade B+)

Provide concise, accurate, professional answers.

User question: {prompt}
"""
                    
                    # Generate response
                    response = model.generate_content(system_message)
                    assistant_response = response.text
                    
                    st.markdown(assistant_response)
                    
                    # Add to history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": assistant_response
                    })
                    
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                    if "API_KEY_INVALID" in str(e):
                        st.error("❌ Invalid API key. Please check your Gemini API key.")
                    elif "RATE_LIMIT" in str(e):
                        st.error("⚠️ Rate limit exceeded. Please wait a moment.")
    
    # Clear chat button
    if len(st.session_state.messages) > 0:
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("Clear Chat History"):
                st.session_state.messages = []
                st.rerun()

if __name__ == "__main__":
    # Test standalone
    st.set_page_config(page_title="Gemini Chat Test", layout="wide")
    st.title("Gemini Chat Test")
    
    # Mock data
    mock_data = {
        'summary': pd.DataFrame({
            'File': ['cluster_test.csv'],
            'Sharpe_Ratio': [1.17],
            'Total_Return': [26.29],
            'Max_Drawdown': [-0.484]
        }),
        'equity': {
            'test': pd.DataFrame({
                'Date': pd.date_range('2020-01-01', periods=100),
                'Cumulative_Return': [1 + i*0.01 for i in range(100)]
            })
        }
    }
    
    chat_tab(mock_data)
