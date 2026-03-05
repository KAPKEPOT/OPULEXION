
## Eiten Interactive Dashboard

A user-friendly web interface for the Eiten portfolio optimizer.

### Features

- 🎯 **Intuitive UI** - No command line needed
- 
- 📊 **Interactive Charts** - Toggle strategies, zoom, hover details
- 
- 📈 **Real-time Updates** - See results instantly
- 
- 📉 **Comprehensive Metrics** - Sharpe, Sortino, Max DD, and more
- 
- 📥 **Export Options** - CSV, Excel, PDF reports
- 
- 🔄 **Multiple Data Sources** - Yahoo Finance, Alpha Vantage, IEX Cloud
- 
- ⚙️ **Customizable** - All parameters adjustable via UI

## Installation


#### Install dashboard dependencies
```
pip install -r requirements-dash.txt
```
#### Or install all dependencies
```
pip install -r requirements.txt
```

###Usage


#### Run the dashboard
```
python run_dashboard.py
```
#### Or directly with streamlit

```
streamlit run dashboard/app.py
```

Then open your browser to
```
http://localhost:8501
```
### **Dashboard Sections**

1. **Configuration Sidebar**

· Select data source
· Choose stocks (presets, manual, file upload)
· Set strategy parameters
· Configure risk management

2. **Main Display**

· Portfolio weights visualization
· Performance charts (backtest, future test)
· Risk metrics cards
· Detailed comparison tables

3. **Export Options**

· Download as CSV
· Export to Excel (multiple sheets)
· Generate PDF reports
· Email reports
· API access

Screenshots

[Add screenshots here]

###### Tips

· Start with preset lists to explore

· Use "Quick Presets" for common configurations

· Hover over charts for detailed values

· Toggle strategies on/off to compare

· Export results for further analysis

