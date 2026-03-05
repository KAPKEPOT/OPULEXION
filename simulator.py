# Basic libraries
import os
import sys
import math
import scipy
import random
import collections
import numpy as np
import pandas as pd
import scipy.stats as st
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings("ignore")

# Styling for plots
plt.style.use('seaborn-v0_8-white')
plt.rc('grid', linestyle="dotted", color='#a0a0a0')
plt.rcParams['axes.edgecolor'] = "#04383F"


class MontoCarloSimulator:
	"""
	Monto carlo simulator that calculates the historical returns distribution and uses it to predict the future returns
	"""

	def __init__(self):
		print("\n--$ Simulator has been initialized")

	def calculate_percentage_change(self, old, new):
		"""
		Percentage change
		"""
		return ((new - old) * 100) / old

	def draw_portfolio_performance_chart(self, returns_matrix, portfolio_weights_dictionary, strategy_name): 
		"""
		Draw returns chart for portfolio performance
		"""

		# Get portfolio returns
		returns_matrix = np.array(returns_matrix).transpose()
		portfolio_weights_vector = np.array([portfolio_weights_dictionary[symbol] for symbol in portfolio_weights_dictionary]).transpose()
		portfolio_returns = np.dot(returns_matrix, portfolio_weights_vector)
		portfolio_returns_cumulative = np.cumsum(portfolio_returns)

		# Plot
		x = np.arange(len(portfolio_returns_cumulative))
		plt.axhline(y = 0, linestyle = 'dotted', alpha = 0.3, color = 'black')
		plt.plot(x, portfolio_returns_cumulative, linewidth = 2.0, label = "Projected Returns from " + str(strategy_name))
		plt.title("Simulated Future Returns", fontsize = 14)
		plt.xlabel("Bars (Time Sorted)", fontsize = 14)
		plt.ylabel("Cumulative Percentage Return", fontsize = 14)
		plt.xticks(fontsize = 14)
		plt.yticks(fontsize = 14)

	def draw_market_performance_chart(self, actual_returns, strategy_name):
		"""
		Draw actual market returns if future data is available
		"""

		# Get market returns
		cumulative_returns = np.cumsum(actual_returns)

		# Plot
		x = np.arange(len(cumulative_returns))
		plt.axhline(y = 0, linestyle = 'dotted', alpha = 0.3, color = 'black')
		plt.plot(x, cumulative_returns, linewidth = 2.0, color = '#282828', linestyle = '--', label = "Market Index Returns")
		plt.title("Simulated Future Returns", fontsize = 14)
		plt.xlabel("Bars (Time Sorted)", fontsize = 14)
		plt.ylabel("Cumulative Percentage Return", fontsize = 14)
		plt.xticks(fontsize = 14)
		plt.yticks(fontsize = 14)

	def simulate_portfolio(self, symbol_names, portfolio_weights_dictionary, portfolio_data_dictionary, future_prices_market, test_or_predict, market_chart, strategy_name, simulation_timesteps = 25):
		returns_matrix = []
		actual_returns_matrix = []
		
		# Iterate over each symbol to get their returns
		for symbol in symbol_names:
			# Get symbol returns using monte carlo
			hist_data = portfolio_data_dictionary[symbol]["historical_prices"]
			
			# Handle different data structures for historical prices
			if isinstance(hist_data, pd.DataFrame):
				# If it's a DataFrame with MultiIndex columns
				if isinstance(hist_data.columns, pd.MultiIndex):
					# Get the Close column values as a flat list
					close_series = hist_data.loc[:, ('Close', slice(None))].iloc[:, 0]
					historical_close_prices = close_series.values.tolist()
				else:
					# Simple DataFrame
					historical_close_prices = hist_data['Close'].values.tolist()
			elif isinstance(hist_data, list):
				# If it's already a list, use it directly
				historical_close_prices = hist_data
			else:
				print(f"Warning: Unexpected data type for {symbol}: {type(hist_data)}")
				continue
			
			# Ensure we have a flat list of numbers
			if historical_close_prices and isinstance(historical_close_prices[0], (list, np.ndarray)):
				# Flatten if nested
				historical_close_prices = [float(x[0]) if isinstance(x, (list, np.ndarray)) else float(x) 
                                     for x in historical_close_prices]			
			else:
				# Convert to float to be safe
				historical_close_prices = [float(x) for x in historical_close_prices]
			
			# Get future data length
			future_data = portfolio_data_dictionary[symbol]["future_prices"]
			future_len = len(future_data) if future_data else 0
			
			future_price_predictions, _ = self.simulate_and_get_future_prices(
			    historical_close_prices,
			    simulation_timesteps=max(simulation_timesteps, future_len)
			)
			
			# Calculate returns from predictions
			predicted_future_returns = []
			for i in range(1, len(future_price_predictions)):
				try:
					ret = self.calculate_percentage_change(
					    future_price_predictions[i - 1],
					    future_price_predictions[i]
					)
					predicted_future_returns.append(ret)
				except Exception as e:
					print(f"Error calculating return at index {i}: {e}")
					continue
			returns_matrix.append(predicted_future_returns)
		
		# Get portfolio returns
		if returns_matrix:
			self.draw_portfolio_performance_chart(returns_matrix, portfolio_weights_dictionary, strategy_name)
		else:
			print(f"Warning: No returns generated for {strategy_name}")
		
	def simulate_and_get_future_prices(self, historical_prices, simulation_timesteps=25):

		if isinstance(historical_prices, (list, np.ndarray)):
			# Convert to list of floats
			close_prices = [float(x) for x in historical_prices]
		else:
			print(f"Warning: Unexpected historical_prices type: {type(historical_prices)}")
			return [], []
		
		# Get log returns from historical data
		returns = []
		for i in range(1, len(close_prices)):
			try:
				ret = math.log(close_prices[i] / close_prices[i - 1])
				returns.append(ret)
			except Exception as e:
				print(f"Error calculating log return: {e}")
				
				continue
				
		if len(returns) == 0:
			print("Warning: No returns calculated from historical data")
			return [], []
		
		# Get distribution of returns
		try:
			hist = np.histogram(returns, bins=32)
			hist_dist = scipy.stats.rv_histogram(hist)  # Distribution function
		except Exception as e:
			print(f"Error creating distribution: {e}")
			return [], []
			
		predicted_prices = []
		# Do 25 iterations to simulate prices
		for iteration in range(25):
			new_close_prices = [close_prices[-1]]
			for i in range(simulation_timesteps):
				try:
					random_value = random.uniform(0, 1)
					return_value = float(np.exp(hist_dist.ppf(random_value)))  # Get simulated return
					price_last_point = new_close_prices[-1]
					price_next_point = price_last_point * return_value
					
					# Add to list
					new_close_prices.append(price_next_point)
				except Exception as e:
					print(f"Error in simulation iteration {iteration}, step {i}: {e}")
					# Add the last price again to maintain length
					new_close_prices.append(new_close_prices[-1])
			
			predicted_prices.append(new_close_prices)
		
		# Calculate confidence intervals and average future returns
		try:
			predicted_prices_mean = np.mean(predicted_prices, axis=0)
			conf_intervals = st.t.interval(0.95, len(predicted_prices), 
                                       loc=predicted_prices_mean, 
                                       scale=st.sem(predicted_prices, axis=0))
		except Exception as e:
			print(f"Error calculating confidence intervals: {e}")
			predicted_prices_mean = np.mean(predicted_prices, axis=0) if predicted_prices else []
			conf_intervals = ([], [])
		return predicted_prices_mean.tolist(), conf_intervals

	def is_nan(self, object):
		"""
		Check if object is null
		"""
		return object != object

		
