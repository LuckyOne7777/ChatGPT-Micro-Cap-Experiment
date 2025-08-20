"""Utilities for maintaining the ChatGPT micro cap portfolio.

The script processes portfolio positions, logs trades, and prints daily
results. It is intentionally lightweight and avoids changing existing
logic or behaviour.
"""

from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf
from typing import Any, cast
import os
import pkg_resources

# Shared file locations
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR  # Save files in the same folder as this script
PORTFOLIO_CSV = DATA_DIR / "chatgpt_portfolio_update.csv"
TRADE_LOG_CSV = DATA_DIR / "chatgpt_trade_log.csv"


def check_versions() -> None:
    REQUIRED = {
    "numpy": "1.26.4",
    "pandas": "2.2.2",
    "yfinance": "0.2.38",
    "matplotlib": "3.8.4",
    }

    for pkg, req_version in REQUIRED.items():
        try:
            installed_version = pkg_resources.get_distribution(pkg).version
            if installed_version != req_version:
                raise RuntimeError(
                    f"{pkg}=={req_version} required, but {installed_version} installed. "
                    f"Run: pip install -r requirements.txt"
                )
        except pkg_resources.DistributionNotFound:
            raise RuntimeError(
                f"{pkg}=={req_version} required but not installed. "
                f"Run: pip install -r requirements.txt"
        )


def check_weekend() -> str:
    today = datetime.today().strftime("%Y-%m-%d")
    dow = datetime.now().weekday()  # 0=Mon .. 6=Sun
    if dow == 5:  # Sat
        today = (pd.to_datetime(today).date() - pd.Timedelta(days=1)).isoformat()
    elif dow == 6:  # Sun
        today = (pd.to_datetime(today).date() - pd.Timedelta(days=2)).isoformat()
    return today


def download_price_data(ticker: str, **kwargs: Any) -> pd.DataFrame:
    """Download price data with Yahoo Finance and fallback to Stooq.

    Parameters
    ----------
    ticker:
        The ticker symbol to download.
    **kwargs:
        Keyword arguments passed to ``yfinance.download``. ``period`` is
        converted to a ``start``/``end`` pair for the Stooq fallback.

    Returns
    -------
    pd.DataFrame
        Price data with columns ``Open``, ``High``, ``Low``, ``Close``,
        ``Adj Close`` and ``Volume``.
    """

    data = pd.DataFrame()

    try:
        data = yf.download(ticker, **kwargs)
    except Exception:
        pass

    if data.empty:
        period = kwargs.pop("period", None)
        start = kwargs.get("start")
        end = kwargs.get("end")
        if period and not start and not end and period.endswith("d"):
            days = int(period[:-1])
            end = datetime.today()
            start = end - pd.Timedelta(days=days)
        end = end or datetime.today()
        start = start or (end - pd.Timedelta(days=5))

        candidates = [ticker]
        if ticker.startswith("^"):
            bare = ticker[1:]
            candidates.append(bare)
            candidates.append(f"{bare}.US")
        elif "." not in ticker:
            candidates.append(f"{ticker}.US")

        for symbol in candidates:
            url = f"https://stooq.com/q/d/l/?s={symbol.lower()}&i=d"
            try:
                stooq = pd.read_csv(url)
            except Exception:
                stooq = pd.DataFrame()
            if not stooq.empty:
                stooq['Date'] = pd.to_datetime(stooq['Date'])
                stooq.set_index('Date', inplace=True)
                stooq.sort_index(inplace=True)
                stooq = stooq.loc[(stooq.index >= pd.to_datetime(start)) & (stooq.index <= pd.to_datetime(end))]
                stooq['Adj Close'] = stooq['Close']
                stooq = stooq[["Open","High","Low","Close","Adj Close","Volume"]]
                data = stooq
                break
            else:
                data = pd.DataFrame()

    if data.empty:
        return pd.DataFrame(columns=["Open", "High", "Low", "Close", "Adj Close", "Volume"])
    return data

