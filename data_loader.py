# Basic libraries
import os
import collections
import pandas as pd
import yfinance as yf
from tqdm import tqdm
import warnings
warnings.filterwarnings("ignore")


class DataEngine:
    def __init__(self, args):
        print("\n--> Data engine has been initialized...")
        self.args = args

        # Stocks list
        self.directory_path = str(os.path.dirname(os.path.abspath(__file__)))
        self.stocks_file_path = f"{self.directory_path}/{self.args.stocks_file_path}"
        self.stocks_list = []

        # Load stock names in a list
        self.load_stocks_from_file()

        # Dictionary to store data. This will only store and save data if the argument is_save_dictionary is 1.
        self.data_dictionary = {}

        # Data length
        self.stock_data_length = []

    def load_stocks_from_file(self):
        """
        Load stock names from the file
        """
        print("Loading all stocks from file...")
        stocks_list = open(self.stocks_file_path, "r").readlines()
        stocks_list = [str(item).strip("\n") for item in stocks_list]

        # Load symbols
        stocks_list = list(sorted(set(stocks_list)))
        print("Total number of stocks: %d" % len(stocks_list))
        self.stocks_list = stocks_list

    def get_most_frequent_key(self, input_list):
        counter = collections.Counter(input_list)
        return list(counter.keys())[0]

    def get_data(self, symbol):
        """
        Get stock data from yahoo finance.
        """
        future_prices = None
        historical_prices = None
        
        # FIX: Better period selection logic
        if self.args.data_granularity_minutes == 1:
            period = "7d"
            interval = "1m"
        elif self.args.data_granularity_minutes == 5:
            period = "1mo"
            interval = "5m"
        elif self.args.data_granularity_minutes == 15:
            period = "2mo"
            interval = "15m"
        elif self.args.data_granularity_minutes == 30:
            period = "3mo"
            interval = "30m"
        elif self.args.data_granularity_minutes == 60:
            period = "6mo"
            interval = "60m"
        elif self.args.data_granularity_minutes == 3600:
            period = "5y"
            interval = "1d"
        else:
            # Default for unsupported granularities
            period = "30d"
            interval = str(self.args.data_granularity_minutes) + "m"

        # Get stock price
        try:
            # Stock price
            stock_prices = yf.download(
                tickers=symbol,
                period=period,
                interval=interval,
                auto_adjust=False,
                progress=False)
            
            # Check if we got any data
            if stock_prices.empty:
                print(f"Warning: No data for {symbol}")
                return [], [], True
                
            stock_prices = stock_prices.reset_index()
            
            # Handle different column names based on yfinance version
            if 'Date' in stock_prices.columns:
                stock_prices.rename(columns={'Date': 'Datetime'}, inplace=True)
            
            try:
                if "Adj Close" in stock_prices.columns:
                    stock_prices = stock_prices.drop(columns=["Adj Close"])
            except Exception as e:
                pass

            data_length = stock_prices.shape[0]
            self.stock_data_length.append(data_length)

            # After getting some data, ignore partial data from yfinance
            # based on number of data samples
            if len(self.stock_data_length) > 5:
                most_frequent_key = self.get_most_frequent_key(
                    self.stock_data_length)
                if (data_length != most_frequent_key and
                    data_length != self.args.history_to_use and
                        symbol != self.args.market_index):  # Needs index
                    return [], [], True

            # FIX: Handle "all" case properly
            if self.args.history_to_use == "all":
                # For some reason, yfinance gives some 0 values in the first index
                if data_length > 1:
                    stock_prices = stock_prices.iloc[1:]
                # Keep all data, don't truncate
            else:
                # Make sure we don't try to slice more than we have
                history = int(self.args.history_to_use)
                if data_length >= history:
                    stock_prices = stock_prices.iloc[-history:]
                else:
                    print(f"Warning: Not enough data for {symbol}. Requested {history}, got {data_length}")
                    return [], [], True

            if self.args.is_test == 1:
                # Make sure we have enough data for future_bars
                future_bars = int(self.args.future_bars)
                if stock_prices.shape[0] > future_bars:
                    future_prices = stock_prices.iloc[-future_bars:]
                    historical_prices = stock_prices.iloc[:-future_bars]
                else:
                    print(f"Warning: Not enough data for {symbol} to split into historical and future")
                    return [], [], True
            else:
                historical_prices = stock_prices
                future_prices = pd.DataFrame()  # Empty dataframe for future

            if stock_prices.shape[0] == 0:
                return [], [], True
                
        except Exception as e:
            print(f"Exception for {symbol}: {e}")
            return [], [], True

        # Convert future_prices to list if it's a DataFrame
        if future_prices is not None and not future_prices.empty:
            future_prices_list = future_prices.values.tolist()
        else:
            future_prices_list = []
            
        return historical_prices, future_prices_list, False

    def get_market_index_price(self):
        """
        Gets market index price e.g SPY. One can change it to some other index
        """
        symbol = self.args.market_index
        stock_price_data, future_prices, not_found = self.get_data(symbol)
        if not_found or stock_price_data is None:
            return None, None

        return stock_price_data, future_prices

    def collect_data_for_all_tickers(self):
        """
        Iterates over all symbols and collects their data
        """

        print("Loading data for all stocks...")
        symbol_names = []
        historical_price = []
        future_price = []

        # Any stock with very low volatility is ignored.
        # You can change this line to address that.
        for i in tqdm(range(len(self.stocks_list))):
            symbol = self.stocks_list[i]
            try:
                stock_price_data, future_prices, not_found = self.get_data(
                    symbol)
                if not not_found and stock_price_data is not None and not stock_price_data.empty:
                    # Add to lists
                    symbol_names.append(symbol)
                    historical_price.append(stock_price_data)
                    future_price.append(future_prices)
                else:
                    print(f"Skipping {symbol} due to data issues")
            except Exception as e:
                print(f"Exception for {symbol}: {e}")
                continue

        # Check if we got any data
        if len(symbol_names) == 0:
            print("ERROR: No data collected for any stock!")
            return {}

        # Sometimes, there are some errors in feature generation or price
        # extraction, let us remove that stuff
        historical_price_info, future_price_info, symbol_names = self.remove_bad_data(
            historical_price, future_price, symbol_names)
        
        for i in range(0, len(symbol_names)):
            self.data_dictionary[symbol_names[i]] = {
                "historical_prices": historical_price_info[i],
                "future_prices": future_price_info[i]}

        print(f"Successfully loaded data for {len(symbol_names)} stocks")
        return self.data_dictionary

    def remove_bad_data(self, historical_price, future_price, symbol_names):
        """
        Remove bad data i.e data that had some errors while scraping or feature generation

        *** This can be much more improved with dicts and filter function.
        """

        # FIX: Handle empty lists
        if len(historical_price) == 0:
            return [], [], []
            
        length_dictionary = collections.Counter(
            [i.shape[0] for i in historical_price])
        if not length_dictionary:
            return [], [], []
            
        length_dictionary = list(length_dictionary.keys())
        most_common_length = length_dictionary[0]

        filtered_historical_price, filtered_future_prices, filtered_symbols = [], [], []
        for i in range(len(future_price)):
            if historical_price[i].shape[0] == most_common_length:
                filtered_symbols.append(symbol_names[i])
                filtered_historical_price.append(historical_price[i])
                filtered_future_prices.append(future_price[i])

        return filtered_historical_price, filtered_future_prices, filtered_symbols