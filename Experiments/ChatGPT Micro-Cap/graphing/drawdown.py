import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf # type: ignore
from pathlib import Path
overall_dir = Path(__file__).parents[1]

def plot_drawdown(equity_df: pd.DataFrame):
    equity_df = equity_df.copy()

    # FORCE numeric (this is the key fix)
    equity_df["Total Equity"] = pd.to_numeric(
        equity_df["Total Equity"], errors="coerce"
    )

    # Drop any rows that failed conversion
    equity_df = equity_df.dropna(subset=["Total Equity"])

    running_max = equity_df["Total Equity"].cummax()
    drawdown = ((equity_df["Total Equity"] - running_max) / running_max) * 100

    plt.figure()
    plt.plot(equity_df["Date"], drawdown)
    plt.axhline(0)
    plt.ylabel("Drawdown (%)")
    plt.title("Drawdown Curve")
    path = overall_dir  / Path("images/drawdown.png")
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.show()

def load_data(trade_log_path: str | Path, daily_updates_path: str | Path):
    trades = pd.read_csv(trade_log_path, parse_dates=["Date"])
    daily = pd.read_csv(daily_updates_path, parse_dates=["Date"])
    equity = daily[daily["Ticker"] == "TOTAL"].sort_values("Date")
    return trades, daily, equity

TRADE_LOG_PATH = overall_dir / Path("csv_files/Trade Log.csv")
DAILY_PATH = overall_dir / Path("csv_files/Daily Updates.csv")
trades, daily, equity = load_data(TRADE_LOG_PATH, DAILY_PATH)
plot_drawdown(equity)