def set_data_dir(data_dir: Path) -> None:
    """Update global paths for portfolio and trade logs.

    Parameters
    ----------
    data_dir:
        Directory where ``chatgpt_portfolio_update.csv`` and
        ``chatgpt_trade_log.csv`` are stored.
    """

    global DATA_DIR, PORTFOLIO_CSV, TRADE_LOG_CSV
    DATA_DIR = Path(data_dir)
    os.makedirs(DATA_DIR, exist_ok=True)
    PORTFOLIO_CSV = DATA_DIR / "chatgpt_portfolio_update.csv"
    TRADE_LOG_CSV = DATA_DIR / "chatgpt_trade_log.csv"



def process_portfolio(
    portfolio: pd.DataFrame | dict[str, list[object]] | list[dict[str, object]],
    cash: float,
    interactive: bool = True,
) -> tuple[pd.DataFrame, float]:
    """Update daily price information, log stop-loss sells, and prompt for trades.

    Parameters
    ----------
    portfolio:
        Current holdings provided as a DataFrame, mapping of column names to
        lists, or a list of row dictionaries. The input is normalised to a
        ``DataFrame`` before any processing so that downstream code only deals
        with a single type.
    cash:
        Cash balance available for trading.
    interactive:
        When ``True`` (default) the function prompts for manual trades via
        ``input``. Set to ``False`` to skip all interactive prompts – useful
        when the function is driven by a user interface or automated tests.

    Returns
    -------
    tuple[pd.DataFrame, float]
        Updated portfolio and cash balance.
    """
    today = datetime.today().strftime("%Y-%m-%d")
    now = datetime.now()
    day = now.weekday()
    if isinstance(portfolio, pd.DataFrame):
        portfolio_df = portfolio.copy()
    elif isinstance(portfolio, (dict, list)):
        portfolio_df = pd.DataFrame(portfolio)
    else:  # pragma: no cover - defensive type check
        raise TypeError("portfolio must be a DataFrame, dict, or list of dicts")

    results: list[dict[str, object]] = []
    total_value = 0.0
    total_pnl = 0.0

    if (day == 6 or day == 5) and interactive:
        print("Today is currently a weekend. Program will use Friday's stock data. If this is wrong, check date logs.")
        # set weekend days as Friday
        today = pd.to_datetime(today).date()
        today = check_weekend()
        
    if interactive:
        while True:
            print(portfolio_df)
            action = input(
                f""" You have {cash} in cash.
Would you like to log a manual trade? Enter 'b' for buy, 's' for sell, or press Enter to continue: """
            ).strip().lower()
            if action == "b":
                try:
                    ticker = input("Enter ticker symbol: ").strip().upper()
                    shares = float(input("Enter number of shares: "))
                    buy_price = float(input("Enter buy price: "))
                    stop_loss = float(input("Enter stop loss: "))
                    if shares <= 0 or buy_price <= 0 or stop_loss <= 0:
                        raise ValueError
                except ValueError:
                    print("Invalid input. Manual buy cancelled.")
                else:
                    cash, portfolio_df = log_manual_buy(
                        buy_price,
                        shares,
                        ticker,
                        stop_loss,
                        cash,
                        portfolio_df,
                    )
                continue
            if action == "s":
                try:
                    ticker = input("Enter ticker symbol: ").strip().upper()
                    shares = float(input("Enter number of shares to sell: "))
                    sell_price = float(input("Enter sell price: "))
                    if shares <= 0 or sell_price <= 0:
                        raise ValueError
                except ValueError:
                    print("Invalid input. Manual sell cancelled.")
                else:
                    cash, portfolio_df = log_manual_sell(
                        sell_price,
                        shares,
                        ticker,
                        cash,
                        portfolio_df,
                    )
                continue
            break
    for _, stock in portfolio_df.iterrows():
        ticker = stock["ticker"]
        shares = int(stock["shares"])
        cost = stock["buy_price"]
        cost_basis = stock["cost_basis"]
        stop = stock["stop_loss"]
        data = yf.Ticker(ticker).history(period="1d")

        if data.empty:
            print(f"No data for {ticker}")
            row = {
                "Date": today,
                "Ticker": ticker,
                "Shares": shares,
                "Buy Price": cost,
                "Cost Basis": cost_basis,
                "Stop Loss": stop,
                "Current Price": "",
                "Total Value": "",
                "PnL": "",
                "Action": "NO DATA",
                "Cash Balance": "",
                "Total Equity": "",
            }
        else:
            low_price = round(float(data["Low"].iloc[-1]), 2)
            close_price = round(float(data["Close"].iloc[-1]), 2)

            if low_price <= stop:
                price = stop
                value = round(price * shares, 2)
                pnl = round((price - cost) * shares, 2)
                action = "SELL - Stop Loss Triggered"
                cash += value
                portfolio_df = log_sell(ticker, shares, price, cost, pnl, portfolio_df)
            else:
                price = close_price
                value = round(price * shares, 2)
                pnl = round((price - cost) * shares, 2)
                action = "HOLD"
                total_value += value
                total_pnl += pnl

            row = {
                "Date": today,
                "Ticker": ticker,
                "Shares": shares,
                "Buy Price": cost,
                "Cost Basis": cost_basis,
                "Stop Loss": stop,
                "Current Price": price,
                "Total Value": value,
                "PnL": pnl,
                "Action": action,
                "Cash Balance": "",
                "Total Equity": "",
            }

        results.append(row)

    # Append TOTAL summary row
    total_row = {
        "Date": today,
        "Ticker": "TOTAL",
        "Shares": "",
        "Buy Price": "",
        "Cost Basis": "",
        "Stop Loss": "",
        "Current Price": "",
        "Total Value": round(total_value, 2),
        "PnL": round(total_pnl, 2),
        "Action": "",
        "Cash Balance": round(cash, 2),
        "Total Equity": round(total_value + cash, 2),
    }
    results.append(total_row)

    df = pd.DataFrame(results)
    if PORTFOLIO_CSV.exists():
        existing = pd.read_csv(PORTFOLIO_CSV)
        existing = existing[existing["Date"] != str(today)]
        print("Saving results to CSV...")
        df = pd.concat([existing, df], ignore_index=True)

    df.to_csv(PORTFOLIO_CSV, index=False)
    return portfolio_df, cash,


