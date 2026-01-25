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
        assemble_path("total_logged_days_by_ticker.png"),
        dpi=300,
        bbox_inches="tight"
    )
    plt.show()

from data_helper import load_data, assemble_path

trades, daily, equity = load_data()

plot_total_logged_days_by_ticker(daily)
