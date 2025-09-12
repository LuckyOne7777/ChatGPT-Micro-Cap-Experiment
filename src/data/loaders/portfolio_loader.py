"""
Portfolio data loader for the ChatGPT Micro Cap Experiment.
"""

import pandas as pd
import os
from pathlib import Path
from datetime import datetime


class PortfolioLoader:
    """Loader for portfolio data."""
    
    def __init__(self, data_dir: str = "Scripts and CSV Files"):
        self.data_dir = data_dir
        self.portfolio_csv = os.path.join(data_dir, "chatgpt_portfolio_update.csv")
    
    def load_portfolio_data(self, date_filter: str = None) -> pd.DataFrame:
        """Load all portfolio data (excluding TOTAL rows)."""
        df = pd.read_csv(self.portfolio_csv)
        # Filter out TOTAL rows to work only with individual stocks
        df = df[df["Ticker"] != "TOTAL"].copy()
        # Convert Date column to datetime
        df["Date"] = pd.to_datetime(df["Date"])
        
        # Filter by report date if specified
        if date_filter:
            report_datetime = pd.to_datetime(date_filter)
            df = df[df["Date"] <= report_datetime]
        
        return df
    
    def load_portfolio_totals(self, date_filter: str = None) -> pd.DataFrame:
        """Load portfolio equity history including a baseline row."""
        chatgpt_df = pd.read_csv(self.portfolio_csv)
        chatgpt_df = chatgpt_df[chatgpt_df["Ticker"] == "TOTAL"].copy()
        chatgpt_df["Date"] = pd.to_datetime(chatgpt_df["Date"])
        chatgpt_df["Total Equity"] = pd.to_numeric(
            chatgpt_df["Total Equity"], errors="coerce"
        )
        
        # Filter by report date if specified
        if date_filter:
            report_datetime = pd.to_datetime(date_filter)
            chatgpt_df = chatgpt_df[chatgpt_df["Date"] <= report_datetime]
        baseline_date = pd.Timestamp("2025-06-27")
        baseline_equity = 100.0
        baseline_row = pd.DataFrame({"Date": [baseline_date], "Total Equity": [baseline_equity]})

        out = pd.concat([baseline_row, chatgpt_df], ignore_index=True).sort_values("Date")
        out = out.drop_duplicates(subset=["Date"], keep="last").reset_index(drop=True)
        return out
    
    def get_currently_held_stocks(self, portfolio_df: pd.DataFrame) -> pd.DataFrame:
        """Get currently held stocks by finding entries on the last date and filtering for positive shares."""
        # Find the last date in the portfolio
        last_date = portfolio_df["Date"].max()
        # Filter for entries on that date
        last_date_entries = portfolio_df[portfolio_df["Date"] == last_date]
        # Filter for stocks with positive shares
        current_holdings = last_date_entries[last_date_entries["Shares"] > 0]
        return current_holdings