def log_sell(
    ticker: str,
    shares: float,
    price: float,
    cost: float,
    pnl: float,
    portfolio: pd.DataFrame,
) -> pd.DataFrame:
    """Record a stop-loss sale in ``TRADE_LOG_CSV`` and remove the ticker."""
    today = check_weekend()
    log = {
        "Date": today,
        "Ticker": ticker,
        "Shares Sold": shares,
        "Sell Price": price,
        "Cost Basis": cost,
        "PnL": pnl,
        "Reason": "AUTOMATED SELL - STOPLOSS TRIGGERED",
    }
    print(f"{ticker} stop loss was met. Selling all shares.")
    portfolio = portfolio[portfolio["ticker"] != ticker]

    if TRADE_LOG_CSV.exists():
        df = pd.read_csv(TRADE_LOG_CSV)
        df = pd.concat([df, pd.DataFrame([log])], ignore_index=True)
    else:
        df = pd.DataFrame([log])
    df.to_csv(TRADE_LOG_CSV, index=False)
    return portfolio


def log_manual_buy(
    buy_price: float,
    shares: float,
    ticker: str,
    stoploss: float,
    cash: float,
    chatgpt_portfolio: pd.DataFrame,
    interactive: bool = True,
) -> tuple[float, pd.DataFrame]:
    """Log a manual purchase and append to the portfolio."""

    today = check_weekend()
    if interactive:
        check = input(
            f"""You are currently trying to buy {shares} shares of {ticker} with a price of {buy_price} and a stoploss of {stoploss}.
        If this a mistake, type "1". """
        )
    
        if check == "1":
            print("Returning...")
            return cash, chatgpt_portfolio

    # Ensure DataFrame exists with required columns
    if not isinstance(chatgpt_portfolio, pd.DataFrame) or chatgpt_portfolio.empty:
        chatgpt_portfolio = pd.DataFrame(columns=["ticker", "shares", "stop_loss", "buy_price", "cost_basis"])

    # Download current market data
    data = download_price_data(ticker, period="1d", auto_adjust=False, progress=False)
    data = cast(pd.DataFrame, data)

    if data.empty:
        print(f"Manual buy for {ticker} failed: no market data available.")
        return cash, chatgpt_portfolio

    day_high = float(data["High"].iloc[-1].item())
    day_low = float(data["Low"].iloc[-1].item())

    if not (day_low <= buy_price <= day_high):
        print(
            f"Manual buy for {ticker} at {buy_price} failed: price outside today's range {round(day_low, 2)}-{round(day_high, 2)}."
        )
        return cash, chatgpt_portfolio

    if buy_price * shares > cash:
        print(
            f"Manual buy for {ticker} failed: cost {buy_price * shares} exceeds cash balance {cash}."
        )
        return cash, chatgpt_portfolio

    # Log trade to trade log CSV
    pnl = 0.0
    log = {
        "Date": today,
        "Ticker": ticker,
        "Shares Bought": shares,
        "Buy Price": buy_price,
        "Cost Basis": buy_price * shares,
        "PnL": pnl,
        "Reason": "MANUAL BUY - New position",
    }

    if os.path.exists(TRADE_LOG_CSV):
        df = pd.read_csv(TRADE_LOG_CSV)
        df = pd.concat([df, pd.DataFrame([log])], ignore_index=True)
    else:
        df = pd.DataFrame([log])
    df.to_csv(TRADE_LOG_CSV, index=False)

    # === Update portfolio DataFrame ===
    rows = chatgpt_portfolio.loc[
        chatgpt_portfolio["ticker"].astype(str).str.upper() == ticker.upper()
    ]

    if rows.empty:
        # New position
        new_trade = {
            "ticker": ticker,
            "shares": float(shares),
            "stop_loss": float(stoploss),
            "buy_price": float(buy_price),
            "cost_basis": float(buy_price * shares),
        }
        chatgpt_portfolio = pd.concat(
            [chatgpt_portfolio, pd.DataFrame([new_trade])], ignore_index=True
        )
    else:
        # Add to existing position — recompute weighted avg price
        idx = rows.index[0]
        cur_shares = float(chatgpt_portfolio.at[idx, "shares"])
        cur_cost = float(chatgpt_portfolio.at[idx, "cost_basis"])

        new_shares = cur_shares + float(shares)
        new_cost = cur_cost + float(buy_price * shares)
        avg_price = new_cost / new_shares if new_shares else 0.0

        chatgpt_portfolio.at[idx, "shares"] = new_shares
        chatgpt_portfolio.at[idx, "cost_basis"] = new_cost
        chatgpt_portfolio.at[idx, "buy_price"] = avg_price
        chatgpt_portfolio.at[idx, "stop_loss"] = float(stoploss)

    # Deduct cash
    cash -= shares * buy_price
    print(f"Manual buy for {ticker} complete!")
    return cash, chatgpt_portfolio



