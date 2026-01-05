import pandas as pd
import matplotlib.pyplot as plt

def plot_repeated_ticker_exposure(trades_df: pd.DataFrame):
    entries = trades_df.dropna(subset=["Shares Bought"])

    entry_counts = entries["Ticker"].value_counts()

    plt.figure()
    entry_counts.plot(kind="bar")
    plt.title("Number of Entries per Ticker")
    plt.savefig("Scripts and CSV Files/images/repeated_exposure.png", dpi=300, bbox_inches="tight")
    plt.show()

def load_data(trade_log_path: str, daily_updates_path: str):
    trades = pd.read_csv(trade_log_path, parse_dates=["Date"])
    daily = pd.read_csv(daily_updates_path, parse_dates=["Date"])
    equity = daily[daily["Ticker"] == "TOTAL"].sort_values("Date")
    return trades, daily, equity


trades, daily, equity = load_data("Scripts and CSV Files/Trade Log.csv", "Scripts and CSV Files/Daily Updates.csv",)
plot_repeated_ticker_exposure(trades)