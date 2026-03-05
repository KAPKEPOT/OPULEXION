# Basic libraries
import os
import random
import warnings
import numpy as np
warnings.filterwarnings("ignore")

class StrategyHelperFunctions:
	def __init__(self):
		print("Helper functions have been created")
		
	def random_matrix_theory_based_cov(self, returns_matrix):
		"""
		This is inspired by the excellent post @ https://srome.github.io/Eigenvesting-III-Random-Matrix-Filtering-In-Finance/
		"""

		# Calculate variance and std, will come in handy during reconstruction
		if np.any(np.isnan(returns_matrix)) or np.any(np.isinf(returns_matrix)):
			print("Warning: NaN or Inf values found in returns matrix. Cleaning data...")
			returns_matrix = np.nan_to_num(returns_matrix, nan=0.0, posinf=0.0, neginf=0.0)
		
		# Calculate variance and std, will come in handy during reconstruction
		try:
			variances = np.diag(np.cov(returns_matrix))
		except Exception as e:
			print(f"Error computing covariance: {e}")
			# Return original covariance matrix if filtering fails
			return np.cov(returns_matrix)
		
		standard_deviations = np.sqrt(variances)
		
		# Get correlation matrix and compute eigen vectors and values
		try:
			correlation_matrix = np.corrcoef(returns_matrix)
			
			# Check if correlation matrix is valid
			if np.any(np.isnan(correlation_matrix)) or np.any(np.isinf(correlation_matrix)):
				correlation_matrix = np.nan_to_num(correlation_matrix, nan=0.0, posinf=1.0, neginf=-1.0)
				np.fill_diagonal(correlation_matrix, 1.0)  # Diagonal should be 1
			
			# Add small regularization term to ensure positive definiteness
			n = correlation_matrix.shape[0]
			correlation_matrix = correlation_matrix + 1e-8 * np.eye(n)
			
			eig_values, eig_vectors = np.linalg.eigh(correlation_matrix)
		
		except np.linalg.LinAlgError as e:
			print(f"Eigenvalue computation failed: {e}. Returning original covariance matrix.")
			return np.cov(returns_matrix)
		
		# Get maximum theoretical eigen value for a random matrix
		sigma = 1  # The variance for all of the standardized log returns is 1
		Q = len(returns_matrix[0]) / len(returns_matrix)
		max_theoretical_eval = np.power(sigma*(1 + np.sqrt(1/Q)), 2)
		
		# Prune random eigen values
		eig_values_pruned = eig_values[eig_values > max_theoretical_eval]
		eig_values[eig_values <= max_theoretical_eval] = 0
		
		# Reconstruct the covariance matrix from the correlation matrix and filtered eigen values
		try:
			temp = np.dot(eig_vectors, np.dot(np.diag(eig_values), np.transpose(eig_vectors)))
			np.fill_diagonal(temp, 1)
			filtered_matrix = temp
			filtered_cov_matrix = np.dot(
			    np.diag(standard_deviations),
			    np.dot(filtered_matrix, np.diag(standard_deviations))			    
			)
		except Exception as e:
			print(f"Error reconstructing matrix: {e}. Returning original covariance matrix.")
			return np.cov(returns_matrix)
		return filtered_cov_matrix