def log_manual_sell(
    sell_price: float,
    shares_sold: float,
    ticker: str,
    cash: float,
    chatgpt_portfolio: pd.DataFrame,
    reason: str | None = None,
    interactive: bool = True,
) -> tuple[float, pd.DataFrame]:
    """Log a manual sale and update the portfolio.

    Parameters
    ----------
    reason:
        Description of why the position is being sold. Ignored when
        ``interactive`` is ``True``.
    interactive:
        When ``False`` no interactive confirmation is requested.
    """
    today = check_weekend()
    if interactive:
        reason = input(
            f"""You are currently trying to sell {shares_sold} shares of {ticker} at a price of {sell_price}.
If this is a mistake, enter 1. """
        )

    if reason == "1":
        print("Returning...")
        return cash, chatgpt_portfolio
    elif reason is None:
        reason = ""
    if ticker not in chatgpt_portfolio["ticker"].values:
        print(f"Manual sell for {ticker} failed: ticker not in portfolio.")
        return cash, chatgpt_portfolio
    ticker_row = chatgpt_portfolio[chatgpt_portfolio["ticker"] == ticker]

    total_shares = int(ticker_row["shares"].item())
    if shares_sold > total_shares:
        print(
            f"Manual sell for {ticker} failed: trying to sell {shares_sold} shares but only own {total_shares}."
        )
        return cash, chatgpt_portfolio
    data = download_price_data(ticker, period="1d")
    data = cast(pd.DataFrame, data)
    if data.empty:
        print(f"Manual sell for {ticker} failed: no market data available.")
        return cash, chatgpt_portfolio
    day_high = float(data["High"].iloc[-1])
    day_low = float(data["Low"].iloc[-1])
    if not (day_low <= sell_price <= day_high):
        print(
            f"Manual sell for {ticker} at {sell_price} failed: price outside today's range {round(day_low, 2)}-{round(day_high, 2)}."
        )
        return cash, chatgpt_portfolio
    buy_price = float(ticker_row["buy_price"].item())
    cost_basis = buy_price * shares_sold
    pnl = sell_price * shares_sold - cost_basis
    log = {
        "Date": today,
        "Ticker": ticker,
        "Shares Bought": "",
        "Buy Price": "",
        "Cost Basis": cost_basis,
        "PnL": pnl,
        "Reason": f"MANUAL SELL - {reason}",
        "Shares Sold": shares_sold,
        "Sell Price": sell_price,
    }
    if os.path.exists(TRADE_LOG_CSV):
        df = pd.read_csv(TRADE_LOG_CSV)
        df = pd.concat([df, pd.DataFrame([log])], ignore_index=True)
    else:
        df = pd.DataFrame([log])
    df.to_csv(TRADE_LOG_CSV, index=False)

    if total_shares == shares_sold:
        chatgpt_portfolio = chatgpt_portfolio[chatgpt_portfolio["ticker"] != ticker]
    else:
        row_index = ticker_row.index[0]
        chatgpt_portfolio.at[row_index, "shares"] = total_shares - shares_sold
        chatgpt_portfolio.at[row_index, "cost_basis"] = (
            chatgpt_portfolio.at[row_index, "shares"]
            * chatgpt_portfolio.at[row_index, "buy_price"]
        )

    cash = cash + shares_sold * sell_price
    print(f"manual sell for {ticker} complete!")
    return cash, chatgpt_portfolio


