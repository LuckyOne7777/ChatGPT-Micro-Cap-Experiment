import matplotlib.pyplot as plt
import pandas as pd

def plot_top_wins_vs_losses(trades_df: pd.DataFrame, n: int = 3):
    realized = trades_df.dropna(subset=["Shares Sold", "Sell Price", "PnL"])

    pnl_by_ticker = (
        realized.groupby("Ticker")["PnL"]
        .sum()
        .sort_values(ascending=False)
    )

    top_wins = pnl_by_ticker.head(n)
    top_losses = pnl_by_ticker.tail(n)

    fig, axes = plt.subplots(1, 2)

    top_wins.plot(kind="bar", ax=axes[0])
    axes[0].set_title("Top Wins")

    top_losses.plot(kind="bar", ax=axes[1])
    axes[1].set_title("Top Losses")
    plt.savefig("Scripts and CSV Files/images/top_losses_vs_wins.png", dpi=300, bbox_inches="tight")
    plt.show()

def load_data(trade_log_path: str, daily_updates_path: str):
    trades = pd.read_csv(trade_log_path, parse_dates=["Date"])
    daily = pd.read_csv(daily_updates_path, parse_dates=["Date"])
    equity = daily[daily["Ticker"] == "TOTAL"].sort_values("Date")
    return trades, daily, equity


trades, daily, equity = load_data("Scripts and CSV Files/Trade Log.csv", "Scripts and CSV Files/Daily Updates.csv",)
plot_top_wins_vs_losses(trades)