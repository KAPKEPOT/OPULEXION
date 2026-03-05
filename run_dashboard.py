#!/usr/bin/env python3
"""
Entry point for running the Eiten dashboard
"""

import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    # Check if streamlit is installed
    try:
        import streamlit
    except ImportError:
        print("Streamlit not found. Installing required packages...")
        os.system("pip install streamlit")
    
    # Run the dashboard
    dashboard_path = Path(__file__).parent / "dashboard" / "app.py"
    os.system(f"streamlit run {dashboard_path}")