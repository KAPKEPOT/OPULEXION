# dashboard/app.py
"""
Eiten Interactive Dashboard
Main application file
"""

import streamlit as st
import sys
import os
from pathlib import Path

# Add parent directory to path to import eiten modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import dashboard components
from dashboard.components.sidebar import render_sidebar
from dashboard.components.charts import render_weights_chart, render_performance_charts
from dashboard.components.metrics import render_metrics_cards
from dashboard.components.export import render_export_buttons
from dashboard.utils.data_handler import prepare_data, run_optimization
from dashboard.utils.session import init_session_state

# Page configuration
st.set_page_config(
    page_title="Eiten Portfolio Optimizer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load custom CSS
def load_css():
    css_file = Path(__file__).parent / "assets" / "style.css"
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        # Default styling
        st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem;
            color: #1E88E5;
            text-align: center;
            margin-bottom: 1rem;
            padding: 1rem;
            background: linear-gradient(90deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 10px;
        }
        .metric-card {
            background: white;
            padding: 1rem;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.3s;
        }
        .metric-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        .metric-value {
            font-size: 1.8rem;
            font-weight: bold;
            color: #1E88E5;
        }
        .metric-label {
            font-size: 0.9rem;
            color: #6c757d;
            text-transform: uppercase;
        }
        .positive {
            color: #43A047;
        }
        .negative {
            color: #E53935;
        }
        .stButton > button {
            background-color: #1E88E5;
            color: white;
            font-weight: bold;
            border: none;
            padding: 0.5rem 2rem;
            border-radius: 5px;
            transition: all 0.3s;
        }
        .stButton > button:hover {
            background-color: #1565C0;
            box-shadow: 0 2px 8px rgba(30,136,229,0.3);
        }
        .info-box {
            background-color: #e3f2fd;
            padding: 1rem;
            border-radius: 10px;
            border-left: 4px solid #1E88E5;
            margin: 1rem 0;
        }
        </style>
        """, unsafe_allow_html=True)

# Initialize session state
init_session_state()

# Load CSS
load_css()

# Header
st.markdown('<h1 class="main-header">📊 Eiten Portfolio Optimizer</h1>', unsafe_allow_html=True)

# Create two columns for the top section
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("### ⚙️ Quick Config")
    # Quick preset selector
    preset = st.selectbox(
        "Quick Presets",
        ["Custom", "Tech Stocks", "FAANG", "Dow Jones", "S&P 500"],
        key="preset_selector"
    )
    
    if preset != "Custom" and preset != st.session_state.get('last_preset', ''):
        st.session_state.last_preset = preset
        # Load preset stocks
        presets = {
            "Tech Stocks": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "AMD", "META"],
            "FAANG": ["META", "AAPL", "AMZN", "NFLX", "GOOGL"],
            "Dow Jones": ["AAPL", "MSFT", "JPM", "JNJ", "WMT", "V", "HD", "DIS"],
            "S&P 500": ["AAPL", "MSFT", "AMZN", "GOOGL", "TSLA", "BRK-B", "JPM", "JNJ"]
        }
        st.session_state.stocks = presets[preset]

with col2:
    st.markdown("### 📈 Market Overview")
    market_cols = st.columns(3)
    with market_cols[0]:
        st.metric("S&P 500", "+12.4%", "+2.1%")
    with market_cols[1]:
        st.metric("NASDAQ", "+18.2%", "+3.4%")
    with market_cols[2]:
        st.metric("DOW JONES", "+8.7%", "+1.2%")

# Main layout: Sidebar + Content
with st.sidebar:
    render_sidebar()

# Main content area
if st.session_state.get('optimization_run', False):
    # Show results in tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Portfolio Weights", 
        "📈 Performance Charts", 
        "📉 Risk Analysis",
        "📋 Detailed Report"
    ])
    
    with tab1:
        st.subheader("Portfolio Allocation by Strategy")
        render_weights_chart()
    
    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Backtest Results")
            if os.path.exists("output/backtest.png"):
                st.image("output/backtest.png", use_container_width=True)
        with col2:
            st.subheader("Future Test Results")
            if os.path.exists("output/future_tests.png"):
                st.image("output/future_tests.png", use_container_width=True)
        
        st.subheader("Monte Carlo Simulation")
        if os.path.exists("output/monte_carlo.png"):
            st.image("output/monte_carlo.png", use_container_width=True)
    
    with tab3:
        st.subheader("Risk Metrics")
        render_metrics_cards()
    
    with tab4:
        st.subheader("Performance Summary")
        
        # Display metrics table
        if st.session_state.get('metrics_df') is not None:
            st.dataframe(
                st.session_state.metrics_df,
                use_container_width=True,
                height=400
            )
        
        # Export section
        st.markdown("---")
        st.subheader("📥 Export Results")
        render_export_buttons()

else:
    # Welcome screen
    st.markdown("""
    <div class="info-box">
        <h3>👋 Welcome to Eiten Portfolio Optimizer!</h3>
        <p>Configure your portfolio in the sidebar and click <b>🚀 Run Optimization</b> to get started.</p>
        <p>Features:</p>
        <ul>
            <li>📊 Multiple portfolio strategies (Eigen, MVP, MSR, Genetic Algo)</li>
            <li>📈 Interactive charts and visualizations</li>
            <li>📉 Comprehensive risk metrics</li>
            <li>📥 Export results to CSV, Excel, or PDF</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Show sample preview
    col1, col2, col3 = st.columns(3)
    with col1:
        st.image("https://via.placeholder.com/300x200?text=Portfolio+Weights", use_column_width=True)
    with col2:
        st.image("https://via.placeholder.com/300x200?text=Backtest+Results", use_column_width=True)
    with col3:
        st.image("https://via.placeholder.com/300x200?text=Risk+Metrics", use_column_width=True)

# Footer
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #6c757d;'>"
    "Made with ❤️ using Streamlit | "
    "<a href='https://github.com/KAPKEPOT/eiten'>GitHub</a>"
    "</p>",
    unsafe_allow_html=True
)