def daily_results(chatgpt_portfolio: pd.DataFrame, cash: float) -> None:
    """Print daily price updates and performance metrics (incl. Beta & Alpha) with neat formatting."""
    portfolio_dict: list[dict[str, object]] = chatgpt_portfolio.to_dict(orient="records")

    today = check_weekend()

    # -------- Collect daily ticker updates (pretty table) --------
    rows = []
    header = ["Ticker", "Close", "% Chg", "Volume"]
    for stock in portfolio_dict + [{"ticker": "^RUT"}, {"ticker": "IWO"}, {"ticker": "XBI"}]:
        ticker = stock["ticker"]
        try:
            data = download_price_data(ticker, period="2d", progress=False, auto_adjust=True)
            data = cast(pd.DataFrame, data)
            if data.empty or len(data) < 2:
                rows.append([ticker, "—", "—", "—"])
                continue

            # Use .item() to avoid FutureWarning
            price = data["Close"].iloc[-1]
            last_price = data["Close"].iloc[-2]
            volume = data["Volume"].iloc[-1]

            price = float(price.item() if hasattr(price, "item") else float(price))
            last_price = float(last_price.item() if hasattr(last_price, "item") else float(last_price))
            volume = float(volume.item() if hasattr(volume, "item") else float(volume))

            percent_change = ((price - last_price) / last_price) * 100
            rows.append([ticker, f"{price:,.2f}", f"{percent_change:+.2f}%", f"{int(volume):,}"])
        except Exception as e:
            raise Exception(f"Download for {ticker} failed. {e} Try checking internet connection.")

    # Read portfolio history
    chatgpt_df = pd.read_csv(PORTFOLIO_CSV)

    # Use only TOTAL rows, sorted by date
    totals = chatgpt_df[chatgpt_df["Ticker"] == "TOTAL"].copy()
    starting_equity = float(totals.loc[totals.index[0],"Total Equity"])
    if totals.empty:
        # Minimal report if no totals yet
        print("\n" + "=" * 64)
        print(f"Daily Results — {today}")
        print("=" * 64)
        print("\n[ Price & Volume ]")
        colw = [10, 12, 9, 15]
        print(f"{header[0]:<{colw[0]}} {header[1]:>{colw[1]}} {header[2]:>{colw[2]}} {header[3]:>{colw[3]}}")
        print("-" * sum(colw) + "-" * 3)
        for r in rows:
            print(f"{str(r[0]):<{colw[0]}} {str(r[1]):>{colw[1]}} {str(r[2]):>{colw[2]}} {str(r[3]):>{colw[3]}}")
        print("\n[ Portfolio Snapshot ]")
        print(chatgpt_portfolio)
        print(f"Cash balance: ${cash:,.2f}")
        return

    totals["Date"] = pd.to_datetime(totals["Date"])
    totals = totals.sort_values("Date")

    final_equity = float(totals.iloc[-1]["Total Equity"])
    equity_series = totals.set_index("Date")["Total Equity"].astype(float).sort_index()

    # --- Max Drawdown ---
    running_max = equity_series.cummax()
    drawdowns = (equity_series / running_max) - 1.0
    max_drawdown = drawdowns.min()  # most negative value
    mdd_date = drawdowns.idxmin()

    # Daily simple returns (portfolio)
    r = equity_series.pct_change().dropna()
    n_days = len(r)
    if n_days < 2:
        print("\n" + "=" * 64)
        print(f"Daily Results — {today}")
        print("=" * 64)
        print("\n[ Price & Volume ]")
        colw = [10, 12, 9, 15]
        print(f"{header[0]:<{colw[0]}} {header[1]:>{colw[1]}} {header[2]:>{colw[2]}} {header[3]:>{colw[3]}}")
        print("-" * sum(colw) + "-" * 3)
        for rrow in rows:
            print(f"{str(rrow[0]):<{colw[0]}} {str(rrow[1]):>{colw[1]}} {str(rrow[2]):>{colw[2]}} {str(rrow[3]):>{colw[3]}}")
        print("\n[ Portfolio Snapshot ]")
        print(chatgpt_portfolio)
        print(f"Cash balance: ${cash:,.2f}")
        print(f"Latest ChatGPT Equity: ${final_equity:,.2f}")
        print(f"Maximum Drawdown: {max_drawdown:.2%} (on {mdd_date.date()})")
        return

    # Risk-free config
    rf_annual = 0.045
    rf_daily = (1 + rf_annual) ** (1 / 252) - 1
    rf_period = (1 + rf_daily) ** n_days - 1

    # Stats
    mean_daily = r.mean()
    std_daily = r.std(ddof=1)

    # Downside deviation (MAR = rf_daily)
    downside = (r - rf_daily).clip(upper=0)
    downside_std = float((downside.pow(2).mean()) ** 0.5) if not downside.empty else np.nan

    # Total return over the window
    period_return = float((1 + r).prod() - 1)

    # Sharpe / Sortino
    sharpe_period = (period_return - rf_period) / (std_daily * np.sqrt(n_days)) if std_daily > 0 else np.nan
    sharpe_annual = ((mean_daily - rf_daily) / std_daily) * np.sqrt(252) if std_daily > 0 else np.nan
    sortino_period = (period_return - rf_period) / (downside_std * np.sqrt(n_days)) if downside_std and downside_std > 0 else np.nan
    sortino_annual = ((mean_daily - rf_daily) / downside_std) * np.sqrt(252) if downside_std and downside_std > 0 else np.nan

    # -------- CAPM: Beta & Alpha (vs ^GSPC) --------
    start_date = equity_series.index.min() - pd.Timedelta(days=1)
    end_date = equity_series.index.max() + pd.Timedelta(days=1)

    spx = download_price_data("^GSPC", start=start_date, end=end_date, progress=False, auto_adjust=True)
    spx = cast(pd.DataFrame, spx)

    beta = np.nan
    alpha_annual = np.nan
    r2 = np.nan
    n_obs = 0

    if not spx.empty and len(spx) >= 2:
        spx = spx.reset_index().set_index("Date").sort_index()
        mkt_ret = spx["Close"].astype(float).pct_change().dropna()

        # Align portfolio & market returns
        common_idx = r.index.intersection(mkt_ret.index)
        if len(common_idx) >= 2:
            rp = (r.reindex(common_idx).astype(float) - rf_daily)   # portfolio excess
            rm = (mkt_ret.reindex(common_idx).astype(float) - rf_daily)  # market excess

            # Ensure 1-D numpy arrays
            x = np.asarray(rm.values, dtype=float).ravel()
            y = np.asarray(rp.values, dtype=float).ravel()

            n_obs = x.size
            rm_std = float(np.std(x, ddof=1)) if n_obs > 1 else 0.0
            if rm_std > 0:
                # OLS: y = beta * x + alpha_daily
                beta, alpha_daily = np.polyfit(x, y, 1)
                alpha_annual = (1 + float(alpha_daily)) ** 252 - 1

                # Compute R²
                corr = np.corrcoef(x, y)[0, 1]
                r2 = float(corr ** 2)

    # $100 normalized S&P 500 over same window
    spx_norm = download_price_data("^GSPC",
                           start=equity_series.index.min(),
                           end=equity_series.index.max() + pd.Timedelta(days=1),
                           progress=False, auto_adjust=True)
    spx_norm = cast(pd.DataFrame, spx_norm)
    spx_value = np.nan
    if not spx_norm.empty:
        initial_price = spx_norm["Close"].iloc[0]
        price_now = spx_norm["Close"].iloc[-1]
        initial_price = float(initial_price.item() if hasattr(initial_price, "item") else float(initial_price))
        price_now = float(price_now.item() if hasattr(price_now, "item") else float(price_now))
        starting_equity = float(input("what was your starting equity? "))
        spx_value = (starting_equity / initial_price) * price_now

    # -------- Pretty Printing --------
    print("\n" + "=" * 64)
    print(f"Daily Results — {today}")
    print("=" * 64)

    # Price & Volume table
    print("\n[ Price & Volume ]")
    colw = [10, 12, 9, 15]
    print(f"{header[0]:<{colw[0]}} {header[1]:>{colw[1]}} {header[2]:>{colw[2]}} {header[3]:>{colw[3]}}")
    print("-" * sum(colw) + "-" * 3)
    for rrow in rows:
        print(f"{str(rrow[0]):<{colw[0]}} {str(rrow[1]):>{colw[1]}} {str(rrow[2]):>{colw[2]}} {str(rrow[3]):>{colw[3]}}")

    # Performance metrics
    def fmt_or_na(x, fmt):
        return (fmt.format(x) if not (x is None or (isinstance(x, float) and np.isnan(x))) else "N/A")

    print("\n[ Risk & Return ]")
    print(f"{'Max Drawdown:':32} {fmt_or_na(max_drawdown, '{:.2%}'):>15}   on {mdd_date.date()}")
    print(f"{'Sharpe Ratio (period):':32} {fmt_or_na(sharpe_period, '{:.4f}'):>15}")
    print(f"{'Sharpe Ratio (annualized):':32} {fmt_or_na(sharpe_annual, '{:.4f}'):>15}")
    print(f"{'Sortino Ratio (period):':32} {fmt_or_na(sortino_period, '{:.4f}'):>15}")
    print(f"{'Sortino Ratio (annualized):':32} {fmt_or_na(sortino_annual, '{:.4f}'):>15}")

    print("\n[ CAPM vs Benchmarks ]")
    if not np.isnan(beta):
        print(f"{'Beta (daily) vs ^GSPC:':32} {beta:>15.4f}")
        print(f"{'Alpha (annualized) vs ^GSPC:':32} {alpha_annual:>15.2%}")
        print(f"{'R² (fit quality):':32} {r2:>15.3f}   {'Obs:':>6} {n_obs}")
        if n_obs < 60 or (not np.isnan(r2) and r2 < 0.20):
            print("  Note: Short sample and/or low R² — alpha/beta may be unstable.")
    else:
        print("Beta/Alpha: insufficient overlapping data.")

    print("\n[ Snapshot ]")
    print(f"{'Latest ChatGPT Equity:':32} ${final_equity:>14,.2f}")
    if not np.isnan(spx_value):
        print(f"{f'${starting_equity} in S&P 500 (same window):':32} ${spx_value:>14,.2f}")

    print(f"{'Cash Balance:':32} ${cash:>14,.2f}")

    print("\n[ Holdings ]")
    print(chatgpt_portfolio)

    print("\n[ Operator Note ]")
    print(
        "You have complete control over every decision. Make any changes you believe are beneficial—no approval required.\n"
        "Deep research is not permitted. Act at your discretion to achieve the best outcome.\n"
        "If you do not make a clear indication to change positions immediately after this message, the portfolio remains unchanged for tomorrow.\n"
        "You are encouraged to use the internet to check current prices (and related up-to-date info) for potential buys.\n"
        "*Paste everything above into ChatGPT*"
    )




