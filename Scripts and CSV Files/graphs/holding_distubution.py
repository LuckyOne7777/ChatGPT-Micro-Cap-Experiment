import pandas as pd
import matplotlib.pyplot as plt

def plot_holding_period_distribution(trades_df: pd.DataFrame, bins: int = 10):
    buys = trades_df.dropna(subset=["Shares Bought"])
    sells = trades_df.dropna(subset=["Shares Sold"])

    merged = buys.merge(
        sells,
        on="Ticker",
        suffixes=("_buy", "_sell")
    )

    holding_days = (merged["Date_sell"] - merged["Date_buy"]).dt.days

    plt.figure()
    plt.hist(holding_days, bins=bins)
    plt.title("Holding Period Distribution (Days)")
    plt.ylabel("Frequency")
    plt.xlabel("Holding Days")
    plt.savefig("Scripts and CSV Files/images/holding_distubution.png", dpi=300, bbox_inches="tight")
    plt.show()

def load_data(trade_log_path: str, daily_updates_path: str):
    trades = pd.read_csv(trade_log_path, parse_dates=["Date"])
    daily = pd.read_csv(daily_updates_path, parse_dates=["Date"])
    equity = daily[daily["Ticker"] == "TOTAL"].sort_values("Date")
    return trades, daily, equity


trades, daily, equity = load_data("Scripts and CSV Files/Trade Log.csv", "Scripts and CSV Files/Daily Updates.csv",)
plot_holding_period_distribution(trades)