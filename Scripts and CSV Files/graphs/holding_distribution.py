import pandas as pd
import matplotlib.pyplot as plt

def compute_fifo_holding_days(trades_df: pd.DataFrame):
    trades_df = trades_df.sort_values("Date")

    holding_days = []

    for ticker, tdf in trades_df.groupby("Ticker"):
        buy_queue = []

        for _, row in tdf.iterrows():
            date = row["Date"]

            if not pd.isna(row["Shares Bought"]):
                buy_queue.append({
                    "date": date,
                    "shares": row["Shares Bought"]
                })

            if not pd.isna(row["Shares Sold"]):
                shares_to_sell = row["Shares Sold"]

                while shares_to_sell > 0 and buy_queue:
                    buy = buy_queue[0]
                    matched = min(buy["shares"], shares_to_sell)

                    days = (date - buy["date"]).days
                    holding_days.append(days)

                    buy["shares"] -= matched
                    shares_to_sell -= matched

                    if buy["shares"] == 0:
                        buy_queue.pop(0)

    return holding_days


def plot_holding_period_distribution(trades_df: pd.DataFrame, bins: int = 10):
    holding_days = compute_fifo_holding_days(trades_df)

    plt.figure()
    plt.hist(holding_days, bins=bins)
    plt.title("Distribution of FIFO Holding Periods (Days)")
    plt.xlabel("Holding Days")
    plt.ylabel("Lot Exit Count")
    plt.savefig(
        "Scripts and CSV Files/images/holding_distubution.png",
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
plot_holding_period_distribution(trades)