def main(file: str, data_dir: Path | None = None) -> None:
    """Check verisons, then run the trading script.

    Parameters
    ----------
    file:
        CSV file containing historical portfolio records.
    data_dir:
        Directory where trade and portfolio CSVs will be stored.
    """
    check_versions()
    chatgpt_portfolio, cash = load_latest_portfolio_state(file)
    print(file)
    if data_dir is not None:
        set_data_dir(data_dir)

    chatgpt_portfolio, cash = process_portfolio(chatgpt_portfolio, cash)
    daily_results(chatgpt_portfolio, cash)

def load_latest_portfolio_state(
    file: str,
) -> tuple[pd.DataFrame | list[dict[str, Any]], float]:
    """Load the most recent portfolio snapshot and cash balance.

    Parameters
    ----------
    file:
        CSV file containing historical portfolio records.

    Returns
    -------
    tuple[pd.DataFrame | list[dict[str, Any]], float]
        A representation of the latest holdings (either an empty DataFrame or a
        list of row dictionaries) and the associated cash balance.
    """

    df = pd.read_csv(file)
    if df.empty:
        portfolio = pd.DataFrame([])
        print(
            "Portfolio CSV is empty. Returning set amount of cash for creating portfolio."
        )
        try:
            cash = float(input("What would you like your starting cash amount to be? "))
        except ValueError:
            raise ValueError(
                "Cash could not be converted to float datatype. Please enter a valid number."
            )
        return portfolio, cash
    non_total = df[df["Ticker"] != "TOTAL"].copy()
    non_total["Date"] = pd.to_datetime(non_total["Date"])

    latest_date = non_total["Date"].max()
    # Get all tickers from the latest date
    latest_tickers = non_total[non_total["Date"] == latest_date].copy()
    sold_mask = latest_tickers["Action"].astype(str).str.startswith("SELL")
    latest_tickers = latest_tickers[~sold_mask].copy()
    latest_tickers.drop(columns=["Date", "Cash Balance", "Total Equity", "Action", "Current Price", "PnL", "Total Value"], inplace=True)
    latest_tickers.rename(columns={"Cost Basis": "cost_basis", "Buy Price": "buy_price", "Shares": "shares", "Ticker": "ticker", "Stop Loss": "stop_loss"}, inplace=True)
    latest_tickers = latest_tickers.reset_index(drop=True).to_dict(orient='records')
    df = df[df["Ticker"] == "TOTAL"]  # Only the total summary rows
    df["Date"] = pd.to_datetime(df["Date"])
    latest = df.sort_values("Date").iloc[-1]
    cash = float(latest["Cash Balance"])
    return latest_tickers, cash

