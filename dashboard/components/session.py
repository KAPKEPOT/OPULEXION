# dashboard/components/session.py
"""
Session state management utilities
"""

import streamlit as st

def init_session_state():
    """Initialize all session state variables"""
    
    # Configuration defaults
    defaults = {
        'stocks': [],
        'data_source': 'Yahoo Finance',
        'granularity': 3600,
        'future_bars': 90,
        'eigen_number': 3,
        'market_index': 'QQQ',
        'apply_filtering': True,
        'only_long': True,
        'history': 'all',
        'run_eigen': True,
        'run_mvp': True,
        'run_msr': True,
        'run_ga': True,
        
        # Results storage
        'optimization_run': False,
        'run_clicked': False,
        'results': None,
        'metrics_df': None,
        'weights': None,
        
        # File uploads
        'uploaded_file': None,
        'api_key': None,
        
        # UI state
        'last_preset': '',
        'current_tab': 0,
    }
    
    # Initialize only if not already set
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def clear_results():
    """Clear optimization results from session state"""
    st.session_state.optimization_run = False
    st.session_state.results = None
    st.session_state.metrics_df = None
    st.session_state.weights = None

def update_config(key, value):
    """Update a configuration value and clear results"""
    st.session_state[key] = value
    clear_results()