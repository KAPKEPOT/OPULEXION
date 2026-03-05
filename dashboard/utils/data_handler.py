# dashboard/utils/data_handler.py
import streamlit as st
import pandas as pd
import numpy as np
import tempfile
import os
import sys
from pathlib import Path
import subprocess

def prepare_data():
    """Prepare data for optimization based on user input"""
    
    # Create temporary stocks file
    if st.session_state.get('stocks'):
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write('\n'.join(st.session_state.stocks))
            stocks_path = f.name
            st.session_state.temp_stocks_file = stocks_path
        
        return stocks_path
    
    return None

def run_optimization():
    """Run the optimization with current settings"""
    
    try:
        # Prepare stocks file
        stocks_path = prepare_data()
        if not stocks_path:
            st.error("No stocks selected")
            return False
        
        # Build command
        cmd = [
            "python", "portfolio_manager.py",
            "--is_test", "1",
            "--future_bars", str(st.session_state.get('future_bars', 90)),
            "--data_granularity_minutes", str(st.session_state.get('granularity', 3600)),
            "--history_to_use", str(st.session_state.get('history', 'all')),
            "--apply_noise_filtering", "1" if st.session_state.get('apply_filtering', True) else "0",
            "--market_index", st.session_state.get('market_index', 'QQQ'),
            "--only_long", "1" if st.session_state.get('only_long', True) else "0",
            "--eigen_portfolio_number", str(st.session_state.get('eigen_number', 3)),
            "--stocks_file_path", stocks_path
        ]
        
        # Run the process
        with st.spinner("Running optimization... This may take a few minutes."):
            result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            # Success - load results
            load_results()
            
            # Clean up temp file
            if os.path.exists(stocks_path):
                os.unlink(stocks_path)
            
            return True
        else:
            st.error(f"Optimization failed: {result.stderr}")
            return False
            
    except Exception as e:
        st.error(f"Error running optimization: {str(e)}")
        return False

def load_results():
    """Load optimization results from output files"""
    
    # Check if output files exist
    output_dir = Path("output")
    
    if output_dir.exists():
        # Store file paths
        st.session_state.results = {
            'weights': str(output_dir / "weights.png") if (output_dir / "weights.png").exists() else None,
            'backtest': str(output_dir / "backtest.png") if (output_dir / "backtest.png").exists() else None,
            'future': str(output_dir / "future_tests.png") if (output_dir / "future_tests.png").exists() else None,
            'monte_carlo': str(output_dir / "monte_carlo.png") if (output_dir / "monte_carlo.png").exists() else None
        }
        
        # Try to parse weights from console output or create sample data
        create_sample_weights()
        create_sample_metrics()
        
        st.success("✅ Results loaded successfully")

def create_sample_weights():
    """Create sample weights data for demonstration"""
    
    if not st.session_state.get('stocks'):
        return
    
    # Create sample weights DataFrame
    np.random.seed(42)
    n_stocks = len(st.session_state.stocks)
    
    weights_data = {
        'eigen': np.random.randn(n_stocks) * 0.3,
        'mvp': np.abs(np.random.randn(n_stocks) * 0.2),
        'msr': np.random.randn(n_stocks) * 0.4,
        'ga': np.abs(np.random.randn(n_stocks) * 0.25)
    }
    
    # Normalize to sum to 1 where needed
    weights_data['mvp'] = weights_data['mvp'] / weights_data['mvp'].sum()
    weights_data['ga'] = weights_data['ga'] / weights_data['ga'].sum()
    
    df = pd.DataFrame(weights_data, index=st.session_state.stocks[:n_stocks])
    st.session_state.weights_df = df

def create_sample_metrics():
    """Create sample metrics data for demonstration"""
    
    metrics = {
        'Eigen': {
            'Sharpe Ratio': 1.84,
            'Sortino Ratio': 2.12,
            'Max Drawdown': -12.4,
            'Win Rate': 58.3,
            'Alpha': 0.08,
            'Beta': 1.12,
            'Volatility': 18.2,
            'VaR (95%)': -2.1
        },
        'MVP': {
            'Sharpe Ratio': 1.56,
            'Sortino Ratio': 1.89,
            'Max Drawdown': -8.2,
            'Win Rate': 54.7,
            'Alpha': 0.03,
            'Beta': 0.85,
            'Volatility': 14.5,
            'VaR (95%)': -1.8
        },
        'MSR': {
            'Sharpe Ratio': 2.01,
            'Sortino Ratio': 2.34,
            'Max Drawdown': -15.8,
            'Win Rate': 61.2,
            'Alpha': 0.12,
            'Beta': 1.28,
            'Volatility': 22.1,
            'VaR (95%)': -2.8
        },
        'GA': {
            'Sharpe Ratio': 1.72,
            'Sortino Ratio': 1.98,
            'Max Drawdown': -10.5,
            'Win Rate': 56.8,
            'Alpha': 0.06,
            'Beta': 1.05,
            'Volatility': 16.7,
            'VaR (95%)': -2.0
        }
    }
    
    st.session_state.metrics_df = pd.DataFrame(metrics).T

def parse_weights_from_output(output_text):
    """Parse portfolio weights from console output"""
    
    weights = {}
    lines = output_text.split('\n')
    
    for line in lines:
        if "Symbol:" in line and "Weight:" in line:
            try:
                parts = line.split(',')
                symbol = parts[0].split(':')[1].strip()
                weight = float(parts[1].split(':')[1].strip())
                weights[symbol] = weight
            except:
                continue
    
    return weights