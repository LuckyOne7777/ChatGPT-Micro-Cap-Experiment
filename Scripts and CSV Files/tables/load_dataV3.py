import pandas as pd
import numpy as np

# ==========================================================
# AVERAGE NUMBER OF TICKERS HELD PER DAY
# ==========================================================
def avg_tickers_per_day():
    df = pd.read_csv(
        "Scripts and CSV Files/Daily Updates.csv",
        parse_dates=["Date"]
    )
    df = df[df["Ticker"] != "TOTAL"]

    return df.groupby("Date")["Ticker"].nunique().mean()


# ==========================================================
# BUILD FIFO LOT-LEVEL REALIZED EXITS
# ==========================================================
def build_fifo_lot_exits(trade_log: pd.DataFrame) -> pd.DataFrame:
    df = trade_log.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values("Date")

    realized = []

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
                exit_price = row["Sell Price"]

                while shares_to_close > 0 and open_lots:
                    lot = open_lots[0]
                    closed_shares = min(lot["shares"], shares_to_close)

                    pnl = closed_shares * (exit_price - lot["price"])
                    holding_days = (row["Date"] - lot["date"]).days

                    realized.append({
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

    return pd.DataFrame(realized)


# ==========================================================
# PURE PnL BY TICKER (POSITION-LEVEL)
# ==========================================================
def build_pure_pnl_by_ticker(lot_exits: pd.DataFrame) -> pd.DataFrame:
    return (
        lot_exits
        .groupby("Ticker")
        .apply(lambda x: pd.Series({
            "PnL": x["PnL"].sum(),
            "Holding_Days": (
                x["Exit_Date"].max() - x["Entry_Date"].min()
            ).days,
            "Avg_Position_Size": np.average(
                x["Shares"] * x["Entry_Price"],
                weights=x["Shares"]
            ),
            "Num_Lot_Exits": len(x)
        }))
        .reset_index()
    )


# ==========================================================
# GENERIC METRIC COMPUTATION
# ==========================================================
def compute_metrics(df: pd.DataFrame, pnl_col: str, holding_col: str):
    wins = df[df[pnl_col] > 0][pnl_col]
    losses = df[df[pnl_col] < 0][pnl_col]

    total = len(df)
    win_rate = len(wins) / total if total else np.nan

    avg_win = wins.mean()
    median_win = wins.median()
    avg_loss = losses.mean()
    median_loss = losses.median()

    profit_factor = (
        wins.sum() / abs(losses.sum())
        if losses.sum() != 0 else np.inf
    )

    expectancy = avg_win * win_rate + avg_loss * (1 - win_rate)

    return {
        "count": total,
        "win_rate": win_rate,
        "avg_win": avg_win,
        "median_win": median_win,
        "avg_loss": avg_loss,
        "median_loss": median_loss,
        "profit_factor": profit_factor,
        "expectancy": expectancy,
        "avg_holding_days": df[holding_col].mean()
    }


# ==========================================================
# MASTER COMPUTATION
# ==========================================================
def compute_trade_metrics(trade_log: pd.DataFrame):

    # FIFO lot-level exits
    lot_exits = build_fifo_lot_exits(trade_log)

    lot_metrics = compute_metrics(
        lot_exits,
        pnl_col="PnL",
        holding_col="Holding_Days"
    )

    # Pure PnL (position-level)
    pure_pnl_trades = build_pure_pnl_by_ticker(lot_exits)

    pure_pnl_metrics = compute_metrics(
        pure_pnl_trades,
        pnl_col="PnL",
        holding_col="Holding_Days"
    )

    # Repeated exposure (lot-level)
    repeated_tickers = (
        lot_exits.groupby("Ticker")
        .size()
        .rename("num_lot_exits")
        .reset_index()
        .query("num_lot_exits > 1")
    )

    # Concentration
    winners = lot_exits[lot_exits["PnL"] > 0]
    losers = lot_exits[lot_exits["PnL"] < 0]

    top_3_winners = winners.nlargest(3, "PnL")
    top_3_losers = losers.nsmallest(3, "PnL")

    return {
        "lot_exits": lot_exits,
        "lot_metrics": lot_metrics,
        "pure_pnl_trades": pure_pnl_trades,
        "pure_pnl_metrics": pure_pnl_metrics,
        "repeated_tickers": repeated_tickers,
        "top_3_winners": top_3_winners,
        "top_3_losers": top_3_losers
    }


# ==========================================================
# PRINT RESULTS
# ==========================================================
def print_results(results: dict):

    print("\n" + "=" * 60)
    print("FIFO LOT-LEVEL PERFORMANCE METRICS")
    print("=" * 60)
    for k, v in results["lot_metrics"].items():
        print(f"{k:30s}: {v:,.4f}" if isinstance(v, float) else f"{k:30s}: {v}")

    print("\n" + "=" * 60)
    print("FIFO LOT-LEVEL REALIZED EXITS")
    print("=" * 60)
    print(results["lot_exits"].to_string(index=False))

    print("\n" + "=" * 60)
    print("PURE PnL METRICS (POSITION-LEVEL)")
    print("=" * 60)
    for k, v in results["pure_pnl_metrics"].items():
        print(f"{k:30s}: {v:,.4f}" if isinstance(v, float) else f"{k:30s}: {v}")

    print("\n" + "=" * 60)
    print("AVERAGE TICKERS HELD PER DAY")
    print("=" * 60)
    print(f"{avg_tickers_per_day():.2f}")

    print("\n" + "=" * 60)
    print("PURE PnL BY TICKER (ONE ROW PER POSITION)")
    print("=" * 60)
    print(
        results["pure_pnl_trades"]
        .sort_values("PnL", ascending=False)
        .to_string(index=False)
    )

    print("\n" + "=" * 60)
    print("TOP 3 WINNING FIFO LOT EXITS")
    print("=" * 60)
    print(results["top_3_winners"].to_string(index=False))

    print("\n" + "=" * 60)
    print("TOP 3 LOSING FIFO LOT EXITS")
    print("=" * 60)
    print(results["top_3_losers"].to_string(index=False))


# ==========================================================
# RUN
# ==========================================================
if __name__ == "__main__":
    trade_log = pd.read_csv("Scripts and CSV Files/Trade Log.csv")
    results = compute_trade_metrics(trade_log)
    print_results(results)
