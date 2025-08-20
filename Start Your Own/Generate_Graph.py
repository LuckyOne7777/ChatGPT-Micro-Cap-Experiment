# Generate_Graph.py
"""
Plot portfolio performance vs. S&P 500 with a configurable starting equity.

- Normalizes BOTH series (portfolio and S&P) to the same starting equity.
- Aligns S&P data to the portfolio dates with forward-fill.
- Backwards-compatible function names for existing imports.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional, cast

import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf

DATA_DIR = Path(__file__).resolve().parent
PORTFOLIO_CSV = DATA_DIR / "chatgpt_portfolio_update.csv"


def parse_date(date_str: str, label: str) -> pd.Timestamp:
    try:
        return pd.to_datetime(date_str)
    except Exception as exc:
        raise SystemExit(f"Invalid {label} '{date_str}'. Use YYYY-MM-DD.") from exc


def _normalize_to_start(series: pd.Series, start_value: float) -> pd.Series:
    """Scale a series so its first non-NA point equals start_value."""
    s = pd.to_numeric(series, errors="coerce")
    if s.isna().all():
        raise SystemExit("Series has no numeric values to normalize.")
    base = s.dropna().iloc[0]
    if base == 0:
        raise SystemExit("Cannot normalize series with base value 0.")
    return s / base * float(start_value)


def load_portfolio_details(
    start_date: Optional[pd.Timestamp],
    end_date: Optional[pd.Timestamp],
    portfolio_csv: Path = PORTFOLIO_CSV,
) -> pd.DataFrame:
    """Return TOTAL rows (Date, Total Equity) filtered to [start_date, end_date]."""
    if not portfolio_csv.exists():
        raise SystemExit(f"Portfolio file '{portfolio_csv}' not found.")

    df = pd.read_csv(portfolio_csv)
    totals = df[df["Ticker"] == "TOTAL"].copy()
    if totals.empty:
        raise SystemExit("Portfolio CSV contains no TOTAL rows.")

    totals["Date"] = pd.to_datetime(totals["Date"], errors="coerce")
    totals["Total Equity"] = pd.to_numeric(totals["Total Equity"], errors="coerce")

    totals = totals.dropna(subset=["Date", "Total Equity"]).sort_values("Date")

    min_date = totals["Date"].min()
    max_date = totals["Date"].max()
    if start_date is None or start_date < min_date:
        start_date = min_date
    if end_date is None or end_date > max_date:
        end_date = max_date
    if start_date > end_date:
        raise SystemExit("Start date must be on or before end date.")

    mask = (totals["Date"] >= start_date) & (totals["Date"] <= end_date)
    return totals.loc[mask, ["Date", "Total Equity"]].reset_index(drop=True)


def download_sp500(dates: pd.Series, starting_equity: float = 100.0) -> pd.DataFrame:
    """
    Download S&P 500 (^GSPC), align to given dates, and normalize to starting_equity.
    Returns DataFrame with columns ['Date', 'SPX Value'] aligned 1:1 with dates.
    """
    if dates.empty:
        raise SystemExit("No dates provided to align benchmark.")

    start_date = pd.to_datetime(dates.min())
    end_date = pd.to_datetime(dates.max())

    try:
        sp500 = yf.download(
            "^GSPC",
            start=start_date,
            end=end_date + pd.Timedelta(days=1),
            progress=False,
        )
        if sp500.empty:
            raise ValueError("No data returned from Yahoo Finance")
    except Exception:
        url = "https://stooq.com/q/d/l/?s=gspc.us&i=d"
        stooq = pd.read_csv(url)
        stooq['Date'] = pd.to_datetime(stooq['Date'])
        stooq.set_index('Date', inplace=True)
        stooq.sort_index(inplace=True)
        stooq = stooq.loc[(stooq.index >= start_date) & (stooq.index <= end_date)]
        stooq['Adj Close'] = stooq['Close']
        sp500 = stooq
    sp500 = cast(pd.DataFrame, sp500)

    if sp500.empty or "Close" not in sp500.columns:
        raise SystemExit("Failed to download S&P 500 data.")

    aligned = sp500["Close"].reindex(pd.to_datetime(dates)).ffill().bfill()
    norm = _normalize_to_start(aligned, starting_equity)

    return pd.DataFrame({"Date": pd.to_datetime(dates), "SPX Value": norm.values})

def plot_comparison(
    portfolio: pd.DataFrame,
    spx: pd.DataFrame,
    starting_equity: float,
    title: str = "Portfolio vs. S&P 500 (Indexed)",
) -> None:
    """
    Plot the two normalized lines. Expects:
      - portfolio: columns ['Date', 'Total Equity'] (already normalized if desired)
      - spx:       columns ['Date', 'SPX Value'] (already normalized)
    """
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.plot(portfolio["Date"], portfolio["Total Equity"], label=f"Portfolio (start={starting_equity:g})", marker="o")
    ax.plot(spx["Date"], spx["SPX Value"], label="S&P 500", marker="o", linestyle="--")

    # Annotate last points as percent vs baseline
    p_last = float(portfolio["Total Equity"].iloc[-1])
    s_last = float(spx["SPX Value"].iloc[-1])

    p_pct = (p_last / starting_equity - 1.0) * 100.0
    s_pct = (s_last / starting_equity - 1.0) * 100.0

    ax.text(portfolio["Date"].iloc[-1], p_last * 1.01, f"{p_pct:+.1f}%", fontsize=9)
    ax.text(spx["Date"].iloc[-1], s_last * 1.01, f"{s_pct:+.1f}%", fontsize=9)

    ax.set_title(title)
    ax.set_xlabel("Date")
    ax.set_ylabel(f"Index (start = {starting_equity:g})")
    ax.legend()
    ax.grid(True)
    fig.autofmt_xdate()
    plt.tight_layout()


def main(
    start_date: Optional[pd.Timestamp],
    end_date: Optional[pd.Timestamp],
    starting_equity: float,
    output: Optional[Path],
    portfolio_csv: Path = PORTFOLIO_CSV,
) -> None:
    # Load portfolio totals in the date range
    totals = load_portfolio_details(start_date, end_date, portfolio_csv=portfolio_csv)

    # Normalize portfolio to the chosen starting equity
    norm_port = totals.copy()
    norm_port["Total Equity"] = _normalize_to_start(norm_port["Total Equity"], starting_equity)

    # Download & normalize S&P to same baseline, aligned to portfolio dates
    spx = download_sp500(norm_port["Date"], starting_equity)

    # Plot
    plot_comparison(norm_port, spx, starting_equity, title="ChatGPT Portfolio vs. S&P 500 (Indexed)")

    # Save or show
    if output:
        output = output if output.is_absolute() else DATA_DIR / output
        plt.savefig(output, bbox_inches="tight")
    else:
        plt.show()
    plt.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot portfolio performance vs S&P 500")
    parser.add_argument("--start-date", type=str, help="YYYY-MM-DD")
    parser.add_argument("--end-date", type=str, help="YYYY-MM-DD")
    parser.add_argument("--start-equity", type=float, default=100.0, help="Baseline to index both series (default 100)")
    parser.add_argument("--baseline-file", type=str, help="Path to a text file containing a single number for baseline")
    parser.add_argument("--output", type=str, help="Optional path to save the chart (.png/.jpg/.pdf)")

    args = parser.parse_args()
    start = parse_date(args.start_date, "start date") if args.start_date else None
    end = parse_date(args.end_date, "end date") if args.end_date else None

    baseline = args.start_equity
    if args.baseline_file:
        p = Path(args.baseline_file)
        if not p.exists():
            raise SystemExit(f"Baseline file not found: {p}")
        try:
            baseline = float(p.read_text().strip())
        except Exception as exc:
            raise SystemExit(f"Could not parse baseline from {p}") from exc

    out_path = Path(args.output) if args.output else None
    main(start, end, baseline, out_path)
