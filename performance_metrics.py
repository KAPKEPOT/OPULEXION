"""
Advanced performance metrics for portfolio analysis
"""

import numpy as np
import pandas as pd
from scipy import stats

class PerformanceAnalyzer:
    def __init__(self):
        self.metrics = {}
    
    def calculate_all_metrics(self, data_dictionary, symbol_names):
        """
        Calculate comprehensive performance metrics for all strategies
        """
        strategies = ['Eigen', 'MVP', 'MSR', 'GA']
        results = {}
        
        for strategy in strategies:
            metrics = self.calculate_strategy_metrics(
                data_dictionary, symbol_names, strategy
            )
            results[strategy] = metrics
        
        return pd.DataFrame(results).T
    
    def calculate_strategy_metrics(self, data_dictionary, symbol_names, strategy):
        """
        Calculate metrics for a specific strategy
        """
        # Get returns for this strategy (you'll need to implement this based on your data structure)
        returns = self.get_strategy_returns(data_dictionary, symbol_names, strategy)
        
        if len(returns) == 0:
            return {}
        
        metrics = {}
        
        # 1. Sharpe Ratio (already exists)
        metrics['Sharpe Ratio'] = self.sharpe_ratio(returns)
        
        # 2. Sortino Ratio (downside risk only)
        metrics['Sortino Ratio'] = self.sortino_ratio(returns)
        
        # 3. Calmar Ratio (return vs max drawdown)
        metrics['Calmar Ratio'] = self.calmar_ratio(returns)
        
        # 4. Maximum Drawdown
        metrics['Max Drawdown'] = self.max_drawdown(returns)
        
        # 5. Win Rate
        metrics['Win Rate'] = self.win_rate(returns)
        
        # 6. Profit Factor
        metrics['Profit Factor'] = self.profit_factor(returns)
        
        # 7. Alpha & Beta
        market_returns = self.get_market_returns(data_dictionary)
        alpha, beta = self.alpha_beta(returns, market_returns)
        metrics['Alpha'] = alpha
        metrics['Beta'] = beta
        
        # 8. Annualized Return
        metrics['Annual Return'] = self.annualized_return(returns)
        
        # 9. Annualized Volatility
        metrics['Volatility'] = self.annualized_volatility(returns)
        
        # 10. Value at Risk (95%)
        metrics['VaR (95%)'] = self.value_at_risk(returns)
        
        # 11. Conditional VaR (Expected Shortfall)
        metrics['CVaR (95%)'] = self.conditional_var(returns)
        
        # 12. Skewness
        metrics['Skewness'] = self.skewness(returns)
        
        # 13. Kurtosis
        metrics['Kurtosis'] = self.kurtosis(returns)
        
        # 14. Information Ratio
        metrics['Information Ratio'] = self.information_ratio(returns, market_returns)
        
        # 15. Treynor Ratio
        metrics['Treynor Ratio'] = self.treynor_ratio(returns, beta)
        
        return metrics
    
    def sharpe_ratio(self, returns, risk_free_rate=0.02):
        """Calculate Sharpe Ratio"""
        excess_returns = np.mean(returns) - risk_free_rate/252
        return excess_returns / np.std(returns) * np.sqrt(252)
    
    def sortino_ratio(self, returns, risk_free_rate=0.02):
        """Calculate Sortino Ratio (uses downside deviation)"""
        excess_returns = np.mean(returns) - risk_free_rate/252
        downside_returns = [r for r in returns if r < 0]
        downside_dev = np.std(downside_returns) if downside_returns else 1
        return excess_returns / downside_dev * np.sqrt(252)
    
    def calmar_ratio(self, returns):
        """Calculate Calmar Ratio (return vs max drawdown)"""
        annual_return = np.mean(returns) * 252
        max_dd = self.max_drawdown(returns)
        return annual_return / abs(max_dd) if max_dd != 0 else 0
    
    def max_drawdown(self, returns):
        """Calculate Maximum Drawdown"""
        cumulative = np.cumprod(1 + np.array(returns))
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        return np.min(drawdown)
    
    def win_rate(self, returns):
        """Calculate percentage of positive returns"""
        positive = len([r for r in returns if r > 0])
        return positive / len(returns)
    
    def profit_factor(self, returns):
        """Calculate Profit Factor (gross profit / gross loss)"""
        gross_profit = sum([r for r in returns if r > 0])
        gross_loss = abs(sum([r for r in returns if r < 0]))
        return gross_profit / gross_loss if gross_loss != 0 else float('inf')
    
    def alpha_beta(self, returns, market_returns):
        """Calculate Alpha and Beta relative to market"""
        if len(market_returns) == 0:
            return 0, 1
        
        # Ensure same length
        min_len = min(len(returns), len(market_returns))
        returns = returns[:min_len]
        market_returns = market_returns[:min_len]
        
        # Linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(
            market_returns, returns
        )
        
        return intercept * 252, slope  # Annualized alpha
    
    def annualized_return(self, returns):
        """Calculate annualized return"""
        total_return = np.prod(1 + np.array(returns)) - 1
        return (1 + total_return) ** (252 / len(returns)) - 1
    
    def annualized_volatility(self, returns):
        """Calculate annualized volatility"""
        return np.std(returns) * np.sqrt(252)
    
    def value_at_risk(self, returns, confidence=0.95):
        """Calculate Value at Risk"""
        return np.percentile(returns, (1 - confidence) * 100)
    
    def conditional_var(self, returns, confidence=0.95):
        """Calculate Conditional VaR (Expected Shortfall)"""
        var = self.value_at_risk(returns, confidence)
        return np.mean([r for r in returns if r <= var])
    
    def skewness(self, returns):
        """Calculate skewness of returns"""
        return stats.skew(returns)
    
    def kurtosis(self, returns):
        """Calculate kurtosis of returns"""
        return stats.kurtosis(returns)
    
    def information_ratio(self, returns, benchmark_returns):
        """Calculate Information Ratio"""
        if len(benchmark_returns) == 0:
            return 0
        
        # Ensure same length
        min_len = min(len(returns), len(benchmark_returns))
        returns = returns[:min_len]
        benchmark_returns = benchmark_returns[:min_len]
        
        active_return = np.mean(returns) - np.mean(benchmark_returns)
        tracking_error = np.std(returns - benchmark_returns)
        
        return active_return / tracking_error * np.sqrt(252) if tracking_error != 0 else 0
    
    def treynor_ratio(self, returns, beta, risk_free_rate=0.02):
        """Calculate Treynor Ratio"""
        if beta == 0:
            return 0
        excess_return = np.mean(returns) * 252 - risk_free_rate
        return excess_return / beta
    
    def get_strategy_returns(self, data_dictionary, symbol_names, strategy):
        """Get returns for a specific strategy - implement based on your data structure"""
        # This needs to be implemented based on how you store strategy returns
        # For now, return empty list
        return []
    
    def get_market_returns(self, data_dictionary):
        """Get market returns for benchmark comparison"""
        # This needs to be implemented
        return []