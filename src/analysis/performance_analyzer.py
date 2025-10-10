"""
Performance analysis for the ChatGPT Micro Cap Experiment.
"""

import pandas as pd
import numpy as np


class PerformanceAnalyzer:
    """Analyzer for performance metrics calculations."""
    
    def calculate_daily_performance(self, portfolio_totals: pd.DataFrame) -> pd.DataFrame:
        """Calculate daily performance metrics."""
        portfolio_totals = portfolio_totals.sort_values("Date").copy()
        portfolio_totals["Daily Return (%)"] = portfolio_totals["Total Equity"].pct_change() * 100
        portfolio_totals["Cumulative Return (%)"] = (portfolio_totals["Total Equity"] / portfolio_totals["Total Equity"].iloc[0] - 1) * 100
        return portfolio_totals
    
    def calculate_roi_over_time(self, df: pd.DataFrame, trade_df: pd.DataFrame = None) -> pd.DataFrame:
        """Calculate ROI over time for each stock, with separate lines for separate trades."""
        # Get unique tickers
        tickers = df["Ticker"].unique()
        
        # Create a DataFrame to store ROI over time
        roi_data = []
        
        # For each ticker, calculate ROI at each time point
        for ticker in tickers:
            stock_data = df[df["Ticker"] == ticker].sort_values("Date")
            if len(stock_data) > 0:
                # If we have trade data, identify separate trades
                if trade_df is not None:
                    ticker_trades = trade_df[trade_df["Ticker"] == ticker].sort_values("Date")
                    if len(ticker_trades) > 0:
                        # Identify buy transactions to separate trades
                        buy_trades = ticker_trades[ticker_trades["Shares Bought"] > 0]
                        if len(buy_trades) > 1:
                            # Multiple separate trades, need to separate them
                            trade_dates = buy_trades["Date"].tolist()
                            # Add the first date of the stock data as the start
                            trade_dates.insert(0, stock_data["Date"].min())
                            # Add a date after the last trade to capture the final data points
                            trade_dates.append(stock_data["Date"].max() + pd.Timedelta(days=1))
                            
                            # For each trade period, calculate ROI separately
                            for i in range(len(trade_dates) - 1):
                                start_date = trade_dates[i]
                                end_date = trade_dates[i + 1]
                                period_data = stock_data[
                                    (stock_data["Date"] >= start_date) & (stock_data["Date"] < end_date)
                                ]
                                
                                if len(period_data) > 0:
                                    # Use the first entry's cost basis for this period
                                    period_cost_basis = period_data.iloc[0]["Cost Basis"]
                                    for _, row in period_data.iterrows():
                                        current_value = row["Total Value"]
                                        if period_cost_basis > 0:
                                            roi_pct = ((current_value / period_cost_basis) - 1) * 100
                                            roi_data.append({
                                                "Ticker": ticker,
                                                "Date": row["Date"],
                                                "ROI (%)": roi_pct,
                                                "TradeGroup": i  # To identify separate trades in plotting
                                            })
                        else:
                            # Single trade or no clear separate trades
                            for _, row in stock_data.iterrows():
                                cost_basis = row["Cost Basis"]
                                current_value = row["Total Value"]
                                if cost_basis > 0:
                                    roi_pct = ((current_value / cost_basis) - 1) * 100
                                    roi_data.append({
                                        "Ticker": ticker,
                                        "Date": row["Date"],
                                        "ROI (%)": roi_pct,
                                        "TradeGroup": 0
                                    })
                    else:
                        # No trade data for this ticker, use original method
                        for _, row in stock_data.iterrows():
                            cost_basis = row["Cost Basis"]
                            current_value = row["Total Value"]
                            if cost_basis > 0:
                                roi_pct = ((current_value / cost_basis) - 1) * 100
                                roi_data.append({
                                    "Ticker": ticker,
                                    "Date": row["Date"],
                                    "ROI (%)": roi_pct,
                                    "TradeGroup": 0
                                })
                else:
                    # No trade data provided, use original method
                    for _, row in stock_data.iterrows():
                        cost_basis = row["Cost Basis"]
                        current_value = row["Total Value"]
                        if cost_basis > 0:
                            roi_pct = ((current_value / cost_basis) - 1) * 100
                            roi_data.append({
                                "Ticker": ticker,
                                "Date": row["Date"],
                                "ROI (%)": roi_pct,
                                "TradeGroup": 0
                            })
        
        return pd.DataFrame(roi_data)
    
    def calculate_win_loss_metrics(self, roi_df: pd.DataFrame) -> dict:
        """Calculate win/loss metrics."""
        # Check if ROI (%) column exists
        if "ROI (%)" not in roi_df.columns:
            return {
                'total_positions': 0,
                'winning_positions': 0,
                'losing_positions': 0,
                'breakeven_positions': 0,
                'win_rate': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'best_position': None,
                'worst_position': None
            }
        
        total_positions = len(roi_df)
        winning_positions = len(roi_df[roi_df["ROI (%)"] > 0])
        losing_positions = len(roi_df[roi_df["ROI (%)"] < 0])
        breakeven_positions = len(roi_df[roi_df["ROI (%)"] == 0])
        
        win_rate = (winning_positions / total_positions) * 100 if total_positions > 0 else 0
        
        avg_win = (roi_df[roi_df["ROI (%)"] > 0]["ROI (%)"].mean() if winning_positions > 0 else 0)
        avg_loss = (roi_df[roi_df["ROI (%)"] < 0]["ROI (%)"].mean() if losing_positions > 0 else 0)
        
        best_position = roi_df.loc[roi_df["ROI (%)"].idxmax()] if total_positions > 0 and not roi_df.empty else None
        worst_position = roi_df.loc[roi_df["ROI (%)"].idxmin()] if total_positions > 0 and not roi_df.empty else None
        
        return {
            'total_positions': total_positions,
            'winning_positions': winning_positions,
            'losing_positions': losing_positions,
            'breakeven_positions': breakeven_positions,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'best_position': best_position,
            'worst_position': worst_position
        }