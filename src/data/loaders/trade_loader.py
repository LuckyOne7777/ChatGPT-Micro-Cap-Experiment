"""
Trade log data loader for the ChatGPT Micro Cap Experiment.
"""

import pandas as pd
import os


class TradeLoader:
    """Loader for trade log data."""
    
    def __init__(self, data_dir: str = "Scripts and CSV Files"):
        self.data_dir = data_dir
        self.trade_log_csv = os.path.join(data_dir, "chatgpt_trade_log.csv")
    
    def load_trade_data(self, date_filter: str = None) -> pd.DataFrame:
        """Load trade log data."""
        df = pd.read_csv(self.trade_log_csv)
        # Convert Date column to datetime
        df["Date"] = pd.to_datetime(df["Date"])
        
        # Filter by report date if specified
        if date_filter:
            report_datetime = pd.to_datetime(date_filter)
            df = df[df["Date"] <= report_datetime]
        
        return df