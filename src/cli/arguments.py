"""
Command line argument parsing for the report generator.
"""

import argparse
from datetime import datetime


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Generate a comprehensive financial report for the ChatGPT Micro Cap Experiment.")
    parser.add_argument("--data-dir", type=str, default="Scripts and CSV Files", help="Directory containing the portfolio and trade log CSV files")
    parser.add_argument("--output-dir", type=str, default="Reports", help="Output directory for reports (default: Reports)")
    parser.add_argument("--no-browser", action="store_true", help="Don't print browser open message")
    parser.add_argument("--date", type=str, help="Generate report ending on this date (YYYY-MM-DD). By default, uses today's date.")
    return parser.parse_args()