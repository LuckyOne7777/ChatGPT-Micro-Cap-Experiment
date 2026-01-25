import pandas as pd
from data_helper import assemble_path, load_data
import matplotlib.pyplot as plt

def plot_repeated_ticker_exposure(trades_df: pd.DataFrame):
    # Count buy-side entries per ticker
    buy_entries = (
        trades_df
        .dropna(subset=["Shares Bought"])
        .groupby("Ticker")
        .size()
    )

    # Convert to repeated buys (re-entries)
    # 0 = bought once, >0 = re-entered
    repeated_buys = buy_entries - 1
    repeated_buys[repeated_buys < 0] = 0

    # Sort for readability
    repeated_buys = repeated_buys.sort_values(ascending=False)

    plt.figure()
    repeated_buys.plot(kind="bar")
    plt.title("Repeated Buy-Side Exposure per Ticker")
    plt.ylabel("Number of Re-Entries")
    plt.xlabel("Ticker")
    plt.savefig(
        assemble_path("repeated_exposure.png"),
        dpi=300,
        bbox_inches="tight"
    )
    plt.show()

trades, daily, equity = load_data() 
plot_repeated_ticker_exposure(trades)