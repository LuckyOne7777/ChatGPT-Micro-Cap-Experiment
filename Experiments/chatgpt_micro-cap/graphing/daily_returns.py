import matplotlib.pyplot as plt 
import pandas as pd

def plot_daily_returns_distribution(
    equity_df: pd.DataFrame,
    bins: int = 30
):
    equity_df = equity_df.copy()

    # Force numeric (critical for safety)
    equity_df["Total Equity"] = pd.to_numeric(
        equity_df["Total Equity"], errors="coerce"
    )
    equity_df = equity_df.dropna(subset=["Total Equity"])
    equity_df = equity_df.sort_values("Date")

    # Daily returns
    daily_returns = equity_df["Total Equity"].pct_change().dropna() * 100

    plt.figure()
    plt.hist(daily_returns, bins=bins)
    plt.xlabel("Daily Return (%)")
    plt.ylabel("Frequency")
    plt.title("Daily Returns Distribution")
    plt.savefig(assemble_path("daily_returns.png"), dpi=300, bbox_inches="tight")
    plt.show()

from data_helper import load_data, assemble_path
trades, daily, equity = load_data()

plot_daily_returns_distribution(equity)