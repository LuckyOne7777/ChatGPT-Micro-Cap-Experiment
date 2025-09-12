"""
Risk analysis for the ChatGPT Micro Cap Experiment.
"""

import pandas as pd
import numpy as np


class RiskAnalyzer:
    """Analyzer for risk metrics calculations."""
    
    def calculate_risk_metrics(self, portfolio_df: pd.DataFrame, drawdown_data: dict, current_cash_balance: float = 0.0) -> dict:
        """Calculate additional risk metrics for the portfolio."""
        # Check if required columns exist
        has_required_columns = ("Cost Basis ($)" in portfolio_df.columns and "Market Value ($)" in portfolio_df.columns)
        
        # Calculate portfolio-level metrics
        if has_required_columns and not portfolio_df.empty:
            total_cost = portfolio_df["Cost Basis ($)"].sum()
            market_value = portfolio_df["Market Value ($)"].sum()
            
            # Adjust total value to include cash
            adjusted_total_value = market_value + current_cash_balance
            
            # Check if Realized Proceeds column exists and include it in ROI calculation
            if "Realized Proceeds ($)" in portfolio_df.columns:
                total_proceeds = portfolio_df["Realized Proceeds ($)"].sum()
                # Correct formula: ROI = ((Proceeds + Market Value + Cash) / Cost Basis - 1) * 100
                overall_roi = ((total_proceeds + market_value) / total_cost - 1) * 100 if total_cost > 0 else 0
                absolute_gain = total_proceeds + market_value - total_cost
            else:
                # Fallback to original calculation if Realized Proceeds column doesn't exist
                overall_roi = ((adjusted_total_value / total_cost) - 1) * 100 if total_cost > 0 else 0
                absolute_gain = adjusted_total_value - total_cost
        else:
            total_cost = 0
            market_value = 0
            adjusted_total_value = current_cash_balance  # When no stocks, total value is just cash
            overall_roi = 0
            absolute_gain = adjusted_total_value
        
        # Calculate average drawdown
        if drawdown_data:
            avg_drawdown = np.mean([data["Max Drawdown (%)"] for data in drawdown_data.values()]) if drawdown_data else 0
            
            # Find worst drawdown
            worst_drawdown_ticker = min(drawdown_data.keys(), 
                                       key=lambda t: drawdown_data[t]["Max Drawdown (%)"])
            worst_drawdown_value = drawdown_data[worst_drawdown_ticker]["Max Drawdown (%)"]
            
            # Find best (least negative) drawdown
            best_drawdown_ticker = max(drawdown_data.keys(), 
                                      key=lambda t: drawdown_data[t]["Max Drawdown (%)"])
            best_drawdown_value = drawdown_data[best_drawdown_ticker]["Max Drawdown (%)"]
            
            # Count stocks with significant drawdowns (>10%)
            significant_drawdown_count = sum(1 for data in drawdown_data.values() 
                                           if data["Max Drawdown (%)"] < -10)
        else:
            avg_drawdown = 0
            worst_drawdown_ticker = "N/A"
            worst_drawdown_value = 0
            best_drawdown_ticker = "N/A"
            best_drawdown_value = 0
            significant_drawdown_count = 0
        
        return {
            'total_cost': total_cost,
            'total_value': adjusted_total_value,  # Now includes cash
            'overall_roi': overall_roi,
            'absolute_gain': absolute_gain,
            'avg_drawdown': avg_drawdown,
            'worst_drawdown_ticker': worst_drawdown_ticker,
            'worst_drawdown_value': worst_drawdown_value,
            'best_drawdown_ticker': best_drawdown_ticker,
            'best_drawdown_value': best_drawdown_value,
            'significant_drawdown_count': significant_drawdown_count,
            'current_cash_balance': current_cash_balance
        }
    
    def calculate_portfolio_volatility(self, portfolio_totals: pd.DataFrame) -> dict:
        """Calculate portfolio volatility metrics."""
        # Calculate daily returns
        portfolio_totals = portfolio_totals.sort_values("Date").copy()
        portfolio_totals["Daily Return (%)"] = portfolio_totals["Total Equity"].pct_change() * 100
        
        # Calculate volatility metrics
        daily_volatility = portfolio_totals["Daily Return (%)"].std()
        annualized_volatility = daily_volatility * np.sqrt(252)  # Annualized (252 trading days)
        
        # Calculate Sharpe ratio (assuming risk-free rate of 0 for simplicity)
        avg_daily_return = portfolio_totals["Daily Return (%)"].mean()
        sharpe_ratio = (avg_daily_return / daily_volatility) * np.sqrt(252) if daily_volatility > 0 else 0
        
        return {
            'daily_volatility': daily_volatility,
            'annualized_volatility': annualized_volatility,
            'sharpe_ratio': sharpe_ratio,
            'avg_daily_return': avg_daily_return
        }
    
    def calculate_sortino_ratio(self, returns: pd.Series, risk_free_rate: float = 0) -> float:
        """Calculate the Sortino ratio."""
        # Calculate excess returns
        excess_returns = returns - risk_free_rate
        
        # Calculate downside deviation (standard deviation of negative returns)
        negative_returns = returns[returns < risk_free_rate]
        if len(negative_returns) > 0:
            downside_deviation = np.sqrt(np.mean((negative_returns - risk_free_rate) ** 2))
        else:
            downside_deviation = 1e-10  # Avoid division by zero
        
        # Calculate Sortino ratio
        sortino_ratio = np.mean(excess_returns) / downside_deviation if downside_deviation > 0 else 0
        
        return sortino_ratio
    
    def calculate_advanced_risk_metrics(self, portfolio_totals: pd.DataFrame) -> dict:
        """Calculate advanced risk metrics including Sortino ratio."""
        # Calculate daily returns
        portfolio_totals = portfolio_totals.sort_values("Date").copy()
        portfolio_totals["Daily Return (%)"] = portfolio_totals["Total Equity"].pct_change() * 100
        
        # Remove NaN values
        returns = portfolio_totals["Daily Return (%)"].dropna()
        
        # Calculate Sortino ratio
        sortino_ratio = self.calculate_sortino_ratio(returns)
        
        # Calculate maximum consecutive wins and losses
        consecutive_wins = 0
        consecutive_losses = 0
        max_consecutive_wins = 0
        max_consecutive_losses = 0
        
        for return_val in returns:
            if return_val > 0:
                consecutive_wins += 1
                consecutive_losses = 0
                max_consecutive_wins = max(max_consecutive_wins, consecutive_wins)
            elif return_val < 0:
                consecutive_losses += 1
                consecutive_wins = 0
                max_consecutive_losses = max(max_consecutive_losses, consecutive_losses)
            else:
                consecutive_wins = 0
                consecutive_losses = 0
        
        return {
            'sortino_ratio': sortino_ratio,
            'max_consecutive_wins': max_consecutive_wins,
            'max_consecutive_losses': max_consecutive_losses
        }