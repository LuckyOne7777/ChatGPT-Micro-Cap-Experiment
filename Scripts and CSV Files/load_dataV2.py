import pandas as pd
import numpy as np

def avg_ticker():
    equity_df = pd.read_csv("Scripts and CSV Files/Daily Updates.csv") 
    equity_df = equity_df[equity_df["Ticker"] != "TOTAL"] 
    total_ticker_num = len(equity_df["Ticker"]) 
    total_day_num = equity_df["Date"].nunique()
    avg_tickers = total_ticker_num / total_day_num
    return avg_tickers
# ==========================================================
# BUILD INDIVIDUAL TRADES (FIFO, PARTIAL EXITS SUPPORTED)
# ==========================================================
def build_individual_trades(trade_log: pd.DataFrame) -> pd.DataFrame:
    df = trade_log.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date")

    trades = []

    for ticker, tdf in df.groupby("Ticker"):
        open_lots = []

        for _, row in tdf.iterrows():

            # ENTRY
            if pd.notna(row.get("Shares Bought")):
                open_lots.append({
                    "shares": row["Shares Bought"],
                    "price": row["Cost Basis"] / row["Shares Bought"],
                    "date": row["Date"]
                })

            # EXIT
            if pd.notna(row.get("Shares Sold")) and open_lots:
                shares_to_close = row["Shares Sold"]

                avg_entry_price = np.average(
                    [lot["price"] for lot in open_lots],
                    weights=[lot["shares"] for lot in open_lots]
                )

                exit_price = row["PnL"] / row["Shares Sold"] + avg_entry_price

                while shares_to_close > 0 and open_lots:
                    lot = open_lots[0]
                    closed_shares = min(lot["shares"], shares_to_close)

                    pnl = closed_shares * (exit_price - lot["price"])
                    holding_days = (row["Date"] - lot["date"]).days

                    trades.append({
                        "Ticker": ticker,
                        "Entry_Date": lot["date"],
                        "Exit_Date": row["Date"],
                        "Shares": closed_shares,
                        "Entry_Price": lot["price"],
                        "Exit_Price": exit_price,
                        "PnL": pnl,
                        "Holding_Days": holding_days
                    })

                    lot["shares"] -= closed_shares
                    shares_to_close -= closed_shares

                    if lot["shares"] == 0:
                        open_lots.pop(0)

    return pd.DataFrame(trades)


# ==========================================================
# BUILD PURE PnL "TRADES" (ONE ROW PER TICKER)
# ==========================================================
def build_pure_ticker_trades(trades: pd.DataFrame) -> pd.DataFrame:
    return (
        trades
        .assign(position_value=lambda x: x["Shares"] * x["Entry_Price"])
        .groupby("Ticker")
        .apply(lambda x: pd.Series({
            "PnL": x["PnL"].sum(),
            "Holding_Days": x["Holding_Days"].sum(),
            "avg_position_size": x["position_value"].mean(),
            "num_trades": len(x)
        }))
        .reset_index()
    )


# ==========================================================
# COMPUTE METRICS (GENERIC — USED BY BOTH LAYERS)
# ==========================================================
def compute_metrics(
    df: pd.DataFrame,
    pnl_col: str = "PnL",
    holding_col: str = "Holding_Days",
    position_series: pd.Series | None = None
):
    wins = df[df[pnl_col] > 0][pnl_col]
    losses = df[df[pnl_col] < 0][pnl_col]

    total_trades = len(df)
    win_rate = len(wins) / total_trades if total_trades else np.nan

    avg_win = wins.mean()
    median_win = wins.median()

    avg_loss = losses.mean()
    median_loss = losses.median()

    profit_factor = (
        wins.sum() / abs(losses.sum())
        if losses.sum() != 0 else np.inf
    )

    expectancy = (
        avg_win * win_rate +
        avg_loss * (1 - win_rate)
    )

    total_holding = df[holding_col].sum()
    avg_position = position_series.mean() if position_series is not None else np.nan

    return {
        "total_trades": total_trades,
        "win_rate": win_rate,
        "avg_win": avg_win,
        "median_win": median_win,
        "avg_loss": avg_loss,
        "median_loss": median_loss,
        "profit_factor": profit_factor,
        "expectancy": expectancy,
        "total_holding_days": total_holding,
        "avg_position_size": avg_position
    }


