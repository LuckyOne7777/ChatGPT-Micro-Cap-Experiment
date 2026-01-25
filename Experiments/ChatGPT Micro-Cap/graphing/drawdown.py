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
    path = assemble_path("drawdown.png")
    plt.savefig(path, dpi=300, bbox_inches="tight")
    plt.show()

from data_helper import load_data, assemble_path

trades, daily, equity = load_data()
plot_drawdown(equity)