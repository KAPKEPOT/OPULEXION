# dashboard/components/sidebar.py
import streamlit as st
import tempfile
import os

def render_sidebar():
    """Render the sidebar with all configuration options"""
    
    st.markdown("## ⚙️ Configuration")
    st.markdown("---")
    
    # Data Source Section
    st.markdown("### 📁 Data Source")
    
    data_source = st.selectbox(
        "Select Source",
        ["Yahoo Finance", "Alpha Vantage", "IEX Cloud", "CSV Upload"],
        key="data_source"
    )
    
    # API Key input if needed
    if data_source in ["Alpha Vantage", "IEX Cloud"]:
        api_key = st.text_input(
            f"{data_source} API Key",
            type="password",
            key="api_key",
            help=f"Enter your {data_source} API key"
        )
        if api_key:
            st.session_state.api_key = api_key
    
    # CSV Upload
    if data_source == "CSV Upload":
        uploaded_file = st.file_uploader(
            "Upload CSV file",
            type=['csv'],
            key="csv_upload",
            help="Upload a CSV file with historical data"
        )
        if uploaded_file:
            st.success("✅ File uploaded successfully")
            st.session_state.uploaded_file = uploaded_file
    
    st.markdown("---")
    
    # Stock Selection Section
    st.markdown("### 📈 Stock Selection")
    
    selection_method = st.radio(
        "Selection Method",
        ["Preset Lists", "Manual Entry", "File Upload"],
        key="selection_method",
        horizontal=True
    )
    
    stocks = []
    
    if selection_method == "Preset Lists":
        preset = st.selectbox(
            "Choose Preset",
            ["Tech Stocks", "FAANG", "Dow Jones", "S&P 500", "Custom"],
            key="preset"
        )
        
        presets = {
            "Tech Stocks": ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "AMD", "META"],
            "FAANG": ["META", "AAPL", "AMZN", "NFLX", "GOOGL"],
            "Dow Jones": ["AAPL", "MSFT", "JPM", "JNJ", "WMT", "V", "HD", "DIS"],
            "S&P 500": ["AAPL", "MSFT", "AMZN", "GOOGL", "TSLA", "BRK-B", "JPM", "JNJ"]
        }
        
        if preset in presets:
            stocks = presets[preset]
            st.info(f"Selected {len(stocks)} stocks")
            
            # Allow editing
            edit = st.checkbox("Edit list")
            if edit:
                stocks_text = st.text_area(
                    "Edit stocks (one per line)",
                    "\n".join(stocks),
                    height=150
                )
                stocks = [s.strip() for s in stocks_text.split('\n') if s.strip()]
    
    elif selection_method == "Manual Entry":
        stocks_text = st.text_area(
            "Enter stock symbols (one per line)",
            "AAPL\nMSFT\nGOOGL\nAMZN\nTSLA",
            height=150,
            help="Enter stock symbols, one per line"
        )
        stocks = [s.strip().upper() for s in stocks_text.split('\n') if s.strip()]
    
    else:  # File Upload
        stocks_file = st.file_uploader(
            "Upload stocks.txt",
            type=['txt'],
            help="Upload a text file with one stock symbol per line"
        )
        
        if stocks_file:
            content = stocks_file.getvalue().decode('utf-8')
            stocks = [s.strip().upper() for s in content.split('\n') if s.strip()]
            st.success(f"✅ Loaded {len(stocks)} stocks")
    
    # Store stocks in session state
    if stocks:
        st.session_state.stocks = stocks
        
        # Show preview
        with st.expander("Preview Selected Stocks"):
            st.write(", ".join(stocks[:10]))
            if len(stocks) > 10:
                st.write(f"... and {len(stocks) - 10} more")
    
    st.markdown("---")
    
    # Strategy Parameters
    st.markdown("### 🎛️ Strategy Parameters")
    
    col1, col2 = st.columns(2)
    
    with col1:
        granularity = st.selectbox(
            "Data Granularity",
            [15, 30, 60, 3600],
            index=3,
            format_func=lambda x: f"{x} minutes" if x < 3600 else "Daily",
            help="Minutes per bar. 3600 = daily data"
        )
        st.session_state.granularity = granularity
        
        future_bars = st.slider(
            "Test Size (bars)",
            min_value=10,
            max_value=200,
            value=90,
            help="Number of bars to reserve for testing"
        )
        st.session_state.future_bars = future_bars
    
    with col2:
        eigen_number = st.number_input(
            "Eigen Portfolio #",
            min_value=1,
            max_value=10,
            value=3,
            help="Which eigen portfolio to use"
        )
        st.session_state.eigen_number = eigen_number
        
        market_index = st.selectbox(
            "Market Index",
            ["SPY", "QQQ", "DIA", "IWM"],
            index=1,
            help="Benchmark index for comparison"
        )
        st.session_state.market_index = market_index
    
    # Risk Parameters
    st.markdown("### ⚠️ Risk Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        apply_filtering = st.checkbox(
            "Apply RMT Filtering",
            value=True,
            help="Use Random Matrix Theory to filter noise"
        )
        st.session_state.apply_filtering = apply_filtering
    
    with col2:
        only_long = st.checkbox(
            "Long Only",
            value=True,
            help="Restrict to long positions only"
        )
        st.session_state.only_long = only_long
    
    # History to use
    history_option = st.radio(
        "History to use",
        ["All available", "Last 500 bars", "Last 1000 bars", "Custom"],
        index=0,
        horizontal=True
    )
    
    if history_option == "Custom":
        custom_history = st.number_input(
            "Number of bars",
            min_value=50,
            max_value=5000,
            value=1000
        )
        st.session_state.history = str(custom_history)
    elif history_option == "Last 500 bars":
        st.session_state.history = "500"
    elif history_option == "Last 1000 bars":
        st.session_state.history = "1000"
    else:
        st.session_state.history = "all"
    
    st.markdown("---")
    
    # Strategy Selection
    st.markdown("### 🔄 Strategies to Run")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.session_state.run_eigen = st.checkbox("Eigen Portfolio", True)
        st.session_state.run_mvp = st.checkbox("Minimum Variance", True)
    
    with col2:
        st.session_state.run_msr = st.checkbox("Maximum Sharpe", True)
        st.session_state.run_ga = st.checkbox("Genetic Algorithm", True)
    
    st.markdown("---")
    
    # Run Button
    run_button = st.button(
        "🚀 RUN OPTIMIZATION",
        type="primary",
        use_container_width=True,
        help="Click to run portfolio optimization with current settings"
    )
    
    if run_button:
        if not st.session_state.get('stocks'):
            st.error("❌ Please select at least one stock")
        else:
            st.session_state.optimization_run = True
            st.session_state.run_clicked = True
            st.rerun()
    
    # Show configuration summary
    if st.session_state.get('stocks'):
        with st.expander("📋 Configuration Summary"):
            st.write(f"**Stocks:** {len(st.session_state.stocks)}")
            st.write(f"**Data Source:** {st.session_state.get('data_source', 'Yahoo Finance')}")
            st.write(f"**Granularity:** {st.session_state.get('granularity', 3600)} min")
            st.write(f"**Test Size:** {st.session_state.get('future_bars', 90)} bars")
            # st.write(f"**Strategies:** ", end="")
            strategies = []
            if st.session_state.get('run_eigen'): strategies.append("Eigen")
            if st.session_state.get('run_mvp'): strategies.append("MVP")
            if st.session_state.get('run_msr'): strategies.append("MSR")
            if st.session_state.get('run_ga'): strategies.append("GA")
            st.write(f"**Strategies:** {', '.join(strategies)}")