# ==========================================================
# COMPUTE ALL RESULTS
# ==========================================================
def compute_trade_metrics(trade_log: pd.DataFrame):

    # Individual FIFO trades
    trades = build_individual_trades(trade_log)

    individual_metrics = compute_metrics(
    trades,
    position_series=(trades["Shares"] * trades["Entry_Price"])
)


    # Repeated tickers (INFO ONLY)
    repeated_tickers = (
        trades.groupby("Ticker")
        .size()
        .rename("num_trades")
        .reset_index()
    )
    repeated_tickers = repeated_tickers[repeated_tickers["num_trades"] > 1]
    individual_metrics["num_repeated_tickers"] = len(repeated_tickers)

    # Pure ticker trades
    pure_ticker_trades = build_pure_ticker_trades(trades)

    pure_ticker_metrics = compute_metrics(
    pure_ticker_trades,
    position_series=pure_ticker_trades["avg_position_size"]
)


    # Concentration
    wins = trades[trades["PnL"] > 0]
    losses = trades[trades["PnL"] < 0]

    top_3_winners = (
        wins.sort_values("PnL", ascending=False)
        .head(3)
        .assign(profit_pct=lambda x: x["PnL"] / wins["PnL"].sum())
        if not wins.empty else pd.DataFrame()
    )

    top_3_losers = (
        losses.sort_values("PnL")
        .head(3)
        .assign(loss_pct=lambda x: abs(x["PnL"]) / abs(losses["PnL"].sum()))
        if not losses.empty else pd.DataFrame()
    )

    return {
        "individual_metrics": individual_metrics,
        "individual_trades": trades,
        "pure_ticker_metrics": pure_ticker_metrics,
        "pure_ticker_trades": pure_ticker_trades,
        "top_3_winners": top_3_winners,
        "top_3_losers": top_3_losers,
        "repeated_ticker_trades": repeated_tickers
    }


# ==========================================================
# PRINT RESULTS
# ==========================================================
def print_trade_results(results: dict):

    avg_tickers = avg_ticker()

    print("\n" + "=" * 60)
    print("TRADE PERFORMANCE METRICS (INDIVIDUAL TRADES)")
    print("=" * 60)
    for k, v in results["individual_metrics"].items():
        print(f"{k:30s}: {v:,.4f}" if isinstance(v, float) else f"{k:30s}: {v}")

    print("\n" + "=" * 60)
    print("INDIVIDUAL CLOSED TRADES")
    print("=" * 60)
    print(results["individual_trades"].to_string(index=False))

    print("\n" + "=" * 60)
    print("TRADE PERFORMANCE METRICS (PURE PnL BY TICKER)")
    print("=" * 60)
    for k, v in results["pure_ticker_metrics"].items():
        print(f"{k:30s}: {v:,.4f}" if isinstance(v, float) else f"{k:30s}: {v}")

    print("\n" + "=" * 60)
    print("AVERAGE NUMBER OF TICKERS PER DAY")
    print("=" * 60)
    print(avg_tickers)

    print("\n" + "=" * 60)
    print("PURE PnL TRADES (ONE ROW PER TICKER)")
    print("=" * 60)
    print(results["pure_ticker_trades"].sort_values("PnL", ascending=False).to_string(index=False))

    print("\n" + "=" * 60)
    print("TOP 3 WINNING TRADES")
    print("=" * 60)
    print(results["top_3_winners"].to_string(index=False))

    print("\n" + "=" * 60)
    print("TOP 3 LOSING TRADES")
    print("=" * 60)
    print(results["top_3_losers"].to_string(index=False))


# ==========================================================
# RUN
# ==========================================================
if __name__ == "__main__":
    trade_log = pd.read_csv("Scripts and CSV Files/Trade Log.csv")
    results = compute_trade_metrics(trade_log)
    print_trade_results(results)
