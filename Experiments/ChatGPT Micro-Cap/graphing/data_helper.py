import pandas as pd 
from pathlib import Path

overall_dir = Path(__file__).parents[1]
TRADE_LOG_PATH = overall_dir / Path("csv_files/Trade Log.csv")
DAILY_PATH = overall_dir / Path("csv_files/Daily Updates.csv")

def load_data(trade_log_path: str | Path, daily_updates_path: str | Path):
    trades = pd.read_csv(trade_log_path, parse_dates=["Date"])
    daily = pd.read_csv(daily_updates_path, parse_dates=["Date"])
    equity = daily[daily["Ticker"] == "TOTAL"].sort_values("Date")
    return trades, daily, equity

def assemble_path(file_name: str) -> Path:
    path = overall_dir  / Path(f"images/{file_name}")
    return path



