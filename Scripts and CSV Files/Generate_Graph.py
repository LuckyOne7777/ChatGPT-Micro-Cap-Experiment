import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf

DATA_DIR = "Scripts and CSV Files"
PORTFOLIO_CSV = f"{DATA_DIR}/chatgpt_portfolio_update.csv"


def load_portfolio_totals() -> pd.DataFrame:
    """Load portfolio equity history including a baseline row."""
    chatgpt_df = pd.read_csv(PORTFOLIO_CSV)
    chatgpt_totals = chatgpt_df[chatgpt_df["Ticker"] == "TOTAL"].copy()
    chatgpt_totals["Date"] = pd.to_datetime(chatgpt_totals["Date"])

    baseline_date = pd.Timestamp("2025-06-27")
    baseline_equity = 100
    baseline_row = pd.DataFrame({"Date": [baseline_date], "Total Equity": [baseline_equity]})
    return pd.concat([baseline_row, chatgpt_totals], ignore_index=True).sort_values("Date")



def download_sp500(start_date: pd.Timestamp, end_date: pd.Timestamp) -> pd.DataFrame:
    """Download S&P 500 prices and normalise to a $100 baseline."""
    try:
        sp500 = yf.download(
            "^SPX",
            start=start_date,
            end=end_date + pd.Timedelta(days=1),
            progress=False,
            auto_adjust=True,
        )
        if sp500.empty:
            raise ValueError("No data returned from Yahoo Finance")
    except Exception:
        url = "https://stooq.com/q/d/l/?s=spx.us&i=d"
        stooq = pd.read_csv(url)
        stooq['Date'] = pd.to_datetime(stooq['Date'])
        stooq.set_index('Date', inplace=True)
        stooq.sort_index(inplace=True)
        stooq = stooq.loc[(stooq.index >= start_date) & (stooq.index <= end_date)]
        stooq['Adj Close'] = stooq['Close']
        sp500 = stooq
    sp500 = sp500.reset_index()
    if isinstance(sp500.columns, pd.MultiIndex):
        sp500.columns = sp500.columns.get_level_values(0)
    spx_27_price = 6173.07
    scaling_factor = 100 / spx_27_price
    sp500["SPX Value ($100 Invested)"] = sp500["Close"] * scaling_factor
    return sp500


def main() -> None:
    """Generate and display the comparison graph."""
    chatgpt_totals = load_portfolio_totals()

    start_date = pd.Timestamp("2025-06-27")
    end_date = chatgpt_totals["Date"].max()
    sp500 = download_sp500(start_date, end_date)

    plt.figure(figsize=(10, 6))
    plt.style.use("seaborn-v0_8-whitegrid")
    plt.plot(
        chatgpt_totals["Date"],
        chatgpt_totals["Total Equity"],
        label="ChatGPT ($100 Invested)",
        marker="o",
        color="blue",
        linewidth=2,
    )
    plt.plot(
        sp500["Date"],
        sp500["SPX Value ($100 Invested)"],
        label="S&P 500 ($100 Invested)",
        marker="o",
        color="orange",
        linestyle="--",
        linewidth=2,
    )

    final_date = chatgpt_totals["Date"].iloc[-1]
    final_chatgpt = float(chatgpt_totals["Total Equity"].iloc[-1])
    final_spx = sp500["SPX Value ($100 Invested)"].iloc[-1]

    plt.text(final_date, final_chatgpt + 0.3, f"+{final_chatgpt - 100:.1f}%", color="blue", fontsize=9)
    plt.text(final_date, final_spx + 0.9, f"+{final_spx - 100:.1f}%", color="orange", fontsize=9)

    drawdown_date = pd.Timestamp("2025-07-11")
    drawdown_value = 102.46
    plt.text(drawdown_date + pd.Timedelta(days=0.5), drawdown_value - 0.5, "-7% Drawdown", color="red", fontsize=9)
    plt.title("ChatGPT's Micro Cap Portfolio vs. S&P 500")
    plt.xlabel("Date")
    plt.ylabel("Value of $100 Investment")
    plt.xticks(rotation=15)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
