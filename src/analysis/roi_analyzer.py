"""
ROI analysis for the ChatGPT Micro Cap Experiment.
"""

import pandas as pd
import numpy as np


class ROIAnalyzer:
    """Analyzer for ROI calculations."""
    
    def __init__(self, portfolio_loader):
        self.portfolio_loader = portfolio_loader
    
    def calculate_stock_roi(self, portfolio_df: pd.DataFrame) -> pd.DataFrame:
        """Calculate ROI for each stock based on cost basis and current value."""
        # Get currently held stocks using the new method
        current_holdings = self.portfolio_loader.get_currently_held_stocks(portfolio_df)
        
        # For each current holding, we need to find its current cost basis and value
        roi_data = []
        
        for _, current_row in current_holdings.iterrows():
            ticker = current_row["Ticker"]
            shares = current_row["Shares"]
            cost_basis = current_row["Cost Basis"]
            current_value = current_row["Total Value"]
            
            if cost_basis > 0:
                # Absolute Return = Realized Proceeds ($) + Market Value ($) - Cost Basis ($)
                # For currently held stocks, Realized Proceeds ($) = 0
                realized_value = 0.0
                unrealized_value = current_value
                total_cost = cost_basis
                net_gain_loss = realized_value + unrealized_value - total_cost
                
                # ROI = Net Gain/Loss ($) ÷ Cost Basis ($)
                roi_pct = (net_gain_loss / total_cost) * 100
                
                roi_data.append({
                    "Ticker": ticker,
                    "Shares": shares,
                    "Cost Basis ($)": total_cost,
                    "Market Value ($)": unrealized_value,
                    "Realized Proceeds ($)": realized_value,
                    "ROI (%)": roi_pct,
                    "Net Gain/Loss ($)": net_gain_loss
                })
        
        return pd.DataFrame(roi_data).sort_values("ROI (%)", ascending=False)
    
    def calculate_all_stocks_roi(self, portfolio_df: pd.DataFrame, trade_df: pd.DataFrame = None) -> pd.DataFrame:
        """Calculate ROI for all stocks ever purchased."""
        # Group by ticker and calculate total shares and cost basis from all transactions
        roi_data = []
        
        # Get the latest date in the portfolio
        latest_date = portfolio_df["Date"].max()
        
        for ticker in portfolio_df["Ticker"].unique():
            stock_data = portfolio_df[portfolio_df["Ticker"] == ticker].sort_values("Date")
            if len(stock_data) > 0:
                # Get the latest entry for current value
                last_entry = stock_data.iloc[-1]
                current_value = last_entry["Total Value"]
                current_shares = last_entry["Shares"]
                
                # For "All Stocks Ever Purchased", we want to show:
                # 1. Total shares ever bought (sum of all buys)
                # 2. Total cost of all shares ever bought
                # 3. Current value of any remaining shares
                # 4. Total proceeds from all sales
                
                if trade_df is not None:
                    # Calculate from trade data if available
                    ticker_trades = trade_df[trade_df["Ticker"] == ticker]
                    if len(ticker_trades) > 0:
                        # Sum all shares bought
                        total_shares_bought = ticker_trades["Shares Bought"].sum()
                        # Sum all cost basis for buys
                        total_cost_basis = ticker_trades[ticker_trades["Shares Bought"] > 0]["Cost Basis"].sum()
                        # Sum all proceeds from sells (Shares Sold * Sell Price)
                        sell_trades = ticker_trades[ticker_trades["Shares Sold"] > 0].copy()
                        if len(sell_trades) > 0:
                            sell_trades["Sell Amount"] = sell_trades["Shares Sold"] * sell_trades["Sell Price"]
                            total_proceeds = sell_trades["Sell Amount"].sum()
                        else:
                            total_proceeds = 0.0
                        
                        # Use calculated values
                        shares = total_shares_bought
                        cost_basis = total_cost_basis
                        proceeds = total_proceeds
                    else:
                        # Fallback to portfolio data approach
                        first_entry = stock_data.iloc[0]
                        shares = first_entry["Shares"]
                        cost_basis = first_entry["Cost Basis"]
                        proceeds = 0.0
                else:
                    # Fallback to portfolio data approach
                    first_entry = stock_data.iloc[0]
                    shares = first_entry["Shares"]
                    cost_basis = first_entry["Cost Basis"]
                    proceeds = 0.0
                
                # Check if the stock is currently held using trade data
                # Sum all shares bought and sold to determine current position
                if trade_df is not None and len(ticker_trades) > 0:
                    total_shares_bought = ticker_trades["Shares Bought"].sum()
                    total_shares_sold = ticker_trades["Shares Sold"].sum()
                    current_shares = total_shares_bought - total_shares_sold
                else:
                    # Fallback to portfolio data approach
                    latest_stock_data = stock_data[stock_data["Date"] == latest_date]
                    if len(latest_stock_data) > 0:
                        latest_entry = latest_stock_data.iloc[-1]
                        current_shares = latest_entry["Shares"]
                    else:
                        current_shares = 0
                
                # Handle cases where we might have sold all shares
                # NEW LOGIC: If we have no buy trades but do have sell trades, 
                # fall back to portfolio data for cost basis
                if trade_df is not None and len(ticker_trades) > 0:
                    buy_trades = ticker_trades[ticker_trades["Shares Bought"] > 0]
                    sell_trades = ticker_trades[ticker_trades["Shares Sold"] > 0]
                    
                    if len(buy_trades) == 0 and len(sell_trades) > 0 and cost_basis == 0:
                        # No buy trades but have sell trades - use portfolio data for cost basis
                        first_entry = stock_data.iloc[0]
                        cost_basis = first_entry["Cost Basis"]
                        shares = first_entry["Shares"]
                
                if current_shares > 0 and cost_basis > 0:
                    # Currently held stocks - use actual current value
                    realized_value = proceeds
                    unrealized_value = current_value
                    total_cost = cost_basis
                    # Absolute Return = Realized Value + Unrealized Value - Total Cost
                    absolute_return = realized_value + unrealized_value - total_cost
                    # ROI = Absolute Return ÷ Total Cost
                    roi_pct = (absolute_return / total_cost) * 100
                    
                    roi_data.append({
                        "Ticker": ticker,
                        "Shares": shares,
                        "Cost Basis ($)": total_cost,
                        "Market Value ($)": unrealized_value,
                        "Realized Proceeds ($)": realized_value,
                        "ROI (%)": roi_pct,
                        "Net Gain/Loss ($)": absolute_return
                    })
                elif cost_basis > 0:  # Sold all shares
                    # For sold positions, current value should be 0
                    current_value = 0.0
                    realized_value = proceeds
                    unrealized_value = current_value
                    total_cost = cost_basis
                    # Absolute Return = Realized Value + Unrealized Value - Total Cost
                    absolute_return = realized_value + unrealized_value - total_cost
                    # ROI = Absolute Return ÷ Total Cost
                    roi_pct = (absolute_return / total_cost) * 100
                    
                    roi_data.append({
                        "Ticker": ticker,
                        "Shares": shares,
                        "Cost Basis ($)": total_cost,
                        "Market Value ($)": unrealized_value,
                        "Realized Proceeds ($)": realized_value,
                        "ROI (%)": roi_pct,
                        "Net Gain/Loss ($)": absolute_return
                    })
        
        return pd.DataFrame(roi_data).sort_values("ROI (%)", ascending=False)
    
    def calculate_current_portfolio_roi(self, portfolio_df: pd.DataFrame) -> pd.DataFrame:
        """Calculate ROI for currently held stocks only."""
        # Use the get_currently_held_stocks method from portfolio_loader
        current_holdings = self.portfolio_loader.get_currently_held_stocks(portfolio_df)
        # For each current holding, we need to find its current cost basis
        roi_data = []
        
        for _, current_row in current_holdings.iterrows():
            ticker = current_row["Ticker"]
            shares = current_row["Shares"]
            current_cost_basis = current_row["Cost Basis"]  # This is the adjusted cost basis
            current_value = current_row["Total Value"]
            
            # Handle cases where we might have sold all shares
            if shares > 0 and current_cost_basis > 0:
                # Absolute Return = Realized Value + Unrealized Value - Total Cost
                # For currently held stocks, Realized Value = 0
                realized_value = 0.0
                unrealized_value = current_value
                total_cost = current_cost_basis
                absolute_return = realized_value + unrealized_value - total_cost
                
                # ROI = Absolute Return ÷ Total Cost
                roi_pct = (absolute_return / total_cost) * 100
                
                roi_data.append({
                    "Ticker": ticker,
                    "Shares": shares,
                    "Cost Basis ($)": total_cost,
                    "Market Value ($)": unrealized_value,
                    "Realized Proceeds ($)": realized_value,
                    "ROI (%)": roi_pct,
                    "Net Gain/Loss ($)": absolute_return
                })
        
        return pd.DataFrame(roi_data).sort_values("ROI (%)", ascending=False)
    
    def calculate_separate_portfolio_roi(self, portfolio_df: pd.DataFrame, initial_cash: float = 100.0) -> dict:
        """
        Calculate separate portfolio ROI as adjusted_total_value / initial_cash.
        
        Args:
            portfolio_df: DataFrame with portfolio data
            initial_cash: Initial cash investment (default $100.0)
            
        Returns:
            dict: Separate ROI metrics
        """
        # Get the latest portfolio data (most recent date)
        latest_date = portfolio_df["Date"].max()
        latest_data = portfolio_df[portfolio_df["Date"] == latest_date]
        
        # Find the TOTAL row which contains portfolio summary
        total_row = latest_data[latest_data["Ticker"] == "TOTAL"]
        
        if len(total_row) > 0 and initial_cash > 0:
            total_equity = total_row.iloc[0]["Total Equity"]
            adjusted_total_value = float(total_equity) if pd.notna(total_equity) else 0.0
            
            # Calculate separate ROI
            separate_roi = (adjusted_total_value / initial_cash) - 1.0
            separate_roi_pct = separate_roi * 100
            
            return {
                "adjusted_total_value": adjusted_total_value,
                "initial_cash": initial_cash,
                "separate_roi": separate_roi,
                "separate_roi_pct": separate_roi_pct
            }
        
        return {
            "adjusted_total_value": 0.0,
            "initial_cash": initial_cash,
            "separate_roi": 0.0,
            "separate_roi_pct": 0.0
        }