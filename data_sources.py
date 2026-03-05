"""
Multiple data source support for Eiten
"""

import pandas as pd
import numpy as np
import requests
import yfinance as yf
from abc import ABC, abstractmethod

class DataSource(ABC):
    """Abstract base class for data sources"""
    
    @abstractmethod
    def get_historical_data(self, symbol, period, interval):
        """Get historical price data"""
        pass
    
    @abstractmethod
    def get_company_info(self, symbol):
        """Get company information"""
        pass

class YahooFinanceSource(DataSource):
    """Yahoo Finance data source"""
    
    def get_historical_data(self, symbol, period="5y", interval="1d"):
        try:
            stock = yf.download(symbol, period=period, interval=interval, progress=False)
            if stock.empty:
                return None
            
            stock = stock.reset_index()
            if 'Date' in stock.columns:
                stock.rename(columns={'Date': 'Datetime'}, inplace=True)
            
            return stock
        except Exception as e:
            print(f"Yahoo Finance error for {symbol}: {e}")
            return None
    
    def get_company_info(self, symbol):
        try:
            ticker = yf.Ticker(symbol)
            return ticker.info
        except:
            return {}

class AlphaVantageSource(DataSource):
    """Alpha Vantage data source (requires API key)"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
    
    def get_historical_data(self, symbol, period="5y", interval="1d"):
        if not self.api_key:
            print("Alpha Vantage API key required")
            return None
        
        # Map intervals to Alpha Vantage format
        interval_map = {
            "1d": "Daily",
            "60m": "60min",
            "30m": "30min",
            "15m": "15min",
            "5m": "5min",
            "1m": "1min"
        }
        
        av_interval = interval_map.get(interval, "Daily")
        
        params = {
            'function': 'TIME_SERIES_DAILY_ADJUSTED' if av_interval == 'Daily' else f'TIME_SERIES_INTRADAY',
            'symbol': symbol,
            'apikey': self.api_key,
            'outputsize': 'full'
        }
        
        if av_interval != 'Daily':
            params['interval'] = av_interval
        
        try:
            response = requests.get(self.base_url, params=params)
            data = response.json()
            
            if 'Time Series (Daily)' in data:
                df = pd.DataFrame.from_dict(data['Time Series (Daily)'], orient='index')
                df.index = pd.to_datetime(df.index)
                df = df.sort_index()
                df = df.reset_index()
                df.rename(columns={'index': 'Datetime'}, inplace=True)
                return df
            else:
                print(f"No data for {symbol}")
                return None
                
        except Exception as e:
            print(f"Alpha Vantage error for {symbol}: {e}")
            return None
    
    def get_company_info(self, symbol):
        params = {
            'function': 'OVERVIEW',
            'symbol': symbol,
            'apikey': self.api_key
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            return response.json()
        except:
            return {}

class IEXCloudSource(DataSource):
    """IEX Cloud data source (requires API key)"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://cloud.iexapis.com/stable"
    
    def get_historical_data(self, symbol, period="5y", interval="1d"):
        if not self.api_key:
            print("IEX Cloud API key required")
            return None
        
        # Map period to IEX format
        range_map = {
            "5y": "5y",
            "2y": "2y",
            "1y": "1y",
            "6mo": "6m",
            "3mo": "3m",
            "1mo": "1m"
        }
        
        iex_range = range_map.get(period, "1y")
        
        url = f"{self.base_url}/stock/{symbol}/chart/{iex_range}"
        params = {
            'token': self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if isinstance(data, list):
                df = pd.DataFrame(data)
                if 'date' in df.columns:
                    df.rename(columns={'date': 'Datetime'}, inplace=True)
                    df['Datetime'] = pd.to_datetime(df['Datetime'])
                return df
            return None
        except Exception as e:
            print(f"IEX Cloud error for {symbol}: {e}")
            return None
    
    def get_company_info(self, symbol):
        url = f"{self.base_url}/stock/{symbol}/company"
        params = {'token': self.api_key}
        
        try:
            response = requests.get(url, params=params)
            return response.json()
        except:
            return {}

class CSVDataSource(DataSource):
    """CSV file data source"""
    
    def __init__(self, file_path):
        self.file_path = file_path
        self.data = self.load_csv()
    
    def load_csv(self):
        try:
            df = pd.read_csv(self.file_path)
            # Try to detect datetime column
            for col in df.columns:
                if 'date' in col.lower() or 'time' in col.lower():
                    df[col] = pd.to_datetime(df[col])
                    df.rename(columns={col: 'Datetime'}, inplace=True)
                    break
            return df
        except Exception as e:
            print(f"Error loading CSV: {e}")
            return None
    
    def get_historical_data(self, symbol, period="5y", interval="1d"):
        # CSV data might contain multiple symbols
        if self.data is not None and 'symbol' in self.data.columns:
            symbol_data = self.data[self.data['symbol'] == symbol]
            if not symbol_data.empty:
                return symbol_data
        return self.data  # Return all data if no symbol filtering
    
    def get_company_info(self, symbol):
        return {}

class DataSourceFactory:
    """Factory class to create data sources"""
    
    @staticmethod
    def create_source(source_type, **kwargs):
        sources = {
            'yahoo': YahooFinanceSource,
            'alphavantage': AlphaVantageSource,
            'iex': IEXCloudSource,
            'csv': CSVDataSource
        }
        
        source_class = sources.get(source_type.lower())
        if source_class:
            return source_class(**kwargs)
        else:
            raise ValueError(f"Unknown data source: {source_type}")
    
    @staticmethod
    def get_available_sources():
        return ['yahoo', 'alphavantage', 'iex', 'csv']
