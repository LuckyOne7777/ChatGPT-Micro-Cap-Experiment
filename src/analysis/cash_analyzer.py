"""
Cash analysis for the ChatGPT Micro Cap Experiment.
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple


class CashAnalyzer:
    """Analyzer for cash position calculations."""
    
    def __init__(self, portfolio_loader):
        self.portfolio_loader = portfolio_loader
    
    def calculate_daily_cash_with_actual_balance(self, trade_df, initial_cash=100.0):
        """
        Calculate cash position for each day based on trade log data using actual initial cash.
        
        For each trade:
        - BUY: Cash decreases by (Shares Bought * Buy Price)
        - SELL: Cash increases by (Shares Sold * Sell Price)
        
        Args:
            trade_df: DataFrame with trade log data
            initial_cash: Initial cash balance (default $100.0)
            
        Returns:
            dict: Daily cash balances
        """
        # Sort by date
        trade_df = trade_df.sort_values('Date')
        
        # Initialize cash balance with initial cash
        daily_cash_balances = {}
        current_cash = initial_cash
        
        # Process each trade
        for _, row in trade_df.iterrows():
            date = row['Date'].date()
            
            # Process buys
            if pd.notna(row['Shares Bought']) and pd.notna(row['Buy Price']) and row['Shares Bought'] > 0:
                amount = row['Shares Bought'] * row['Buy Price']
                current_cash -= amount
            
            # Process sells
            if pd.notna(row['Shares Sold']) and pd.notna(row['Sell Price']) and row['Shares Sold'] > 0:
                amount = row['Shares Sold'] * row['Sell Price']
                current_cash += amount
            
            # Update daily cash balances
            daily_cash_balances[date] = current_cash
        
        return daily_cash_balances
    
    def get_portfolio_values_by_date(self, portfolio_df, dates):
        """
        Get stock market value and total portfolio value for each date.
        
        Args:
            portfolio_df: DataFrame with portfolio data
            dates: List of dates to get values for
            
        Returns:
            dict: Portfolio values by date
        """
        if portfolio_df is None:
            return {}
        
        portfolio_values = {}
        
        # Get TOTAL entries
        total_entries = portfolio_df[portfolio_df['Ticker'] == 'TOTAL']
        
        for date in dates:
            # Find the entry for this date
            date_entries = total_entries[total_entries['Date'].dt.date == date]
            if len(date_entries) > 0:
                entry = date_entries.iloc[0]
                stock_value = float(entry['Total Value']) if pd.notna(entry['Total Value']) else 0.0
                cash_balance = float(entry['Cash Balance']) if pd.notna(entry['Cash Balance']) else 0.0
                total_equity = float(entry['Total Equity']) if pd.notna(entry['Total Equity']) else 0.0
                portfolio_values[date] = {
                    'stock_value': stock_value,
                    'cash_balance': cash_balance,
                    'total_value': total_equity
                }
            else:
                portfolio_values[date] = {
                    'stock_value': 0.0,
                    'cash_balance': 0.0,
                    'total_value': 0.0
                }
        
        return portfolio_values
    
    def get_stock_values_by_date(self, portfolio_df, dates):
        """
        Get individual stock market values for each date.
        
        Args:
            portfolio_df: DataFrame with portfolio data
            dates: List of dates to get values for
            
        Returns:
            dict: Stock values by date
        """
        if portfolio_df is None:
            return {}
        
        stock_values = {}
        
        # Filter out TOTAL entries to work only with individual stocks
        stock_entries = portfolio_df[portfolio_df['Ticker'] != 'TOTAL']
        
        for date in dates:
            # Find the entries for this date
            date_entries = stock_entries[stock_entries['Date'].dt.date == date]
            if len(date_entries) > 0:
                # Create a dictionary of ticker -> market value for this date
                date_stock_values = {}
                for _, entry in date_entries.iterrows():
                    ticker = entry['Ticker']
                    market_value = float(entry['Total Value']) if pd.notna(entry['Total Value']) else 0.0
                    if market_value > 0:  # Only include stocks with positive value
                        date_stock_values[ticker] = market_value
                stock_values[date] = date_stock_values
            else:
                stock_values[date] = {}
        
        return stock_values