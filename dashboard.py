"""
Eiten Interactive Dashboard
Run with: streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import tempfile
import os
import sys
from pathlib import Path

# Add the project directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from eiten import Eiten
import argparse
from performance_metrics import PerformanceAnalyzer
from data_sources import DataSourceFactory

# Page config
st.set_page_config(
    page_title="Eiten Portfolio Optimizer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">📊 Eiten Portfolio Optimizer</h1>', unsafe_allow_html=True)
st.markdown("---")

# Initialize session state
if 'results' not in st.session_state:
    st.session_state.results = None
if 'metrics' not in st.session_state:
    st.session_state.metrics = None

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Data Source Selection
    st.subheader("📁 Data Source")
    data_source = st.selectbox(
        "Choose data source",
        ["Yahoo Finance", "Alpha Vantage", "IEX Cloud", "CSV Upload", "Sample Data"]
    )
    
    # API Key inputs based on selection
    api_key = None
    if data_source == "Alpha Vantage":
        api_key = st.text_input("Alpha Vantage API Key", type="password")
    elif data_source == "IEX Cloud":
        api_key = st.text_input("IEX Cloud API Key", type="password")
    elif data_source == "CSV Upload":
        uploaded_file = st.file_uploader("Upload CSV file", type=['csv'])
        if uploaded_file:
            st.success("File uploaded successfully!")
    
    # Stock Selection
    st.subheader("📈 Stocks")
    input_method = st.radio("Input method", ["Text input", "File upload", "Preset list"])
    
    stocks = []
    if input_method == "Text input":
        stocks_text = st.text_area(
            "Enter stock symbols (one per line)",
            "AAPL\nMSFT\nGOOGL\nAMZN\nTSLA"
        )
        stocks = [s.strip() for s in stocks_text.split('\n') if s.strip()]
    elif input_method == "File upload":
        stocks_file = st.file_uploader("Upload stocks.txt", type=['txt'])
        if stocks_file:
            content = stocks_file.getvalue().decode('utf-8')
            stocks = [s.strip() for s in content.split('\n') if s.strip()]
    else:
        preset = st.selectbox(
            "Choose preset",
            ["Tech Stocks", "FAANG", "Dow Jones", "S&P 500 Sample"]
        )
        presets = {
            "Tech Stocks": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "AMD", "INTC"],
            "FAANG": ["FB", "AAPL", "AMZN", "NFLX", "GOOGL"],
            "Dow Jones": ["AAPL", "MSFT", "JPM", "JNJ", "WMT", "V", "HD", "DIS"],
            "S&P 500 Sample": ["AAPL", "MSFT", "AMZN", "GOOGL", "TSLA", "BRK-B", "JPM", "JNJ"]
        }
        stocks = presets[preset]
    
    st.info(f"Selected {len(stocks)} stocks")
    
    # Parameters
    st.subheader("🎛️ Parameters")
    
    col1, col2 = st.columns(2)
    with col1:
        granularity = st.selectbox(
            "Data granularity",
            [15, 30, 60, 3600],
            index=3,
            help="Minutes per bar. 3600 = daily data"
        )
        future_bars = st.slider(
            "Future bars for testing",
            min_value=10,
            max_value=200,
            value=90,
            help="Number of bars to reserve for testing"
        )
    with col2:
        eigen_number = st.number_input(
            "Eigen portfolio number",
            min_value=1,
            max_value=5,
            value=3,
            help="Which eigen portfolio to use"
        )
        history = st.text_input(
            "History to use",
            value="all",
            help="Number of bars or 'all'"
        )
    
    # Strategy options
    st.subheader("🔄 Strategies")
    strategies = {
        "Eigen Portfolio": st.checkbox("Eigen Portfolio", True),
        "Minimum Variance": st.checkbox("Minimum Variance", True),
        "Maximum Sharpe": st.checkbox("Maximum Sharpe", True),
        "Genetic Algorithm": st.checkbox("Genetic Algorithm", True)
    }
    
    # Risk options
    st.subheader("⚠️ Risk Management")
    apply_noise_filtering = st.checkbox("Apply noise filtering (RMT)", True)
    only_long = st.checkbox("Long only positions", True)
    
    # Run button
    run_button = st.button("🚀 Run Portfolio Optimization", type="primary", use_container_width=True)

# Main content
if run_button and stocks:
    with st.spinner("🔄 Running portfolio optimization... This may take a few minutes."):
        try:
            # Create temp file for stocks
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                f.write('\n'.join(stocks))
                stocks_path = f.name
            
            # Create args object
            args = argparse.Namespace(
                history_to_use=history,
                data_granularity_minutes=granularity,
                is_test=1,
                future_bars=future_bars,
                apply_noise_filtering=apply_noise_filtering,
                only_long=only_long,
                market_index="QQQ",
                eigen_portfolio_number=eigen_number,
                stocks_file_path=stocks_path
            )
            
            # Run Eiten
            eiten = Eiten(args)
            eiten.run_strategies()
            
            # Store results in session state
            st.session_state.results = {
                'weights': 'output/weights.png',
                'backtest': 'output/backtest.png',
                'future': 'output/future_tests.png',
                'monte_carlo': 'output/monte_carlo.png'
            }
            
            # Calculate performance metrics
            analyzer = PerformanceAnalyzer()
            st.session_state.metrics = analyzer.calculate_all_metrics(
                eiten.data_dictionary,
                eiten.symbol_names
            )
            
            st.success("✅ Optimization complete!")
            
        except Exception as e:
            st.error(f"❌ Error: {str(e)}")

# Display results
if st.session_state.results:
    # Performance Metrics Section
    if st.session_state.metrics:
        st.header("📊 Performance Metrics")
        
        metrics_df = st.session_state.metrics
        st.dataframe(metrics_df.style.format({
            'Sharpe Ratio': '{:.3f}',
            'Sortino Ratio': '{:.3f}',
            'Max Drawdown': '{:.2%}',
            'Annual Return': '{:.2%}',
            'Volatility': '{:.2%}',
            'Win Rate': '{:.2%}'
        }), use_container_width=True)
    
    # Charts Section
    st.header("📈 Portfolio Analysis")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "Portfolio Weights", "Backtest Results", 
        "Future Test Results", "Monte Carlo Simulation"
    ])
    
    with tab1:
        if os.path.exists(st.session_state.results['weights']):
            st.image(st.session_state.results['weights'], use_column_width=True)
    
    with tab2:
        if os.path.exists(st.session_state.results['backtest']):
            st.image(st.session_state.results['backtest'], use_column_width=True)
    
    with tab3:
        if os.path.exists(st.session_state.results['future']):
            st.image(st.session_state.results['future'], use_column_width=True)
    
    with tab4:
        if os.path.exists(st.session_state.results['monte_carlo']):
            st.image(st.session_state.results['monte_carlo'], use_column_width=True)
    
    # Export options
    st.header("📥 Export Results")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📊 Export as CSV"):
            # Create CSV export
            csv = st.session_state.metrics.to_csv()
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="portfolio_metrics.csv",
                mime="text/csv"
            )
    with col2:
        if st.button("📑 Export as Excel"):
            # Create Excel export
            with pd.ExcelWriter('portfolio_report.xlsx') as writer:
                st.session_state.metrics.to_excel(writer, sheet_name='Metrics')
            with open('portfolio_report.xlsx', 'rb') as f:
                st.download_button(
                    label="Download Excel",
                    data=f,
                    file_name="portfolio_report.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    with col3:
        if st.button("📄 Export as PDF"):
            st.info("PDF export coming soon!")

# Footer
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: gray;'>"
    "Eiten Portfolio Optimizer | Made with ❤️ using Streamlit"
    "</p>",
    unsafe_allow_html=True
)