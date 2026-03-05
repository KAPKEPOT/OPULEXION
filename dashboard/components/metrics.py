# dashboard/components/metrics.py
"""
Performance metrics cards component
"""

import streamlit as st
import pandas as pd
import numpy as np

def render_metrics_cards():
    """Render performance metrics in card layout"""
    
    # Sample metrics data (replace with actual data)
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
    
    # Strategy selector
    selected_strategy = st.selectbox(
        "Select Strategy",
        list(metrics.keys()),
        key='metric_strategy'
    )
    
    # Create metrics grid
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        create_metric_card(
            "Sharpe Ratio",
            metrics[selected_strategy]['Sharpe Ratio'],
            "Risk-adjusted return",
            "🎯"
        )
        create_metric_card(
            "Max Drawdown",
            f"{metrics[selected_strategy]['Max Drawdown']:.1f}%",
            "Peak to trough decline",
            "📉",
            negative_ok=True
        )
    
    with col2:
        create_metric_card(
            "Sortino Ratio",
            metrics[selected_strategy]['Sortino Ratio'],
            "Downside risk-adjusted",
            "🛡️"
        )
        create_metric_card(
            "Win Rate",
            f"{metrics[selected_strategy]['Win Rate']:.1f}%",
            "Profitable periods",
            "🎲"
        )
    
    with col3:
        create_metric_card(
            "Alpha",
            metrics[selected_strategy]['Alpha'],
            "Excess return",
            "⚡"
        )
        create_metric_card(
            "Beta",
            metrics[selected_strategy]['Beta'],
            "Market sensitivity",
            "📊"
        )
    
    with col4:
        create_metric_card(
            "Volatility",
            f"{metrics[selected_strategy]['Volatility']:.1f}%",
            "Annualized risk",
            "🌊"
        )
        create_metric_card(
            "VaR (95%)",
            f"{metrics[selected_strategy]['VaR (95%)']:.1f}%",
            "Value at Risk",
            "⚠️",
            negative_ok=True
        )
    
    # Add comparison table
    st.markdown("---")
    st.subheader("📊 Strategy Comparison")
    
    comparison_df = pd.DataFrame(metrics).T
    st.dataframe(
        comparison_df.style.format({
            'Sharpe Ratio': '{:.2f}',
            'Sortino Ratio': '{:.2f}',
            'Max Drawdown': '{:.1f}%',
            'Win Rate': '{:.1f}%',
            'Alpha': '{:.3f}',
            'Beta': '{:.2f}',
            'Volatility': '{:.1f}%',
            'VaR (95%)': '{:.1f}%'
        }).background_gradient(cmap='RdYlGn', subset=['Sharpe Ratio', 'Sortino Ratio', 'Win Rate']),
        use_container_width=True,
        height=300
    )

def create_metric_card(title, value, description, icon, negative_ok=False):
    """Create a single metric card"""
    
    # Determine color based on value
    if isinstance(value, (int, float)):
        if value > 0 and not negative_ok:
            color = "#43A047"  # Green
        elif value < 0 and not negative_ok:
            color = "#E53935"  # Red
        else:
            color = "#1E88E5"  # Blue
    else:
        color = "#1E88E5"
    
    # Format value if it's a float
    if isinstance(value, float):
        if abs(value) < 10:
            display_value = f"{value:.2f}"
        else:
            display_value = f"{value:.1f}"
    else:
        display_value = str(value)
    
    html = f"""
    <div class="metric-card">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">{icon}</div>
        <div class="metric-value" style="color: {color};">{display_value}</div>
        <div class="metric-label">{title}</div>
        <div style="font-size: 0.8rem; color: #6c757d; margin-top: 0.5rem;">{description}</div>
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)

def calculate_metrics_from_returns(returns):
    """Calculate performance metrics from returns data"""
    
    metrics = {}
    
    # Basic metrics
    metrics['Total Return'] = (np.prod(1 + returns) - 1) * 100
    metrics['Annual Return'] = ((1 + metrics['Total Return']/100) ** (252/len(returns)) - 1) * 100
    
    # Risk metrics
    metrics['Volatility'] = np.std(returns) * np.sqrt(252) * 100
    metrics['Downside Deviation'] = np.std([r for r in returns if r < 0]) * np.sqrt(252) * 100
    
    # Risk-adjusted returns
    metrics['Sharpe Ratio'] = (np.mean(returns) * 252) / (np.std(returns) * np.sqrt(252))
    metrics['Sortino Ratio'] = (np.mean(returns) * 252) / metrics['Downside Deviation'] * 100 if metrics['Downside Deviation'] > 0 else 0
    
    # Drawdown
    cumulative = (1 + returns).cumprod()
    running_max = np.maximum.accumulate(cumulative)
    drawdown = (cumulative - running_max) / running_max
    metrics['Max Drawdown'] = np.min(drawdown) * 100
    
    # Win rate
    metrics['Win Rate'] = (len([r for r in returns if r > 0]) / len(returns)) * 100
    
    # VaR
    metrics['VaR (95%)'] = np.percentile(returns, 5) * 100
    
    return metrics