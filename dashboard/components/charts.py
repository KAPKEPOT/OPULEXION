# dashboard/components/charts.py
"""
Chart rendering components for the dashboard
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from pathlib import Path

def render_weights_chart():
    """Render interactive portfolio weights chart"""
    
    # Check if we have weights data
    if st.session_state.get('weights') is not None:
        weights_data = st.session_state.weights
    else:
        # Try to load from saved output
        weights_file = Path("output/weights.png")
        if weights_file.exists():
            st.image(str(weights_file), use_column_width=True)
            
            # Add interactive toggles
            st.markdown("### Toggle Strategies")
            cols = st.columns(4)
            with cols[0]:
                st.session_state.show_eigen = st.checkbox("Eigen", True)
            with cols[1]:
                st.session_state.show_mvp = st.checkbox("MVP", True)
            with cols[2]:
                st.session_state.show_msr = st.checkbox("MSR", True)
            with cols[3]:
                st.session_state.show_ga = st.checkbox("GA", True)
        else:
            st.info("No weights data available. Run optimization first.")
            return
    
    # Create interactive matplotlib chart
    if st.session_state.get('weights_df') is not None:
        create_interactive_weights_chart()

def create_interactive_weights_chart():
    """Create an interactive weights chart with matplotlib"""
    
    df = st.session_state.weights_df
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    x = np.arange(len(df.index))
    width = 0.2
    multiplier = 0
    
    strategies = []
    if st.session_state.get('show_eigen', True):
        strategies.append(('Eigen', df['eigen'].values))
    if st.session_state.get('show_mvp', True):
        strategies.append(('MVP', df['mvp'].values))
    if st.session_state.get('show_msr', True):
        strategies.append(('MSR', df['msr'].values))
    if st.session_state.get('show_ga', True):
        strategies.append(('GA', df['ga'].values))
    
    colors = ['#1E88E5', '#43A047', '#FB8C00', '#E53935']
    
    for i, (label, values) in enumerate(strategies):
        offset = width * multiplier
        bars = ax.bar(x + offset, values, width, label=label, color=colors[i % len(colors)])
        multiplier += 1
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            if abs(height) > 0.01:  # Only show significant weights
                ax.annotate(f'{height:.2f}',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3 if height > 0 else -15),
                           textcoords="offset points",
                           ha='center', va='bottom', fontsize=8)
    
    ax.set_xlabel('Stocks', fontsize=12)
    ax.set_ylabel('Weight', fontsize=12)
    ax.set_title('Portfolio Weights by Strategy', fontsize=14, fontweight='bold')
    ax.set_xticks(x + width * (len(strategies) - 1) / 2)
    ax.set_xticklabels(df.index, rotation=45, ha='right')
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5, alpha=0.3)
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

def render_performance_charts():
    """Render performance comparison charts"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Cumulative Returns")
        create_returns_chart()
    
    with col2:
        st.subheader("📉 Drawdown Analysis")
        create_drawdown_chart()
    
    # Rolling metrics
    st.subheader("📊 Rolling Metrics")
    tab1, tab2, tab3 = st.tabs(["Rolling Sharpe", "Rolling Volatility", "Rolling Beta"])
    
    with tab1:
        create_rolling_sharpe_chart()
    with tab2:
        create_rolling_volatility_chart()
    with tab3:
        create_rolling_beta_chart()

def create_returns_chart():
    """Create cumulative returns comparison chart"""
    
    # Check if we have returns data
    returns_file = Path("output/backtest.png")
    if returns_file.exists():
        st.image(str(returns_file), use_column_width=True)
    else:
        # Create sample data for demonstration
        np.random.seed(42)
        days = 252
        dates = pd.date_range(start='2023-01-01', periods=days, freq='D')
        
        fig, ax = plt.subplots(figsize=(10, 5))
        
        strategies = {
            'Eigen': np.random.randn(days).cumsum() * 0.02,
            'MVP': np.random.randn(days).cumsum() * 0.015,
            'MSR': np.random.randn(days).cumsum() * 0.025,
            'GA': np.random.randn(days).cumsum() * 0.02,
            'Market': np.random.randn(days).cumsum() * 0.018
        }
        
        colors = ['#1E88E5', '#43A047', '#FB8C00', '#E53935', '#000000']
        
        for (label, returns), color in zip(strategies.items(), colors):
            ax.plot(dates, returns, label=label, color=color, linewidth=1.5)
        
        ax.set_xlabel('Date')
        ax.set_ylabel('Cumulative Return (%)')
        ax.set_title('Strategy Performance Comparison')
        ax.legend(loc='upper left')
        ax.grid(True, alpha=0.3, linestyle='--')
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5, alpha=0.3)
        
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

