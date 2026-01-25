import pandas as pd 
import matplotlib.pyplot as plt

def compute_total_logged_days_by_ticker(daily_df: pd.DataFrame):
    df = daily_df.copy()

    # Exclude portfolio aggregate
    df = df[df["Ticker"] != "TOTAL"]

    # Consider a ticker held if shares > 0
    df = df[df["Shares"] > 0]

    return (
        df
        .groupby("Ticker")["Date"]
        .nunique()
        .sort_values(ascending=False)
    )
def plot_total_logged_days_by_ticker(daily_df: pd.DataFrame):
    total_days = compute_total_logged_days_by_ticker(daily_df)

    plt.figure()
    plt.bar(total_days.index, total_days.values)
    plt.xticks(rotation=45, ha="right")
    plt.xlabel("Ticker")
    plt.ylabel("Total Days Held")
    plt.title("Total Portfolio Holding Days by Ticker")

    plt.savefig(
        "Scripts and CSV Files/images/total_logged_days_by_ticker.png",
        dpi=300,
        bbox_inches="tight"
    )
    plt.show()

def load_data(trade_log_path: str, daily_updates_path: str):
    trades = pd.read_csv(trade_log_path, parse_dates=["Date"])
    daily = pd.read_csv(daily_updates_path, parse_dates=["Date"])
    equity = daily[daily["Ticker"] == "TOTAL"].sort_values("Date")
    return trades, daily, equity


trades, daily, equity = load_data("Scripts and CSV Files/Trade Log.csv", "Scripts and CSV Files/Daily Updates.csv",)

plot_total_logged_days_by_ticker(daily)
