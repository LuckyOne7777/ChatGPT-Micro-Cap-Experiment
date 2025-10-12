"""
Helper functions for the ChatGPT Micro Cap Experiment.
"""

import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta


def download_sp500(start_date: pd.Timestamp, end_date: pd.Timestamp) -> pd.DataFrame:
    """Download S&P 500 prices and normalise to a $100 baseline (at 2025-06-27 close=6173.07)."""
    try:
        sp500 = yf.download("^SPX", start=start_date, end=end_date + pd.Timedelta(days=1),
                            progress=False, auto_adjust=True)
        sp500 = sp500.reset_index()
        if isinstance(sp500.columns, pd.MultiIndex):
            sp500.columns = sp500.columns.get_level_values(0)

        spx_27_price = 6173.07  # 2025-06-27 close (baseline)
        scaling_factor = 100.0 / spx_27_price
        sp500["SPX Value ($100 Invested)"] = sp500["Close"] * scaling_factor
        return sp500[["Date", "SPX Value ($100 Invested)"]]
    except Exception as e:
        print(f"Warning: Could not download S&P 500 data: {e}")
        # Create a dummy dataframe with the same start and end values
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        values = [100.0] * len(dates)  # Flat line at $100
        return pd.DataFrame({"Date": dates, "SPX Value ($100 Invested)": values})