def create_drawdown_chart():
    """Create drawdown analysis chart"""
    
    fig, ax = plt.subplots(figsize=(10, 5))
    
    # Sample drawdown data
    np.random.seed(42)
    days = 252
    returns = np.random.randn(days) * 0.02
    cumulative = (1 + returns).cumprod()
    running_max = np.maximum.accumulate(cumulative)
    drawdown = (cumulative - running_max) / running_max * 100
    
    ax.fill_between(range(days), drawdown, 0, color='#E53935', alpha=0.3)
    ax.plot(range(days), drawdown, color='#E53935', linewidth=1)
    
    ax.set_xlabel('Trading Days')
    ax.set_ylabel('Drawdown (%)')
    ax.set_title('Portfolio Drawdown')
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Highlight max drawdown
    max_dd_idx = np.argmin(drawdown)
    max_dd = drawdown[max_dd_idx]
    ax.scatter(max_dd_idx, max_dd, color='red', s=50, zorder=5)
    ax.annotate(f'Max DD: {max_dd:.1f}%',
                xy=(max_dd_idx, max_dd),
                xytext=(max_dd_idx + 20, max_dd - 5),
                arrowprops=dict(arrowstyle='->', color='red'))
    
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

def create_rolling_sharpe_chart():
    """Create rolling Sharpe ratio chart"""
    
    fig, ax = plt.subplots(figsize=(10, 4))
    
    # Sample rolling Sharpe data
    np.random.seed(42)
    days = 252
    window = 60
    
    strategies = {
        'Eigen': pd.Series(np.random.randn(days) * 0.02).rolling(window).mean() / 
                 pd.Series(np.random.randn(days) * 0.02).rolling(window).std() * np.sqrt(252),
        'MVP': pd.Series(np.random.randn(days) * 0.015).rolling(window).mean() / 
               pd.Series(np.random.randn(days) * 0.015).rolling(window).std() * np.sqrt(252),
        'MSR': pd.Series(np.random.randn(days) * 0.025).rolling(window).mean() / 
               pd.Series(np.random.randn(days) * 0.025).rolling(window).std() * np.sqrt(252),
    }
    
    colors = ['#1E88E5', '#43A047', '#FB8C00']
    
    for (label, sharpe), color in zip(strategies.items(), colors):
        ax.plot(sharpe.index, sharpe.values, label=label, color=color, linewidth=1.5)
    
    ax.axhline(y=1, color='green', linestyle='--', alpha=0.5, label='Good')
    ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
    ax.axhline(y=-1, color='red', linestyle='--', alpha=0.5, label='Poor')
    
    ax.set_xlabel('Trading Days')
    ax.set_ylabel('Sharpe Ratio')
    ax.set_title(f'Rolling {window}-Day Sharpe Ratio')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

def create_rolling_volatility_chart():
    """Create rolling volatility chart"""
    
    fig, ax = plt.subplots(figsize=(10, 4))
    
    # Sample rolling volatility data
    np.random.seed(42)
    days = 252
    window = 60
    
    strategies = {
        'Eigen': pd.Series(np.random.randn(days) * 0.02).rolling(window).std() * np.sqrt(252) * 100,
        'MVP': pd.Series(np.random.randn(days) * 0.015).rolling(window).std() * np.sqrt(252) * 100,
        'MSR': pd.Series(np.random.randn(days) * 0.025).rolling(window).std() * np.sqrt(252) * 100,
    }
    
    colors = ['#1E88E5', '#43A047', '#FB8C00']
    
    for (label, vol), color in zip(strategies.items(), colors):
        ax.plot(vol.index, vol.values, label=label, color=color, linewidth=1.5)
    
    ax.set_xlabel('Trading Days')
    ax.set_ylabel('Volatility (%)')
    ax.set_title(f'Rolling {window}-Day Annualized Volatility')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

def create_rolling_beta_chart():
    """Create rolling beta chart"""
    
    fig, ax = plt.subplots(figsize=(10, 4))
    
    # Sample rolling beta data
    np.random.seed(42)
    days = 252
    window = 60
    
    strategies = {
        'Eigen': pd.Series(np.random.randn(days) * 0.3 + 1),
        'MVP': pd.Series(np.random.randn(days) * 0.2 + 0.8),
        'MSR': pd.Series(np.random.randn(days) * 0.4 + 1.2),
    }
    
    colors = ['#1E88E5', '#43A047', '#FB8C00']
    
    for (label, beta), color in zip(strategies.items(), colors):
        ax.plot(beta.index, beta.values, label=label, color=color, linewidth=1.5)
    
    ax.axhline(y=1, color='black', linestyle='-', alpha=0.5, label='Market Beta')
    
    ax.set_xlabel('Trading Days')
    ax.set_ylabel('Beta')
    ax.set_title(f'Rolling {window}-Day Market Beta')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

def create_correlation_heatmap():
    """Create correlation heatmap of stocks"""
    
    if st.session_state.get('returns_matrix') is not None:
        returns = st.session_state.returns_matrix
        
        fig, ax = plt.subplots(figsize=(10, 8))
        
        corr_matrix = np.corrcoef(returns)
        
        sns.heatmap(corr_matrix, 
                   annot=True, 
                   fmt='.2f', 
                   cmap='RdBu_r',
                   center=0,
                   square=True,
                   ax=ax,
                   cbar_kws={'label': 'Correlation'})
        
        if st.session_state.get('symbols'):
            ax.set_xticklabels(st.session_state.symbols, rotation=45, ha='right')
            ax.set_yticklabels(st.session_state.symbols, rotation=0)
        
        ax.set_title('Stock Correlation Matrix', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        st.pyplot(fig)
        plt.close()