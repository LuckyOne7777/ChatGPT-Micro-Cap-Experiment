import pandas as pd 
import matplotlib.pyplot as plt

def plot_return_contribution(trades_df: pd.DataFrame):
    realized = trades_df.dropna(subset=["Shares Sold", "Sell Price", "PnL"])

    pnl_by_ticker = (
        realized.groupby("Ticker")["PnL"]
        .sum()
        .sort_values(ascending=False)
    )

    plt.figure()
    pnl_by_ticker.plot(kind="bar")
    plt.title("True Realized PnL by Ticker")
    plt.savefig(assemble_path("return_by_trades.png"), dpi=300, bbox_inches="tight")
    plt.show()

from data_helper import load_data, assemble_path
trades, daily, equity = load_data()
plot_return_contribution(trades)