"""
Drawdown analysis for the ChatGPT Micro Cap Experiment.
"""

import pandas as pd
import numpy as np


class DrawdownAnalyzer:
    """Analyzer for drawdown calculations."""
    
    def calculate_drawdown_over_time(self, stock_data: pd.DataFrame) -> pd.DataFrame:
        """Calculate drawdown over time for a single stock."""
        # Sort by date
        stock_data = stock_data.sort_values("Date").copy()
        
        # Calculate peak value up to each point
        stock_data["Peak Value"] = stock_data["Total Value"].cummax()
        
        # Calculate drawdown
        stock_data["Drawdown ($)"] = stock_data["Total Value"] - stock_data["Peak Value"]
        stock_data["Drawdown (%)"] = (stock_data["Drawdown ($)"] / stock_data["Peak Value"]) * 100
        
        return stock_data
    
    def calculate_all_drawdowns(self, portfolio_df: pd.DataFrame) -> dict:
        """Calculate maximum drawdown for each stock in the portfolio."""
        drawdown_data = {}
        
        # Check if portfolio_df is empty
        if portfolio_df.empty:
            return drawdown_data
        
        # Get unique tickers
        tickers = portfolio_df["Ticker"].unique()
        
        # For each ticker, calculate maximum drawdown
        for ticker in tickers:
            stock_data = portfolio_df[portfolio_df["Ticker"] == ticker].sort_values("Date")
            
            if len(stock_data) > 0:
                # Calculate drawdown over time
                stock_with_drawdown = self.calculate_drawdown_over_time(stock_data)
                
                # Calculate maximum drawdown
                if "Drawdown (%)" in stock_with_drawdown.columns and "Drawdown ($)" in stock_with_drawdown.columns:
                    max_drawdown_pct = stock_with_drawdown["Drawdown (%)"].min()  # Min because drawdown is negative
                    max_drawdown_dollar = stock_with_drawdown["Drawdown ($)"].min()  # Min because drawdown is negative
                    
                    drawdown_data[ticker] = {
                        "Max Drawdown (%)": max_drawdown_pct,
                        "Max Drawdown ($)": max_drawdown_dollar
                    }
        
        return drawdown_data