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
    plt.savefig("Scripts and CSV Files/images/return_by_trades.png", dpi=300, bbox_inches="tight")
    plt.show()

def load_data(trade_log_path: str, daily_updates_path: str):
    trades = pd.read_csv(trade_log_path, parse_dates=["Date"])
    daily = pd.read_csv(daily_updates_path, parse_dates=["Date"])
    equity = daily[daily["Ticker"] == "TOTAL"].sort_values("Date")
    return trades, daily, equity


trades, daily, equity = load_data("Scripts and CSV Files/Trade Log.csv", "Scripts and CSV Files/Daily Updates.csv",)
plot_return_contribution(trades)