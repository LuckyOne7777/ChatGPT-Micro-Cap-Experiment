import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf # type: ignore
from pathlib import Path

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
    plt.savefig("Scripts and CSV Files/images/drawdown.png", dpi=300, bbox_inches="tight")
    plt.show()

def load_data(trade_log_path: str, daily_updates_path: str):
    trades = pd.read_csv(trade_log_path, parse_dates=["Date"])
    daily = pd.read_csv(daily_updates_path, parse_dates=["Date"])
    equity = daily[daily["Ticker"] == "TOTAL"].sort_values("Date")
    return trades, daily, equity


trades, daily, equity = load_data("Scripts and CSV Files/Trade Log.csv", "Scripts and CSV Files/Daily Updates.csv",)
plot_drawdown(equity)