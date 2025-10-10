"""
Plot generation for the ChatGPT Micro Cap Experiment.
"""

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import yfinance as yf
from pathlib import Path
import os
from datetime import datetime, timedelta


class PlotGenerator:
    """Generator for all plots in the financial report."""
    
    def __init__(self, reports_dir: Path):
        self.reports_dir = reports_dir
    
    def save_plot(self, fig, filename: str) -> str:
        """Save plot and return the relative path."""
        filepath = self.reports_dir / filename
        fig.savefig(filepath, dpi=300, bbox_inches="tight")
        return str(filepath.relative_to("Reports"))
    
    def generate_performance_comparison_plot(self, chatgpt_totals: pd.DataFrame, sp500: pd.DataFrame) -> str:
        """Generate and save the performance comparison plot."""
        # metrics
        largest_start, largest_end, largest_gain = self.find_largest_gain(chatgpt_totals)
        dd_date, dd_value, dd_pct = self.compute_drawdown(chatgpt_totals)

        # plotting
        plt.figure(figsize=(12, 8))
        plt.style.use("seaborn-v0_8-whitegrid")

        plt.plot(
            chatgpt_totals["Date"],
            chatgpt_totals["Total Equity"],
            label="ChatGPT ($100 Invested)",
            marker="o",
            color="blue",
            linewidth=2,
        )
        plt.plot(
            sp500["Date"],
            sp500["SPX Value ($100 Invested)"],
            label="S&P 500 ($100 Invested)",
            marker="o",
            color="orange",
            linestyle="--",
            linewidth=2,
        )

        # annotate largest gain
        largest_peak_value = float(
            chatgpt_totals.loc[chatgpt_totals["Date"] == largest_end, "Total Equity"].iloc[0]
        )
        plt.text(
            largest_end,
            largest_peak_value + 0.5,
            f"+{largest_gain:.1f}% largest gain",
            color="green",
            fontsize=9,
        )

        # annotate final P/Ls
        final_date = chatgpt_totals["Date"].iloc[-1]
        final_chatgpt = float(chatgpt_totals["Total Equity"].iloc[-1])
        final_spx = float(sp500["SPX Value ($100 Invested)"].iloc[-1])
        plt.text(final_date, final_chatgpt + 0.5, f"+{final_chatgpt - 100.0:.1f}%", color="blue", fontsize=9)
        plt.text(final_date, final_spx + 1.0, f"+{final_spx - 100.0:.1f}%", color="orange", fontsize=9)

        # annotate max drawdown
        plt.text(
            dd_date + pd.Timedelta(days=1),
            dd_value - 1.0,
            f"{dd_pct:.1f}% max drawdown",
            color="red",
            fontsize=9,
        )

        plt.title("ChatGPT's Micro Cap Portfolio vs. S&P 500", fontsize=16, fontweight='bold')
        plt.xlabel("Date", fontsize=12)
        plt.ylabel("Value of $100 Investment", fontsize=12)
        plt.xticks(rotation=45, ha='right')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        # Save plot
        filepath = self.save_plot(plt, "performance_comparison.png")
        plt.close()
        return filepath
    
    def find_largest_gain(self, df: pd.DataFrame) -> tuple[pd.Timestamp, pd.Timestamp, float]:
        """
        Largest rise from a local minimum to the subsequent peak.
        Returns (start_date, end_date, gain_pct).
        """
        df = df.sort_values("Date")
        min_val = float(df["Total Equity"].iloc[0])
        min_date = pd.Timestamp(df["Date"].iloc[0])
        peak_val = min_val
        peak_date = min_date
        best_gain = 0.0
        best_start = min_date
        best_end = peak_date

        # iterate rows 1..end
        for date, val in df[["Date", "Total Equity"]].iloc[1:].itertuples(index=False):
            val = float(val)
            date = pd.Timestamp(date)

            # extend peak while rising
            if val > peak_val:
                peak_val = val
                peak_date = date
                continue

            # fall → close previous run
            if val < peak_val:
                gain = (peak_val - min_val) / min_val * 100.0
                if gain > best_gain:
                    best_gain = gain
                    best_start = min_date
                    best_end = peak_date
                # reset min/peak at this valley
                min_val = val
                min_date = date
                peak_val = val
                peak_date = date

        # final run (if last segment ends on a rise)
        gain = (peak_val - min_val) / min_val * 100.0
        if gain > best_gain:
            best_gain = gain
            best_start = min_date
            best_end = peak_date

        return best_start, best_end, best_gain
    
    def compute_drawdown(self, df: pd.DataFrame) -> tuple[pd.Timestamp, float, float]:
        """
        Compute running max and drawdown (%). Return (dd_date, dd_value, dd_pct).
        """
        df = df.sort_values("Date").copy()
        df["Running Max"] = df["Total Equity"].cummax()
        df["Drawdown %"] = (df["Total Equity"] / df["Running Max"] - 1.0) * 100.0
        row = df.loc[df["Drawdown %"].idxmin()]
        return pd.Timestamp(row["Date"]), float(row["Total Equity"]), float(row["Drawdown %"])
    
    def generate_roi_bars_plot(self, roi_df: pd.DataFrame) -> str:
        """Generate and save the ROI bars plot."""
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Create bar chart
        colors = ['green' if roi >= 0 else 'red' for roi in roi_df["ROI (%)"]]
        bars = ax.bar(range(len(roi_df)), roi_df["ROI (%)"], color=colors)
        
        # Customize the chart
        ax.set_title("ROI by Stock in Portfolio", fontsize=16, fontweight='bold')
        ax.set_xlabel("Stock Ticker", fontsize=12)
        ax.set_ylabel("ROI (%)", fontsize=12)
        ax.set_xticks(range(len(roi_df)))
        ax.set_xticklabels(roi_df["Ticker"], rotation=45, ha='right')
        
        # Add value labels on bars
        for i, (bar, roi) in enumerate(zip(bars, roi_df["ROI (%)"])):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + (1 if height >= 0 else -3),
                    f'{roi:.1f}%', ha='center', va='bottom' if height >= 0 else 'top', fontsize=9)
        
        # Add grid
        ax.grid(True, axis='y', alpha=0.3)
        ax.axhline(y=0, color='black', linewidth=0.5)
        
        plt.tight_layout()
        
        # Save plot
        filepath = self.save_plot(fig, "roi_by_stock.png")
        plt.close()
        return filepath
    
    def generate_portfolio_composition_plot(self, roi_df: pd.DataFrame) -> str:
        """Generate and save the portfolio composition pie chart."""
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Check if required columns exist
        if "Market Value ($)" not in roi_df.columns or "Ticker" not in roi_df.columns:
            ax.text(0.5, 0.5, "No data available", ha='center', va='center', transform=ax.transAxes)
            ax.set_title("Portfolio Composition by Market Value", fontsize=16, fontweight='bold')
            plt.tight_layout()
            filepath = self.save_plot(fig, "portfolio_composition.png")
            plt.close()
            return filepath
        
        # Only include stocks with positive value
        positive_value = roi_df[roi_df["Market Value ($)"] > 0]
        
        if len(positive_value) > 0:
            ax.pie(positive_value["Market Value ($)"], labels=positive_value["Ticker"], 
                   autopct='%1.1f%%', startangle=90, textprops={'fontsize': 10})
            ax.set_title("Portfolio Composition by Market Value", fontsize=16, fontweight='bold')
        else:
            ax.text(0.5, 0.5, "No current holdings", ha='center', va='center', transform=ax.transAxes)
        
        plt.tight_layout()
        
        # Save plot
        filepath = self.save_plot(fig, "portfolio_composition.png")
        plt.close()
        return filepath
    
    def generate_roi_drawdown_dashboard(self, roi_df: pd.DataFrame, drawdown_data: dict, all_stocks_roi: pd.DataFrame = None) -> str:
        """Create a comprehensive dashboard showing both ROI and drawdown metrics."""
        # Create a figure with subplots
        fig = plt.figure(figsize=(20, 15))
        
        # Check if we have data
        if roi_df.empty or not drawdown_data:
            # Create empty plots with messages
            for i in range(1, 5):
                ax = plt.subplot(2, 3, i)
                ax.text(0.5, 0.5, "No data available", ha='center', va='center', transform=ax.transAxes)
                ax.set_title(f"Chart {i}", fontsize=14, fontweight='bold')
        else:
            # Check if required columns exist before proceeding
            required_columns = ["Ticker", "ROI (%)"]
            if not all(col in roi_df.columns for col in required_columns):
                # Create empty plots with messages
                for i in range(1, 5):
                    ax = plt.subplot(2, 3, i)
                    ax.text(0.5, 0.5, "No data available", ha='center', va='center', transform=ax.transAxes)
                    ax.set_title(f"Chart {i}", fontsize=14, fontweight='bold')
            else:
                # Merge ROI and drawdown data
                combined_data = all_stocks_roi.copy()
                
                # Check if Ticker column exists before mapping
                if "Ticker" in combined_data.columns:
                    combined_data["Max Drawdown (%)"] = combined_data["Ticker"].map(
                        {ticker: data["Max Drawdown (%)"] for ticker, data in drawdown_data.items()}
                    )
                    combined_data["Max Drawdown ($)"] = combined_data["Ticker"].map(
                        {ticker: data["Max Drawdown ($)"] for ticker, data in drawdown_data.items()}
                    )
                
                # Calculate ROI/Drawdown ratio (return per unit of drawdown risk)
                # Check if required columns exist before calculation
                if "ROI (%)" in combined_data.columns and "Max Drawdown (%)" in combined_data.columns:
                    # Avoid division by zero
                    combined_data["ROI/Drawdown Ratio"] = combined_data.apply(
                        lambda row: row["ROI (%)"] / abs(row["Max Drawdown (%)"]) if row["Max Drawdown (%)"] != 0 else 0, 
                        axis=1
                    )
                
                # 1. Scatter plot: ROI vs Drawdown
                ax1 = plt.subplot(2, 3, 1)
                if "Max Drawdown (%)" in combined_data.columns and "ROI (%)" in combined_data.columns:
                    colors = ['green' if roi >= 0 else 'red' for roi in combined_data["ROI (%)"]]
                    # Check if Shares column exists for sizing
                    sizes = combined_data["Shares"]*20 if "Shares" in combined_data.columns else 50
                    scatter = ax1.scatter(combined_data["Max Drawdown (%)"], combined_data["ROI (%)"], 
                                         s=sizes, c=colors, alpha=0.6)
                    ax1.set_title("ROI vs Maximum Drawdown", fontsize=14, fontweight='bold')
                    ax1.set_xlabel("Maximum Drawdown (%)")
                    ax1.set_ylabel("ROI (%)")
                    
                    # Add ticker labels if Ticker column exists
                    if "Ticker" in combined_data.columns:
                        for i, row in combined_data.iterrows():
                            ax1.annotate(row["Ticker"], 
                                        (row["Max Drawdown (%)"], row["ROI (%)"]),
                                        xytext=(5, 5), textcoords='offset points',
                                        fontsize=9, ha='left')
                    
                    ax1.grid(True, alpha=0.3)
                    ax1.axhline(y=0, color='black', linewidth=0.5)
                    ax1.axvline(x=0, color='black', linewidth=0.5)
                else:
                    ax1.text(0.5, 0.5, "No data available", ha='center', va='center', transform=ax1.transAxes)
                    ax1.set_title("ROI vs Maximum Drawdown", fontsize=14, fontweight='bold')
                
                # 2. Bar chart of ROI
                ax2 = plt.subplot(2, 3, 2)
                if "ROI (%)" in combined_data.columns and "Ticker" in combined_data.columns:
                    colors = ['green' if roi >= 0 else 'red' for roi in combined_data["ROI (%)"]]
                    bars = ax2.bar(range(len(combined_data)), combined_data["ROI (%)"], color=colors)
                    ax2.set_title("ROI by Stock", fontsize=14, fontweight='bold')
                    ax2.set_xlabel("Stock Ticker")
                    ax2.set_ylabel("ROI (%)")
                    ax2.set_xticks(range(len(combined_data)))
                    ax2.set_xticklabels(combined_data["Ticker"], rotation=45, ha='right')
                    
                    # Add value labels on bars
                    for i, (bar, roi) in enumerate(zip(bars, combined_data["ROI (%)"])): 
                        height = bar.get_height()
                        ax2.text(bar.get_x() + bar.get_width()/2., height + (1 if height >= 0 else -3),
                                f'{roi:.1f}%', ha='center', va='bottom' if height >= 0 else 'top', fontsize=8)
                    
                    ax2.grid(True, axis='y', alpha=0.3)
                    ax2.axhline(y=0, color='black', linewidth=0.5)
                else:
                    ax2.text(0.5, 0.5, "No data available", ha='center', va='center', transform=ax2.transAxes)
                    ax2.set_title("ROI by Stock", fontsize=14, fontweight='bold')
                
                # 3. Bar chart of Max Drawdown
                ax3 = plt.subplot(2, 3, 3)
                if "Max Drawdown (%)" in combined_data.columns and "Ticker" in combined_data.columns:
                    colors = ['red' if drawdown < 0 else 'green' for drawdown in combined_data["Max Drawdown (%)"]]
                    bars = ax3.bar(range(len(combined_data)), combined_data["Max Drawdown (%)"], color=colors)
                    ax3.set_title("Max Drawdown by Stock", fontsize=14, fontweight='bold')
                    ax3.set_xlabel("Stock Ticker")
                    ax3.set_ylabel("Max Drawdown (%)")
                    ax3.set_xticks(range(len(combined_data)))
                    ax3.set_xticklabels(combined_data["Ticker"], rotation=45, ha='right')
                    
                    # Add value labels on bars
                    for i, (bar, drawdown) in enumerate(zip(bars, combined_data["Max Drawdown (%)"])): 
                        height = bar.get_height()
                        ax3.text(bar.get_x() + bar.get_width()/2., height + (1 if height >= 0 else -3),
                                f'{drawdown:.1f}%', ha='center', va='bottom' if height >= 0 else 'top', fontsize=8)
                    
                    ax3.grid(True, axis='y', alpha=0.3)
                    ax3.axhline(y=0, color='black', linewidth=0.5)
                else:
                    ax3.text(0.5, 0.5, "No data available", ha='center', va='center', transform=ax3.transAxes)
                    ax3.set_title("Max Drawdown by Stock", fontsize=14, fontweight='bold')
                
                # 4. Scatter plot: ROI vs Drawdown Ratio
                ax4 = plt.subplot(2, 3, 4)
                if "ROI/Drawdown Ratio" in combined_data.columns and "ROI (%)" in combined_data.columns:
                    colors = ['green' if roi >= 0 else 'red' for roi in combined_data["ROI (%)"]]
                    # Check if Shares column exists for sizing
                    sizes = combined_data["Shares"]*20 if "Shares" in combined_data.columns else 50
                    scatter = ax4.scatter(combined_data["ROI/Drawdown Ratio"], combined_data["ROI (%)"], 
                                         s=sizes, c=colors, alpha=0.6)
                    ax4.set_title("ROI vs ROI/Drawdown Ratio", fontsize=14, fontweight='bold')
                    ax4.set_xlabel("ROI/Drawdown Ratio")
                    ax4.set_ylabel("ROI (%)")
                    
                    # Add ticker labels if Ticker column exists
                    if "Ticker" in combined_data.columns:
                        for i, row in combined_data.iterrows():
                            ax4.annotate(row["Ticker"], 
                                        (row["ROI/Drawdown Ratio"], row["ROI (%)"]),
                                        xytext=(5, 5), textcoords='offset points',
                                        fontsize=9, ha='left')
                    
                    ax4.grid(True, alpha=0.3)
                    ax4.axhline(y=0, color='black', linewidth=0.5)
                    ax4.axvline(x=0, color='black', linewidth=0.5)
                else:
                    ax4.text(0.5, 0.5, "No data available", ha='center', va='center', transform=ax4.transAxes)
                    ax4.set_title("ROI vs ROI/Drawdown Ratio", fontsize=14, fontweight='bold')
                
                # # 5. Bar chart of ROI for all stocks ever purchased
                # ax5 = plt.subplot(2, 3, 5)
                # if all_stocks_roi is not None and not all_stocks_roi.empty and "ROI (%)" in all_stocks_roi.columns and "Ticker" in all_stocks_roi.columns:
                #     colors = ['green' if roi >= 0 else 'red' for roi in all_stocks_roi["ROI (%)"]]
                #     bars = ax5.bar(range(len(all_stocks_roi)), all_stocks_roi["ROI (%)"], color=colors)
                #     ax5.set_title("ROI by Stock (All Stocks Ever Purchased)", fontsize=14, fontweight='bold')
                #     ax5.set_xlabel("Stock Ticker")
                #     ax5.set_ylabel("ROI (%)")
                #     ax5.set_xticks(range(len(all_stocks_roi)))
                #     ax5.set_xticklabels(all_stocks_roi["Ticker"], rotation=45, ha='right')
                #
                #     # Add value labels on bars
                #     for i, (bar, roi) in enumerate(zip(bars, all_stocks_roi["ROI (%)"])):
                #         height = bar.get_height()
                #         ax5.text(bar.get_x() + bar.get_width()/2., height + (1 if height >= 0 else -3),
                #                 f'{roi:.1f}%', ha='center', va='bottom' if height >= 0 else 'top', fontsize=8)
                #
                #     ax5.grid(True, axis='y', alpha=0.3)
                #     ax5.axhline(y=0, color='black', linewidth=0.5)
                # else:
                #     ax5.text(0.5, 0.5, "Data not available", ha='center', va='center', transform=ax5.transAxes)
                #     ax5.set_title("ROI by Stock (All Stocks Ever Purchased)", fontsize=14, fontweight='bold')
                #
                # # 6. Bar chart of Max Drawdown for all stocks ever purchased
                # ax6 = plt.subplot(2, 3, 6)
                # if all_stocks_roi is not None and not all_stocks_roi.empty and "Ticker" in all_stocks_roi.columns:
                #     # Map drawdown data to all_stocks_roi
                #     all_stocks_drawdown = all_stocks_roi.copy()
                #     if isinstance(drawdown_data, dict):
                #         all_stocks_drawdown["Max Drawdown (%)"] = all_stocks_drawdown["Ticker"].map(
                #             {ticker: data["Max Drawdown (%)"] for ticker, data in drawdown_data.items()}
                #         )
                #
                #     if "Max Drawdown (%)" in all_stocks_drawdown.columns:
                #         colors = ['red' if drawdown < 0 else 'green' for drawdown in all_stocks_drawdown["Max Drawdown (%)"]]
                #         bars = ax6.bar(range(len(all_stocks_drawdown)), all_stocks_drawdown["Max Drawdown (%)"], color=colors)
                #         ax6.set_title("Max Drawdown by Stock (All Stocks Ever Purchased)", fontsize=14, fontweight='bold')
                #         ax6.set_xlabel("Stock Ticker")
                #         ax6.set_ylabel("Max Drawdown (%)")
                #         ax6.set_xticks(range(len(all_stocks_drawdown)))
                #         ax6.set_xticklabels(all_stocks_drawdown["Ticker"], rotation=45, ha='right')
                #
                #         # Add value labels on bars
                #         for i, (bar, drawdown) in enumerate(zip(bars, all_stocks_drawdown["Max Drawdown (%)"])):
                #             height = bar.get_height()
                #             ax6.text(bar.get_x() + bar.get_width()/2., height + (1 if height >= 0 else -3),
                #                     f'{drawdown:.1f}%', ha='center', va='bottom' if height >= 0 else 'top', fontsize=8)
                #
                #         ax6.grid(True, axis='y', alpha=0.3)
                #         ax6.axhline(y=0, color='black', linewidth=0.5)
                #     else:
                #         ax6.text(0.5, 0.5, "Drawdown data not available", ha='center', va='center', transform=ax6.transAxes)
                #         ax6.set_title("Max Drawdown by Stock (All Stocks Ever Purchased)", fontsize=14, fontweight='bold')
                # else:
                #     ax6.text(0.5, 0.5, "Data not available", ha='center', va='center', transform=ax6.transAxes)
                #     ax6.set_title("Max Drawdown by Stock (All Stocks Ever Purchased)", fontsize=14, fontweight='bold')
                #
        plt.tight_layout()
        
        # Save plot
        filepath = self.save_plot(fig, "roi_drawdown_dashboard.png")
        plt.close()
        return filepath
    
    def generate_comparative_roi_dashboard(self, all_stocks_roi: pd.DataFrame, current_portfolio_roi: pd.DataFrame) -> str:
        """Create a dashboard comparing both ROI analyses."""
        # Create a figure with subplots
        fig = plt.figure(figsize=(20, 12))
        
        # Check if required columns exist
        required_columns = ["Cost Basis ($)", "Market Value ($)", "ROI (%)", "Ticker"]
        
        # 1. Bar chart comparing both portfolio ROIs
        ax1 = plt.subplot(2, 3, 1)
        
        # Check if required columns exist in both DataFrames
        all_stocks_has_columns = all(col in all_stocks_roi.columns for col in required_columns[:2])
        current_portfolio_has_columns = all(col in current_portfolio_roi.columns for col in required_columns[:2])
        
        if all_stocks_has_columns and not all_stocks_roi.empty:
            all_stocks_total_cost = all_stocks_roi["Cost Basis ($)"].sum()
            all_stocks_total_value = all_stocks_roi["Market Value ($)"].sum()
            all_stocks_roi_pct = ((all_stocks_total_value / all_stocks_total_cost) - 1) * 100 if all_stocks_total_cost > 0 else 0
        else:
            all_stocks_total_cost = 0
            all_stocks_total_value = 0
            all_stocks_roi_pct = 0
        
        if current_portfolio_has_columns and not current_portfolio_roi.empty:
            current_portfolio_total_cost = current_portfolio_roi["Cost Basis ($)"].sum()
            current_portfolio_total_value = current_portfolio_roi["Market Value ($)"].sum()
            current_portfolio_roi_pct = ((current_portfolio_total_value / current_portfolio_total_cost) - 1) * 100 if current_portfolio_total_cost > 0 else 0
        else:
            current_portfolio_total_cost = 0
            current_portfolio_total_value = 0
            current_portfolio_roi_pct = 0
        
        portfolios = ['All Stocks\nEver Purchased', 'Currently\nHeld Stocks']
        rois = [all_stocks_roi_pct, current_portfolio_roi_pct]
        colors = ['blue', 'green']
        
        bars = ax1.bar(portfolios, rois, color=colors)
        ax1.set_title("Portfolio ROI Comparison", fontsize=14, fontweight='bold')
        ax1.set_ylabel("ROI (%)")
        
        # Add value labels on bars
        for bar, roi in zip(bars, rois):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + (0.5 if height >= 0 else -1),
                    f'{roi:.2f}%', ha='center', va='bottom' if height >= 0 else 'top', fontsize=10)
        
        ax1.grid(True, axis='y', alpha=0.3)
        ax1.axhline(y=0, color='black', linewidth=0.5)
        
        # 2. Bar chart of ROI for all stocks ever purchased
        ax2 = plt.subplot(2, 3, 2)
        if all(col in all_stocks_roi.columns for col in required_columns[:3]) and not all_stocks_roi.empty:
            colors = ['green' if roi >= 0 else 'red' for roi in all_stocks_roi["ROI (%)"]]
            bars = ax2.bar(range(len(all_stocks_roi)), all_stocks_roi["ROI (%)"], color=colors)
            ax2.set_title("ROI - All Stocks Ever Purchased", fontsize=14, fontweight='bold')
            ax2.set_xlabel("Stock Ticker")
            ax2.set_ylabel("ROI (%)")
            ax2.set_xticks(range(len(all_stocks_roi)))
            ax2.set_xticklabels(all_stocks_roi["Ticker"], rotation=45, ha='right')
            
            # Add value labels on bars
            for i, (bar, roi) in enumerate(zip(bars, all_stocks_roi["ROI (%)"])):
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height + (1 if height >= 0 else -3),
                        f'{roi:.1f}%', ha='center', va='bottom' if height >= 0 else 'top', fontsize=8)
            
            ax2.grid(True, axis='y', alpha=0.3)
            ax2.axhline(y=0, color='black', linewidth=0.5)
        else:
            ax2.text(0.5, 0.5, "No data available", ha='center', va='center', transform=ax2.transAxes)
            ax2.set_title("ROI - All Stocks Ever Purchased", fontsize=14, fontweight='bold')
        
        # 3. Bar chart of ROI for currently held stocks
        ax3 = plt.subplot(2, 3, 3)
        if all(col in current_portfolio_roi.columns for col in required_columns[:3]) and not current_portfolio_roi.empty:
            colors = ['green' if roi >= 0 else 'red' for roi in current_portfolio_roi["ROI (%)"]]
            bars = ax3.bar(range(len(current_portfolio_roi)), current_portfolio_roi["ROI (%)"], color=colors)
            ax3.set_title("ROI - Currently Held Stocks", fontsize=14, fontweight='bold')
            ax3.set_xlabel("Stock Ticker")
            ax3.set_ylabel("ROI (%)")
            ax3.set_xticks(range(len(current_portfolio_roi)))
            ax3.set_xticklabels(current_portfolio_roi["Ticker"], rotation=45, ha='right')
            
            # Add value labels on bars
            for i, (bar, roi) in enumerate(zip(bars, current_portfolio_roi["ROI (%)"])):
                height = bar.get_height()
                ax3.text(bar.get_x() + bar.get_width()/2., height + (1 if height >= 0 else -3),
                        f'{roi:.1f}%', ha='center', va='bottom' if height >= 0 else 'top', fontsize=8)
            
            ax3.grid(True, axis='y', alpha=0.3)
            ax3.axhline(y=0, color='black', linewidth=0.5)
        else:
            ax3.text(0.5, 0.5, "No data available", ha='center', va='center', transform=ax3.transAxes)
            ax3.set_title("ROI - Currently Held Stocks", fontsize=14, fontweight='bold')
        
        # 4. Pie chart of all stocks portfolio composition
        ax4 = plt.subplot(2, 3, 4)
        if all(col in all_stocks_roi.columns for col in ["Cost Basis ($)", "Ticker"]) and not all_stocks_roi.empty:
            # Only include stocks with positive value
            positive_value = all_stocks_roi
            if len(positive_value) > 0:
                ax4.pie(positive_value["Cost Basis ($)"], labels=positive_value["Ticker"],
                       autopct='%1.1f%%', startangle=90)
            else:
                ax4.text(0.5, 0.5, "No positive values", ha='center', va='center', transform=ax4.transAxes)
        else:
            ax4.text(0.5, 0.5, "No data available", ha='center', va='center', transform=ax4.transAxes)
        ax4.set_title("All Stocks Ever Purchased by Cost Basis", fontsize=14, fontweight='bold')
        
        # 5. Pie chart of current portfolio composition
        ax5 = plt.subplot(2, 3, 5)
        if all(col in current_portfolio_roi.columns for col in ["Cost Basis ($)", "Ticker"]) and not current_portfolio_roi.empty:
            # Only include stocks with positive value
            positive_value = current_portfolio_roi[current_portfolio_roi["Market Value ($)"] > 0]
            if len(positive_value) > 0:
                ax5.pie(positive_value["Cost Basis ($)"], labels=positive_value["Ticker"],
                       autopct='%1.1f%%', startangle=90)
            else:
                ax5.text(0.5, 0.5, "No positive values", ha='center', va='center', transform=ax5.transAxes)
        else:
            ax5.text(0.5, 0.5, "No data available", ha='center', va='center', transform=ax5.transAxes)
        ax5.set_title("Currently Held by Cost Basis", fontsize=14, fontweight='bold')
        
        # 6. Bar chart comparing cost basis vs Market Value
        ax6 = plt.subplot(2, 3, 6)
        if (all(col in all_stocks_roi.columns for col in ["Cost Basis ($)", "Market Value ($)", "Ticker"]) and
            not all_stocks_roi.empty):
            x = np.arange(len(all_stocks_roi))
            width = 0.35
            
            bars1 = ax6.bar(x - width/2, all_stocks_roi["Cost Basis ($)"], width, label='Cost Basis', color='skyblue')
            bars2 = ax6.bar(x + width/2, all_stocks_roi["Market Value ($)"] + all_stocks_roi["Realized Proceeds ($)"], width, label='Market Value', color='lightgreen')
            
            ax6.set_title("Cost Basis vs (Realized Proceeds+Market Value)", fontsize=14, fontweight='bold')
            ax6.set_xlabel("Stock Ticker")
            ax6.set_ylabel("Value ($)")
            ax6.set_xticks(x)
            ax6.set_xticklabels(all_stocks_roi["Ticker"], rotation=45, ha='right')
            ax6.legend()
        else:
            ax6.text(0.5, 0.5, "No data available", ha='center', va='center', transform=ax6.transAxes)
            ax6.set_title("Cost Basis vs (Realized Proceeds+Market Value)", fontsize=14, fontweight='bold')
        
        ax6.grid(True, axis='y', alpha=0.3)
        
        plt.tight_layout()
        
        # Save plot
        filepath = self.save_plot(fig, "comparative_roi_dashboard.png")
        plt.close()
        return filepath
    
    def generate_daily_performance_plot(self, daily_data: pd.DataFrame) -> str:
        """Generate daily performance plot."""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Daily returns
        ax1.bar(daily_data["Date"], daily_data["Daily Return (%)"], color=['green' if x >= 0 else 'red' for x in daily_data["Daily Return (%)"]])
        ax1.set_title("Daily Returns (%)", fontsize=14, fontweight='bold')
        ax1.set_ylabel("Daily Return (%)")
        ax1.grid(True, alpha=0.3)
        ax1.axhline(y=0, color='black', linewidth=0.5)
        
        # Cumulative returns
        ax2.plot(daily_data["Date"], daily_data["Cumulative Return (%)"], color='blue', linewidth=2, marker='o')
        ax2.set_title("Cumulative Returns (%)", fontsize=14, fontweight='bold')
        ax2.set_ylabel("Cumulative Return (%)")
        ax2.set_xlabel("Date")
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=0, color='black', linewidth=0.5)
        
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # Save plot
        filepath = self.save_plot(fig, "daily_performance.png")
        plt.close()
        return filepath
    
    def generate_individual_drawdown_plot(self, portfolio_df: pd.DataFrame) -> str:
        """Generate and save the individual stock drawdown over time plot."""
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Get unique tickers
        tickers = portfolio_df["Ticker"].unique()
        
        # Define a color map
        colors = plt.cm.tab10(np.linspace(0, 1, len(tickers)))
        
        # Plot drawdown over time for each stock
        for i, ticker in enumerate(tickers):
            stock_data = portfolio_df[portfolio_df["Ticker"] == ticker].sort_values("Date")
            
            if len(stock_data) > 0:
                # Calculate drawdown over time
                stock_with_drawdown = self.calculate_drawdown_over_time(stock_data)
                
                # Only plot if we have more than one data point
                if len(stock_with_drawdown) > 1:
                    ax.plot(stock_with_drawdown["Date"], stock_with_drawdown["Drawdown (%)"], 
                           marker='o', linewidth=2, label=ticker, color=colors[i])
                    
                    # Add ticker label at the end of the line
                    last_point = stock_with_drawdown.iloc[-1]
                    ax.annotate(ticker, 
                               (last_point["Date"], last_point["Drawdown (%)"]),
                               xytext=(5, 0), textcoords='offset points',
                               fontsize=9, va='center')
        
        # Customize the chart
        ax.set_title("Drawdown Over Time for Each Stock", fontsize=16, fontweight='bold')
        ax.set_xlabel("Date", fontsize=12)
        ax.set_ylabel("Drawdown (%)", fontsize=12)
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color='black', linewidth=0.5)
        
        # Rotate x-axis labels
        plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        
        # Save plot
        filepath = self.save_plot(fig, "individual_drawdowns.png")
        plt.close()
        return filepath
    
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
    
    def generate_roi_over_time_plot(self, roi_time_df: pd.DataFrame) -> str:
        """Generate and save the ROI over time plot."""
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Get unique tickers
        tickers = roi_time_df["Ticker"].unique()
        
        # Define a color map
        colors = plt.cm.tab10(np.linspace(0, 1, len(tickers)))
        
        # Plot ROI over time for each stock
        for i, ticker in enumerate(tickers):
            stock_data = roi_time_df[roi_time_df["Ticker"] == ticker].sort_values("Date")
            
            if len(stock_data) > 1:  # Only plot if we have more than one data point
                # Check if we have TradeGroup to separate trades
                if "TradeGroup" in stock_data.columns:
                    # Plot each trade group separately
                    trade_groups = stock_data["TradeGroup"].unique()
                    for group in trade_groups:
                        group_data = stock_data[stock_data["TradeGroup"] == group].sort_values("Date")
                        if len(group_data) > 1:
                            # Use different line styles for different trade groups
                            linestyle = '-' if group == 0 else '--' if group == 1 else '-.' if group == 2 else ':'
                            # For the first trade group, use just the ticker name
                            label = ticker if group == 0 else f"{ticker} (Trade {group+1})"
                            ax.plot(group_data["Date"], group_data["ROI (%)"], 
                                   marker='o', linewidth=2, label=label, 
                                   color=colors[i], linestyle=linestyle)
                            
                            # Add ticker label at the end of each line
                            last_point = group_data.iloc[-1]
                            # For the first trade group, use just the ticker name
                            annotation = ticker if group == 0 else f"{ticker} (Trade {group+1})"
                            ax.annotate(annotation, 
                                       (last_point["Date"], last_point["ROI (%)"]),
                                       xytext=(5, 0), textcoords='offset points',
                                       fontsize=9, va='center', color=colors[i])
                else:
                    # Original plotting method for backward compatibility
                    ax.plot(stock_data["Date"], stock_data["ROI (%)"], 
                           marker='o', linewidth=2, label=ticker, color=colors[i])
                    
                    # Add ticker label at the end of the line
                    last_point = stock_data.iloc[-1]
                    ax.annotate(ticker, 
                               (last_point["Date"], last_point["ROI (%)"]),
                               xytext=(5, 0), textcoords='offset points',
                               fontsize=9, va='center')
        
        # Customize the chart
        ax.set_title("ROI Over Time for Each Stock", fontsize=16, fontweight='bold')
        ax.set_xlabel("Date", fontsize=12)
        ax.set_ylabel("ROI (%)", fontsize=12)
        ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3)
        ax.axhline(y=0, color='black', linewidth=0.5)
        
        # Rotate x-axis labels
        plt.xticks(rotation=45, ha='right')
        
        plt.tight_layout()
        
        # Save plot
        filepath = self.save_plot(fig, "roi_over_time.png")
        plt.close()
        return filepath
    
    def generate_risk_return_plot(self, portfolio_totals: pd.DataFrame) -> str:
        """Generate and save a risk-return scatter plot."""
        # Calculate daily returns
        portfolio_totals = portfolio_totals.sort_values("Date").copy()
        portfolio_totals["Daily Return (%)"] = portfolio_totals["Total Equity"].pct_change() * 100
        
        # Remove NaN values
        returns = portfolio_totals["Daily Return (%)"].dropna()
        
        # Calculate metrics
        avg_return = returns.mean()
        volatility = returns.std()
        
        # Create plot
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Scatter plot of daily returns
        ax.scatter(volatility, avg_return, s=100, c='blue', alpha=0.7, edgecolors='black')
        ax.annotate('Portfolio', (volatility, avg_return), xytext=(10, 0), 
                    textcoords='offset points', fontsize=12, fontweight='bold')
        
        # Add S&P 500 comparison point (hypothetical)
        # For a more accurate comparison, we would need actual S&P 500 daily returns
        spx_volatility = 15.0  # Hypothetical value
        spx_return = 0.05      # Hypothetical value
        ax.scatter(spx_volatility, spx_return, s=100, c='orange', alpha=0.7, edgecolors='black')
        ax.annotate('S&P 500 (Est.)', (spx_volatility, spx_return), xytext=(10, 0), 
                    textcoords='offset points', fontsize=12, fontweight='bold')
        
        # Customize the chart
        ax.set_title("Risk-Return Profile", fontsize=16, fontweight='bold')
        ax.set_xlabel("Volatility (Standard Deviation of Returns %)", fontsize=12)
        ax.set_ylabel("Average Daily Return (%)", fontsize=12)
        ax.grid(True, alpha=0.3)
        
        # Add quadrant lines
        ax.axhline(y=0, color='black', linewidth=0.5)
        ax.axvline(x=0, color='black', linewidth=0.5)
        
        plt.tight_layout()
        
        # Save plot
        filepath = self.save_plot(fig, "risk_return_profile.png")
        plt.close()
        return filepath
    
    def generate_position_size_analysis(self, roi_df: pd.DataFrame) -> str:
        """Generate position size analysis plot."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Check if required columns exist
        required_columns = ["ROI (%)", "Shares", "Market Value ($)", "Ticker"]
        has_required_columns = all(col in roi_df.columns for col in required_columns)
        
        if not has_required_columns or roi_df.empty:
            # Display message if data is missing
            ax1.text(0.5, 0.5, "No data available", ha='center', va='center', transform=ax1.transAxes)
            ax1.set_title("Position Size vs ROI", fontsize=14, fontweight='bold')
            ax2.text(0.5, 0.5, "No data available", ha='center', va='center', transform=ax2.transAxes)
            ax2.set_title("Portfolio Allocation by ROI", fontsize=14, fontweight='bold')
            plt.tight_layout()
            filepath = self.save_plot(fig, "position_analysis.png")
            plt.close()
            return filepath
        
        # Position size vs ROI
        colors = ['green' if roi >= 0 else 'red' for roi in roi_df["ROI (%)"]]
        # Ensure all sizes are positive to avoid sqrt warnings
        sizes = np.abs(roi_df["Shares"]*20) if "Shares" in roi_df.columns else 50
        scatter = ax1.scatter(roi_df["Market Value ($)"] if "Market Value ($)" in roi_df.columns else [], 
                             roi_df["ROI (%)"] if "ROI (%)" in roi_df.columns else [], 
                             s=sizes, c=colors, alpha=0.6)
        ax1.set_title("Position Size vs ROI", fontsize=14, fontweight='bold')
        ax1.set_xlabel("Position Value ($)")
        ax1.set_ylabel("ROI (%)")
        
        # Add ticker labels if columns exist
        if "Ticker" in roi_df.columns and "Market Value ($)" in roi_df.columns and "ROI (%)" in roi_df.columns:
            for i, row in roi_df.iterrows():
                ax1.annotate(row["Ticker"], 
                            (row["Market Value ($)"], row["ROI (%)"]),
                            xytext=(5, 5), textcoords='offset points',
                            fontsize=8, ha='left')
        
        ax1.grid(True, alpha=0.3)
        ax1.axhline(y=0, color='black', linewidth=0.5)
        ax1.axvline(x=0, color='black', linewidth=0.5)
        
        # Position distribution
        if "ROI (%)" in roi_df.columns and "Ticker" in roi_df.columns:
            # Show all stocks with color coding for positive/negative ROI
            colors = ['green' if roi >= 0 else 'red' for roi in roi_df["ROI (%)"]]
            
            ax2.bar(roi_df["Ticker"], roi_df["Market Value ($)"] + roi_df["Realized Proceeds ($)"],
                    color=colors, alpha=0.7)
            ax2.set_title("Portfolio Allocation by ROI", fontsize=14, fontweight='bold')
            ax2.set_xlabel("Stock Ticker")
            ax2.set_ylabel("Realized Proceeds + Market Value ($)")
            # Set tick positions and labels
            ax2.set_xticks(range(len(roi_df["Ticker"])))
            ax2.set_xticklabels(roi_df["Ticker"], rotation=45, ha='right')
            ax2.grid(True, axis='y', alpha=0.3)
            
            # Add a legend to explain the color coding
            from matplotlib.patches import Patch
            legend_elements = [Patch(facecolor='green', label='Positive ROI'),
                              Patch(facecolor='red', label='Negative ROI')]
            ax2.legend(handles=legend_elements)
        else:
            ax2.text(0.5, 0.5, "No data available", ha='center', va='center', transform=ax2.transAxes)
            ax2.set_title("Portfolio Allocation by ROI", fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        
        # Save plot
        filepath = self.save_plot(fig, "position_analysis.png")
        plt.close()
        return filepath
    
    def generate_sector_analysis(self, roi_df: pd.DataFrame) -> str:
        """Generate sector analysis based on ticker characteristics."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Check if required columns exist
        required_columns = ["Ticker", "Market Value ($)", "Cost Basis ($)"]
        has_required_columns = all(col in roi_df.columns for col in required_columns)
        
        if not has_required_columns or roi_df.empty:
            # Display message if data is missing
            ax1.text(0.5, 0.5, "No data available", ha='center', va='center', transform=ax1.transAxes)
            ax1.set_title("Portfolio Allocation by Category", fontsize=14, fontweight='bold')
            ax2.text(0.5, 0.5, "No data available", ha='center', va='center', transform=ax2.transAxes)
            ax2.set_title("Category Performance", fontsize=14, fontweight='bold')
            plt.tight_layout()
            filepath = self.save_plot(fig, "sector_analysis.png")
            plt.close()
            return filepath
        
        # For this analysis, we'll categorize stocks based on ticker patterns
        # In a real implementation, this would use actual sector data
        
        # Create a simple categorization based on ticker length and first letter
        def categorize_ticker(ticker):
            if len(ticker) <= 3:
                return "Small Cap"
            elif len(ticker) <= 4:
                return "Mid Cap"
            else:
                return "Micro Cap"
        
        # Check if Ticker column exists before applying categorization
        if "Ticker" in roi_df.columns:
            roi_df["Category"] = roi_df["Ticker"].apply(categorize_ticker)
            
            # Calculate category performance
            if "Market Value ($)" in roi_df.columns and "Cost Basis ($)" in roi_df.columns:
                category_performance = roi_df.groupby("Category").agg({
                    "Market Value ($)": "sum",
                    "Cost Basis ($)": "sum"
                }).reset_index()
                
                if not category_performance.empty and "Cost Basis ($)" in category_performance.columns and "Market Value ($)" in category_performance.columns:
                    category_performance["ROI (%)"] = (category_performance["Market Value ($)"] / category_performance["Cost Basis ($)"] - 1) * 100
                    
                    # Category allocation
                    ax1.pie(category_performance["Market Value ($)"], labels=category_performance["Category"], 
                           autopct='%1.1f%%', startangle=90, textprops={'fontsize': 10})
                    ax1.set_title("Portfolio Allocation by Category", fontsize=14, fontweight='bold')
                    
                    # Category performance
                    if "ROI (%)" in category_performance.columns:
                        colors = ['green' if roi >= 0 else 'red' for roi in category_performance["ROI (%)"]]
                        bars = ax2.bar(category_performance["Category"], category_performance["ROI (%)"], color=colors)
                        ax2.set_title("Category Performance", fontsize=14, fontweight='bold')
                        ax2.set_ylabel("ROI (%)")
                        ax2.grid(True, axis='y', alpha=0.3)
                        ax2.axhline(y=0, color='black', linewidth=0.5)
                        
                        # Add value labels
                        for bar, roi in zip(bars, category_performance["ROI (%)"]):
                            height = bar.get_height()
                            ax2.text(bar.get_x() + bar.get_width()/2., height + (0.5 if height >= 0 else -1),
                                    f'{roi:.1f}%', ha='center', va='bottom' if height >= 0 else 'top')
                    else:
                        ax2.text(0.5, 0.5, "No ROI data", ha='center', va='center', transform=ax2.transAxes)
                        ax2.set_title("Category Performance", fontsize=14, fontweight='bold')
                else:
                    ax1.text(0.5, 0.5, "No performance data", ha='center', va='center', transform=ax1.transAxes)
                    ax1.set_title("Portfolio Allocation by Category", fontsize=14, fontweight='bold')
                    ax2.text(0.5, 0.5, "No performance data", ha='center', va='center', transform=ax2.transAxes)
                    ax2.set_title("Category Performance", fontsize=14, fontweight='bold')
            else:
                ax1.text(0.5, 0.5, "Missing value columns", ha='center', va='center', transform=ax1.transAxes)
                ax1.set_title("Portfolio Allocation by Category", fontsize=14, fontweight='bold')
                ax2.text(0.5, 0.5, "Missing value columns", ha='center', va='center', transform=ax2.transAxes)
                ax2.set_title("Category Performance", fontsize=14, fontweight='bold')
        else:
            ax1.text(0.5, 0.5, "No ticker data", ha='center', va='center', transform=ax1.transAxes)
            ax1.set_title("Portfolio Allocation by Category", fontsize=14, fontweight='bold')
            ax2.text(0.5, 0.5, "No ticker data", ha='center', va='center', transform=ax2.transAxes)
            ax2.set_title("Category Performance", fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        
        # Save plot
        filepath = self.save_plot(fig, "sector_analysis.png")
        plt.close()
        return filepath
    
    def generate_win_loss_analysis(self, win_loss_metrics: dict) -> str:
        """Generate win/loss analysis plot."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Check if win_loss_metrics has the required data
        if not win_loss_metrics or 'winning_positions' not in win_loss_metrics:
            # Display message if data is missing
            ax1.text(0.5, 0.5, "No data available", ha='center', va='center', transform=ax1.transAxes)
            ax1.set_title("Position Distribution", fontsize=14, fontweight='bold')
            ax2.text(0.5, 0.5, "No data available", ha='center', va='center', transform=ax2.transAxes)
            ax2.set_title("Average Win vs Average Loss", fontsize=14, fontweight='bold')
            plt.tight_layout()
            filepath = self.save_plot(fig, "win_loss_analysis.png")
            plt.close()
            return filepath
        
        # Win/Loss distribution
        labels = ['Winning', 'Losing', 'Breakeven']
        sizes = [win_loss_metrics['winning_positions'], win_loss_metrics['losing_positions'], win_loss_metrics['breakeven_positions']]
        colors = ['green', 'red', 'gray']
        
        ax1.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
        ax1.set_title("Position Distribution", fontsize=14, fontweight='bold')
        
        # Average win vs average loss
        categories = ['Average Win', 'Average Loss']
        values = [win_loss_metrics['avg_win'], abs(win_loss_metrics['avg_loss']) if win_loss_metrics['avg_loss'] else 0]
        colors = ['green', 'red']
        
        bars = ax2.bar(categories, values, color=colors)
        ax2.set_title("Average Win vs Average Loss", fontsize=14, fontweight='bold')
        ax2.set_ylabel("ROI (%)")
        ax2.grid(True, axis='y', alpha=0.3)
        
        # Add value labels
        for bar, value in zip(bars, values):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{value:.1f}%', ha='center', va='bottom')
        
        plt.tight_layout()
        
        # Save plot
        filepath = self.save_plot(fig, "win_loss_analysis.png")
        plt.close()
        return filepath

    def generate_cash_position_plot(self, cash_data) -> str:
        """Generate and save the cash position plot with total stock value as single bar."""
        # Extract data
        dates = sorted(cash_data['actual_cash'].keys())
        actual_cash = [cash_data['actual_cash'][date] for date in dates]
        
        # Prepare total stock values for each date
        stock_data = cash_data['stock_values']
        total_stock_values = []
        
        for date in dates:
            date_stocks = stock_data.get(date, {})
            total_value = sum(date_stocks.values())
            total_stock_values.append(total_value)
        
        # Create stacked bar chart
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Plot cash position as base
        bars1 = ax.bar(range(len(dates)), actual_cash, label='Cash Position', color='lightblue')
        
        # Plot total stock value stacked on top of cash
        bottom_values = actual_cash.copy()
        bars2 = ax.bar(range(len(dates)), total_stock_values, bottom=bottom_values, 
                      label='Total Stock Value', color='lightcoral')
        
        # Customize the chart
        ax.set_title("Daily Portfolio Composition (Cash + Total Stock Market Value)", fontsize=16, fontweight='bold')
        ax.set_xlabel("Date", fontsize=12)
        ax.set_ylabel("Value ($)", fontsize=12)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Add horizontal line at y=0
        ax.axhline(y=0, color='black', linewidth=0.5)
        
        # Highlight negative cash balance if it occurs
        negative_indices = [i for i, cash in enumerate(actual_cash) if cash < 0]
        if negative_indices:
            ax.scatter(negative_indices, [0]*len(negative_indices), color='red', s=100, marker='v', label='Negative Cash Balance')
        
        # Set x-axis labels
        ax.set_xticks(range(len(dates)))
        ax.set_xticklabels([date.strftime('%Y-%m-%d') for date in dates], rotation=45, ha='right')
        
        plt.tight_layout()
        
        # Save plot
        filepath = self.save_plot(fig, "cash_position.png")
        plt.close()
        return filepath
