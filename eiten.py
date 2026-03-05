import math
import numpy as np
import matplotlib.pyplot as plt
import sys
import pandas as pd

# Load our modules
from data_loader import DataEngine
from simulator import MontoCarloSimulator
from backtester import BackTester
from strategy_manager import StrategyManager


class Eiten:
    def __init__(self, args):
        plt.style.use('seaborn-v0_8-white')
        plt.rc('grid', linestyle="dotted", color='#a0a0a0')
        plt.rcParams['axes.edgecolor'] = "#04383F"
        plt.rcParams['figure.figsize'] = (12, 6)

        print("\n--* Eiten has been initialized...")
        self.args = args

        # Create data engine
        self.dataEngine = DataEngine(args)

        # Monto carlo simulator
        self.simulator = MontoCarloSimulator()

        # Strategy manager
        self.strategyManager = StrategyManager()

        # Back tester
        self.backTester = BackTester()

        # Data dictionary
        self.data_dictionary = {}

        print('\n')

    def calculate_percentage_change(self, old, new):
        """
        Calculate percentage change
        """
        return ((new - old) * 100) / old

    def create_returns(self, historical_price_info):
    	returns_matrix = []
    	returns_matrix_percentages = []
    	predicted_return_vectors = []
    	
    	for i in range(0, len(historical_price_info)):
    		# Get the DataFrame for this symbol
    		df = historical_price_info[i]
    		
    		# Check if it's a DataFrame and has the Close column
    		if not isinstance(df, pd.DataFrame):
    			print(f"Warning: historical_price_info[{i}] is not a DataFrame: {type(df)}")
    			continue
    		
    		# Handle MultiIndex columns (like from yfinance)
    		if isinstance(df.columns, pd.MultiIndex):
    			# Get the Close column values (first ticker's Close)
    			close_series = df.loc[:, ('Close', slice(None))].iloc[:, 0]
    			close_prices = close_series.values.tolist()
    		else:
    			# Simple DataFrame
    			if 'Close' not in df.columns:
    				print(f"Warning: 'Close' column not found in DataFrame. Columns: {df.columns.tolist()}")
    				continue
    			close_prices = df['Close'].values.tolist()
    		
    		# Ensure close_prices is a flat list of numbers
    		# If it's still nested, flatten it
    		if close_prices and isinstance(close_prices[0], list):
    			close_prices = [item[0] if isinstance(item, list) else item for item in close_prices]
 
    		# Need at least 2 prices to calculate returns
    		if len(close_prices) < 2:
    			print(f"Warning: Not enough close prices for symbol at index {i}: {len(close_prices)}")
    			continue
    		
    		# Calculate returns
    		log_returns = []
    		percentage_returns = []
    		
    		for j in range(1, len(close_prices)):
    			try:
    				# Ensure we're working with numbers
    				prev_price = float(close_prices[j-1])
    				curr_price = float(close_prices[j])
    				log_return = math.log(curr_price / prev_price)
    				log_returns.append(log_return)
    				pct_return = self.calculate_percentage_change(prev_price, curr_price)
    				percentage_returns.append(pct_return)
    			except Exception as e:
    				print(f"Error calculating return at index {j}: {e}")
    				print(f"  prev_price: {close_prices[j-1]} ({type(close_prices[j-1])})")
    				print(f"  curr_price: {close_prices[j]} ({type(close_prices[j])})")
    				continue
    				
    		total_data = len(close_prices)
    		
    		# Expected returns in future
    		try:
    			future_expected_returns = np.mean([(self.calculate_percentage_change(close_prices[j - 1], close_prices[j])) / 
                                              (total_data - j) for j in range(1, len(close_prices))])
    		except Exception as e:
    			print(f"Error calculating future expected returns: {e}")
    			future_expected_returns = 0
    		
    		# Add to matrices
    		returns_matrix.append(log_returns)
    		returns_matrix_percentages.append(percentage_returns)
    		predicted_return_vectors.append(future_expected_returns)
    	
    	# Convert to numpy arrays for one liner calculations
    	if len(returns_matrix) == 0:
    		print("Warning: No returns data generated!")
    		return np.array([]), np.array([]), np.array([])
    	
    	predicted_return_vectors = np.array(predicted_return_vectors)
    	returns_matrix = np.array(returns_matrix)
    	returns_matrix_percentages = np.array(returns_matrix_percentages)
    	
    	return predicted_return_vectors, returns_matrix, returns_matrix_percentages

    def load_data(self):
        """
        Loads data needed for analysis
        """
        # Gather data for all stocks in a dictionary format
        # Dictionary keys will be -> historical_prices, future_prices
        self.data_dictionary = self.dataEngine.collect_data_for_all_tickers()

        # Add data to lists
        symbol_names = list(sorted(self.data_dictionary.keys()))
        historical_price_info, future_prices = [], []
        for symbol in symbol_names:
            historical_price_info.append(
                self.data_dictionary[symbol]["historical_prices"])
            future_prices.append(self.data_dictionary[symbol]["future_prices"])

        # Get return matrices and vectors
        predicted_return_vectors, returns_matrix, returns_matrix_percentages = self.create_returns(
            historical_price_info)
        return historical_price_info, future_prices, symbol_names, predicted_return_vectors, returns_matrix, returns_matrix_percentages

    def run_strategies(self):
        """
        Run strategies, back and future test them, and simulate the returns.
        """
        historical_price_info, future_prices, symbol_names, predicted_return_vectors, returns_matrix, returns_matrix_percentages = self.load_data()
        historical_price_market, future_prices_market = self.dataEngine.get_market_index_price()
        
        # DETAILED DIAGNOSTICS - Find exact root cause
        print("\n" + "="*50)
        print("DATA LOADING DIAGNOSTICS")
        print("="*50)
        print(f"Number of symbols: {len(symbol_names)}")
        print(f"Symbols: {symbol_names}")
        print(f"Returns matrix shape: {returns_matrix.shape}")
        print(f"Returns matrix type: {type(returns_matrix)}")
        
        # Check each symbol's data
        print("\n--- Individual Symbol Data ---")
        for i, symbol in enumerate(symbol_names):
        	hist_data = self.data_dictionary[symbol]["historical_prices"]
        	future_data = self.data_dictionary[symbol]["future_prices"]
        	print(f"\n{symbol}:")
        	print(f"  Historical data type: {type(hist_data)}")
        	if hasattr(hist_data, 'shape'):
        		print(f"  Historical data shape: {hist_data.shape}")
        	elif isinstance(hist_data, list):
        		print(f"  Historical data length: {len(hist_data)}")
        	else:
        		print(f"  Historical data: {hist_data}")
        	print(f"  Future data type: {type(future_data)}")
        	if hasattr(future_data, 'shape'):
        		print(f"  Future data shape: {future_data.shape}")
        	elif isinstance(future_data, list):
        		print(f"  Future data length: {len(future_data)}")
        
        # Check the create_returns function output
        print("\n--- Returns Matrix Details ---")
        print(f"Returns matrix shape: {returns_matrix.shape}")
        if returns_matrix.shape[1] == 0:
        	print("❌ CRITICAL: No time periods in returns matrix!")
        	
        	# Try to recreate returns manually to see where it fails
        	print("\n--- Manual Returns Calculation Test ---")
        	for i, symbol in enumerate(symbol_names):
        		hist_data = self.data_dictionary[symbol]["historical_prices"]
        		if isinstance(hist_data, pd.DataFrame):
        			if 'Close' in hist_data.columns:
        				close_prices = hist_data['Close'].values
        				print(f"{symbol}: Close prices length = {len(close_prices)}")
        				if len(close_prices) > 1:
        					try:
        						returns = [self.calculate_percentage_change(close_prices[i-1], close_prices[i]) 
        						for i in range(1, len(close_prices))]
        						print(f"  Successfully calculated {len(returns)} returns")
        					except Exception as e:
        						print(f"  Error calculating returns: {e}")
        				else:
        					print(f"  Not enough close prices (need at least 2)")
        			else:
        				print(f"  No 'Close' column found. Columns: {hist_data.columns.tolist()}")
        		else:
        			print(f"  Historical data is not a DataFrame: {type(hist_data)}")
        			
        print("="*50 + "\n")
        
        # Check if returns_matrix has data
        if returns_matrix.shape[1] == 0:
        	print("\n❌ ERROR: Returns matrix has no time periods data!")
        	print("\nEXACT ROOT CAUSE:")
        	print("The create_returns() function failed to generate any returns because:")
        	
        	# Determine the exact cause
        	if len(symbol_names) == 0:
        		print("  - No symbols were successfully loaded from data_loader")
        	else:
        		# Check if historical_price_info is empty
        		if len(historical_price_info) == 0:
        			print("  - historical_price_info is empty")
        		else:
        			# Check first symbol's data
        			first_symbol = symbol_names[0]
        			first_data = self.data_dictionary[first_symbol]["historical_prices"]
        			if isinstance(first_data, pd.DataFrame):
        				if first_data.empty:
        					print(f"  - DataFrame for {first_symbol} is empty")
        				elif 'Close' not in first_data.columns:
        					print(f"  - 'Close' column missing in {first_symbol} data. Columns: {first_data.columns.tolist()}")
        				elif len(first_data) < 2:
        					print(f"  - Insufficient data points for {first_symbol}: only {len(first_data)} row(s)")
        				else:
        					print(f"  - Unknown issue with {first_symbol}. Data head:\n{first_data.head()}")
        			else:
        				print(f"  - Historical data for {first_symbol} is not a DataFrame: {type(first_data)}")
        	
        	print("\nDebug the data_loader.get_data() function to see why it's returning empty/invalid data.")
        	sys.exit(1)
        	

        # Calculate covariance matrix
        covariance_matrix = np.cov(returns_matrix)
        
        # Use random matrix theory to filter out the noisy eigen values
        if self.args.apply_noise_filtering:
        	print("\n** Applying random matrix theory to filter out noise in the covariance matrix...\n")
        	
        	# Check if returns_matrix has enough data and is valid
        	if np.any(np.isnan(returns_matrix)) or np.any(np.isinf(returns_matrix)):
        		print("Warning: NaN or Inf values detected in returns matrix. Cleaning...")
        		returns_matrix = np.nan_to_num(returns_matrix, nan=0.0, posinf=0.0, neginf=0.0)
        	
        	# Check if we have enough data points
        	if returns_matrix.shape[1] < returns_matrix.shape[0]:
        		print(f"Warning: More assets ({returns_matrix.shape[0]}) than time periods ({returns_matrix.shape[1]}). RMT may not work well.")
        	
        	# Only proceed if we have data
        	if returns_matrix.shape[1] > 0:
        		try:
        			covariance_matrix = self.strategyManager.random_matrix_theory_based_cov(returns_matrix)
        		except Exception as e:
        			print(f"RMT filtering failed: {e}. Using original covariance matrix.")
        	else:
        		print("Warning: No time periods data available. Skipping RMT filtering.")

        # Get weights for the portfolio
        eigen_portfolio_weights_dictionary = self.strategyManager.calculate_eigen_portfolio(
            symbol_names, covariance_matrix, self.args.eigen_portfolio_number)
        mvp_portfolio_weights_dictionary = self.strategyManager.calculate_minimum_variance_portfolio(
            symbol_names, covariance_matrix)
        msr_portfolio_weights_dictionary = self.strategyManager.calculate_maximum_sharpe_portfolio(
            symbol_names, covariance_matrix, predicted_return_vectors)
        ga_portfolio_weights_dictionary = self.strategyManager.calculate_genetic_algo_portfolio(
            symbol_names, returns_matrix_percentages)

        # Print weights
        print("\n*% Printing portfolio weights...")
        self.print_and_plot_portfolio_weights(
            eigen_portfolio_weights_dictionary, 'Eigen Portfolio', plot_num=1)
        self.print_and_plot_portfolio_weights(
            mvp_portfolio_weights_dictionary, 'Minimum Variance Portfolio (MVP)', plot_num=2)
        self.print_and_plot_portfolio_weights(
            msr_portfolio_weights_dictionary, 'Maximum Sharpe Portfolio (MSR)', plot_num=3)
        self.print_and_plot_portfolio_weights(
            ga_portfolio_weights_dictionary, 'Genetic Algo (GA)', plot_num=4)
        self.draw_plot("output/weights.png")

        # Back test
        print("\n*& Backtesting the portfolios...")
        self.backTester.back_test(symbol_names, eigen_portfolio_weights_dictionary,
                                  self.data_dictionary,
                                  historical_price_market,
                                  self.args.only_long,
                                  market_chart=True,
                                  strategy_name='Eigen Portfolio')
        self.backTester.back_test(symbol_names,
                                  mvp_portfolio_weights_dictionary,
                                  self.data_dictionary, historical_price_market,
                                  self.args.only_long,
                                  market_chart=False,
                                  strategy_name='Minimum Variance Portfolio (MVP)')
        self.backTester.back_test(symbol_names, msr_portfolio_weights_dictionary,
                                  self.data_dictionary,
                                  historical_price_market,
                                  self.args.only_long,
                                  market_chart=False,
                                  strategy_name='Maximum Sharpe Portfolio (MSR)')
        self.backTester.back_test(symbol_names,
                                  ga_portfolio_weights_dictionary,
                                  self.data_dictionary,
                                  historical_price_market,
                                  self.args.only_long,
                                  market_chart=False,
                                  strategy_name='Genetic Algo (GA)')
        self.draw_plot("output/backtest.png")

        if self.args.is_test:
            print("\n#^ Future testing the portfolios...")
            # Future test
            self.backTester.future_test(symbol_names,
                                        eigen_portfolio_weights_dictionary,
                                        self.data_dictionary,
                                        future_prices_market,
                                        self.args.only_long,
                                        market_chart=True,
                                        strategy_name='Eigen Portfolio')
            self.backTester.future_test(symbol_names,
                                        mvp_portfolio_weights_dictionary,
                                        self.data_dictionary,
                                        future_prices_market,
                                        self.args.only_long,
                                        market_chart=False,
                                        strategy_name='Minimum Variance Portfolio (MVP)')
            self.backTester.future_test(symbol_names,
                                        msr_portfolio_weights_dictionary,
                                        self.data_dictionary,
                                        future_prices_market,
                                        self.args.only_long,
                                        market_chart=False,
                                        strategy_name='Maximum Sharpe Portfolio (MSR)')
            self.backTester.future_test(symbol_names,
                                        ga_portfolio_weights_dictionary,
                                        self.data_dictionary,
                                        future_prices_market,
                                        self.args.only_long,
                                        market_chart=False,
                                        strategy_name='Genetic Algo (GA)')
            self.draw_plot("output/future_tests.png")

        # Simulation
        print("\n+$ Simulating future prices using monte carlo...")
        self.simulator.simulate_portfolio(symbol_names,
                                          eigen_portfolio_weights_dictionary,
                                          self.data_dictionary,
                                          future_prices_market,
                                          self.args.is_test,
                                          market_chart=True,
                                          strategy_name='Eigen Portfolio')
        self.simulator.simulate_portfolio(symbol_names,
                                          eigen_portfolio_weights_dictionary,
                                          self.data_dictionary,
                                          future_prices_market,
                                          self.args.is_test,
                                          market_chart=False,
                                          strategy_name='Minimum Variance Portfolio (MVP)')
        self.simulator.simulate_portfolio(symbol_names,
                                          eigen_portfolio_weights_dictionary,
                                          self.data_dictionary,
                                          future_prices_market,
                                          self.args.is_test,
                                          market_chart=False,
                                          strategy_name='Maximum Sharpe Portfolio (MSR)')
        self.simulator.simulate_portfolio(symbol_names,
                                          ga_portfolio_weights_dictionary,
                                          self.data_dictionary,
                                          future_prices_market,
                                          self.args.is_test,
                                          market_chart=False,
                                          strategy_name='Genetic Algo (GA)')
        self.draw_plot("output/monte_carlo.png")

    def draw_plot(self, filename="output/graph.png"):
        """
        Draw plots
        """
        # Styling for plots

        plt.grid()
        plt.legend(fontsize=14)
        plt.tight_layout()
        plt.show()
        
        """if self.args.save_plot:
            plt.savefig(filename)
        else:
            plt.tight_layout()
            plt.show()""" # Plots were not being generated properly. Need to fix this.

    def print_and_plot_portfolio_weights(self, weights_dictionary: dict, strategy, plot_num: int) -> None:
        print("\n-------- Weights for %s --------" % strategy)
        symbols = list(sorted(weights_dictionary.keys()))
        symbol_weights = []
        for symbol in symbols:
            print("Symbol: %s, Weight: %.4f" %
                  (symbol, weights_dictionary[symbol]))
            symbol_weights.append(weights_dictionary[symbol])

        # Plot
        width = 0.1
        x = np.arange(len(symbol_weights))
        plt.bar(x + (width * (plot_num - 1)) + 0.05,
                symbol_weights, label=strategy, width=width)
        plt.xticks(x, symbols, fontsize=14)
        plt.yticks(fontsize=14)
        plt.xlabel("Symbols", fontsize=14)
        plt.ylabel("Weight in Portfolio", fontsize=14)
        plt.title("Portfolio Weights for Different Strategies", fontsize=14)
