#!/usr/bin/env python3
r"""
trading_script.py — Robust interactive logger/valuator for a tiny micro-cap portfolio.

Key improvements vs the basic script:
- Holiday-aware "last trading day" via SPY probe (so Labor Day etc. won't break price fetch)
- Yahoo 'recent' fallback: if a date-bounded fetch is empty, use the most recent bar (<= end)
- Multi-source OHLCV with fallbacks: Yahoo -> Stooq (pandas-datareader) -> Stooq CSV -> proxy
- Full-share enforcement (accepts "3.00", rejects "3.5")
- Consistent CSV schema with trade log and portfolio snapshot

Dependencies:
  pip install pandas numpy yfinance pandas-datareader requests

Usage examples:
  python trading_script.py --file "Start Your Own/chatgpt_portfolio_update.csv"
  python trading_script.py --file path/to/chatgpt_portfolio_update.csv --asof 2025-08-29

CSV files:
  chatgpt_portfolio_update.csv  (rolling snapshots + TOTAL row per day)
  chatgpt_trade_log.csv         (append-only trade log)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, cast, Dict, List, Optional
import os
import warnings
import logging
import json

import numpy as np
import pandas as pd
import yfinance as yf

# Optional pandas-datareader (Stooq)
try:
    import pandas_datareader.data as pdr  # noqa: F401
    _HAS_PDR = True
except Exception:
    _HAS_PDR = False

# ------------------------------
# Globals / paths
# ------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR
PORTFOLIO_CSV = DATA_DIR / "chatgpt_portfolio_update.csv"
TRADE_LOG_CSV = DATA_DIR / "chatgpt_trade_log.csv"
DEFAULT_BENCHMARKS = ["IWO", "XBI", "SPY", "IWM"]

logger = logging.getLogger(__name__)

# ------------------------------
# AS-OF override
# ------------------------------
ASOF_DATE: pd.Timestamp | None = None

def set_asof(date: str | datetime | pd.Timestamp | None) -> None:
    """Force the script to treat a specific date as 'today' (YYYY-MM-DD)."""
    global ASOF_DATE
    if date is None:
        print("No prior date passed. Using today's date...")
        ASOF_DATE = None
        return
    ASOF_DATE = pd.Timestamp(date).normalize()
    print(f"Setting date as {ASOF_DATE.date()}.")

_env_asof = os.environ.get("ASOF_DATE")
if _env_asof:
    set_asof(_env_asof)

def _effective_now() -> datetime:
    return (ASOF_DATE.to_pydatetime() if ASOF_DATE is not None else datetime.now())

# ------------------------------
# Benchmarks config
# ------------------------------

def _read_json_file(path: Path) -> Optional[Dict]:
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as exc:
        logger.warning("tickers.json present but malformed: %s -> %s. Falling back to defaults.", path, exc)
        return None
    except Exception as exc:
        logger.warning("Unable to read tickers.json (%s): %s. Falling back to defaults.", path, exc)
        return None

def load_benchmarks(script_dir: Path | None = None) -> List[str]:
    base = Path(script_dir) if script_dir else SCRIPT_DIR
    candidates = [base, base.parent]

    cfg = None
    cfg_path = None
    for c in candidates:
        p = (c / "tickers.json").resolve()
        data = _read_json_file(p)
        if data is not None:
            cfg = data
            cfg_path = p
            break

    if not cfg:
        return DEFAULT_BENCHMARKS.copy()

    benchmarks = cfg.get("benchmarks")
    if not isinstance(benchmarks, list):
        logger.warning("tickers.json at %s missing 'benchmarks' array. Falling back to defaults.", cfg_path)
        return DEFAULT_BENCHMARKS.copy()

    seen = set()
    result: list[str] = []
    for t in benchmarks:
        if not isinstance(t, str):
            continue
        up = t.strip().upper()
        if not up:
            continue
        if up not in seen:
            seen.add(up)
            result.append(up)
    return result if result else DEFAULT_BENCHMARKS.copy()

# ------------------------------
# Date helpers (holiday-aware)
# ------------------------------

def _weekend_only_last_trading_date(today: datetime | None = None) -> pd.Timestamp:
    dt = pd.Timestamp(today or _effective_now())
    if dt.weekday() == 5:  # Sat -> Fri
        return (dt - pd.Timedelta(days=1)).normalize()
    if dt.weekday() == 6:  # Sun -> Fri
        return (dt - pd.Timedelta(days=2)).normalize()
    return dt.normalize()

def last_trading_date(today: datetime | None = None) -> pd.Timestamp:
    """
    Try to infer the most recent U.S. market session using SPY's last
    available daily bar <= 'today'. Falls back to weekend mapping.
    """
    ref = pd.Timestamp(today or _effective_now()).normalize()
    try:
        df = yf.download("SPY", period="10d", interval="1d", progress=False, threads=False, auto_adjust=False)
        if isinstance(df, pd.DataFrame) and not df.empty:
            if not isinstance(df.index, pd.DatetimeIndex):
                df.index = pd.to_datetime(df.index)
            df = df.sort_index()
            idx = df.index[df.index <= ref]
            if len(idx) > 0:
                return idx[-1].normalize()
    except Exception:
        pass
    return _weekend_only_last_trading_date(ref)

def check_weekend() -> str:
    return last_trading_date().date().isoformat()

def trading_day_window(target: datetime | None = None) -> tuple[pd.Timestamp, pd.Timestamp]:
    d = last_trading_date(target)
    return d, (d + pd.Timedelta(days=1))

# ------------------------------
# Data access layer
# ------------------------------

STOOQ_MAP = {
    "^GSPC": "^SPX",
    "^DJI": "^DJI",
    "^IXIC": "^IXIC",
}
STOOQ_BLOCKLIST = {"^RUT"}

@dataclass
class FetchResult:
    df: pd.DataFrame
    source: str  # "yahoo" | "yahoo:recent" | "stooq-pdr" | "stooq-csv" | "yahoo:<proxy>-proxy" | "empty"

def _to_datetime_index(df: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(df.index, pd.DatetimeIndex):
        try:
            df.index = pd.to_datetime(df.index)
        except Exception:
            pass
    return df

def _normalize_ohlcv(df: pd.DataFrame) -> pd.DataFrame:
    for c in ["Open", "High", "Low", "Close", "Volume"]:
        if c not in df.columns:
            df[c] = np.nan
    if "Adj Close" not in df.columns:
        df["Adj Close"] = df["Close"]
    return df[["Open", "High", "Low", "Close", "Adj Close", "Volume"]]

def _yahoo_download(ticker: str, **kwargs: Any) -> pd.DataFrame:
    import io, requests
    from contextlib import redirect_stderr, redirect_stdout

    sess = requests.Session()
    sess.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    kwargs.setdefault("progress", False)
    kwargs.setdefault("threads", False)
    kwargs.setdefault("session", sess)

    buf = io.StringIO()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            with redirect_stdout(buf), redirect_stderr(buf):
                df = cast(pd.DataFrame, yf.download(ticker, **kwargs))
        except Exception:
            return pd.DataFrame()
    return df if isinstance(df, pd.DataFrame) else pd.DataFrame()

def _stooq_csv_download(ticker: str, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    import requests, io
    if ticker in STOOQ_BLOCKLIST:
        return pd.DataFrame()
    t = STOOQ_MAP.get(ticker, ticker)

    if not t.startswith("^"):
        sym = t.lower()
        if not sym.endswith(".us"):
            sym = f"{sym}.us"
    else:
        sym = t.lower()

    url = f"https://stooq.com/q/d/l/?s={sym}&i=d"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code != 200 or not r.text.strip():
            return pd.DataFrame()
        df = pd.read_csv(io.StringIO(r.text))
        if df.empty:
            return pd.DataFrame()
        df["Date"] = pd.to_datetime(df["Date"])
        df.set_index("Date", inplace=True)
        df.sort_index(inplace=True)
        df = df.loc[(df.index >= start.normalize()) & (df.index < end.normalize())]
        if "Adj Close" not in df.columns:
            df["Adj Close"] = df["Close"]
        return df[["Open", "High", "Low", "Close", "Adj Close", "Volume"]]
    except Exception:
        return pd.DataFrame()

def _stooq_download(ticker: str, start: datetime | pd.Timestamp, end: datetime | pd.Timestamp) -> pd.DataFrame:
    if not _HAS_PDR or ticker in STOOQ_BLOCKLIST:
        return pd.DataFrame()
    t = STOOQ_MAP.get(ticker, ticker)
    if not t.startswith("^"):
        t = t.lower()
    try:
        import pandas_datareader.data as pdr_local
        df = cast(pd.DataFrame, pdr_local.DataReader(t, "stooq", start=start, end=end))
        df.sort_index(inplace=True)
        return df
    except Exception:
        return pd.DataFrame()

def _weekend_safe_range(period: str | None, start: Any, end: Any) -> tuple[pd.Timestamp, pd.Timestamp]:
    if start or end:
        end_ts = pd.Timestamp(end) if end else last_trading_date() + pd.Timedelta(days=1)
        start_ts = pd.Timestamp(start) if start else (end_ts - pd.Timedelta(days=5))
        return start_ts.normalize(), pd.Timestamp(end_ts).normalize()

    if isinstance(period, str) and period.endswith("d"):
        days = int(period[:-1])
    else:
        days = 1

    end_trading = last_trading_date()
    start_ts = (end_trading - pd.Timedelta(days=days)).normalize()
    end_ts = (end_trading + pd.Timedelta(days=1)).normalize()
    return start_ts, end_ts

def download_price_data(ticker: str, **kwargs: Any) -> FetchResult:
    """
    OHLCV with fallbacks:
      1) Yahoo (date-bounded)
      1b) Yahoo 'recent' (period=10d) -> last bar < end
      2) Stooq via pandas-datareader
      3) Stooq direct CSV
      4) Proxy (^GSPC->SPY, ^RUT->IWM) via Yahoo
    """
    period = kwargs.pop("period", None)
    start = kwargs.pop("start", None)
    end = kwargs.pop("end", None)
    kwargs.setdefault("progress", False)
    kwargs.setdefault("threads", False)

    s, e = _weekend_safe_range(period, start, end)

    # 1) Yahoo with explicit range
    df_y = _yahoo_download(ticker, start=s, end=e, **kwargs)
    if isinstance(df_y, pd.DataFrame) and not df_y.empty:
        return FetchResult(_normalize_ohlcv(_to_datetime_index(df_y)), "yahoo")

    # 1b) Yahoo recent fallback
    try:
        df_recent = _yahoo_download(ticker, period="10d", interval="1d")
        if isinstance(df_recent, pd.DataFrame) and not df_recent.empty:
            df_recent = _to_datetime_index(df_recent).sort_index()
            df_recent = df_recent.loc[df_recent.index < e]
            if not df_recent.empty:
                last_bar = df_recent.tail(1)
                return FetchResult(_normalize_ohlcv(last_bar), "yahoo:recent")
    except Exception:
        pass

    # 2) Stooq via pandas-datareader
    df_s = _stooq_download(ticker, start=s, end=e)
    if isinstance(df_s, pd.DataFrame) and not df_s.empty:
        return FetchResult(_normalize_ohlcv(_to_datetime_index(df_s)), "stooq-pdr")

    # 3) Stooq CSV
    df_csv = _stooq_csv_download(ticker, s, e)
    if isinstance(df_csv, pd.DataFrame) and not df_csv.empty:
        return FetchResult(_normalize_ohlcv(_to_datetime_index(df_csv)), "stooq-csv")

    # 4) Proxy
    proxy_map = {"^GSPC": "SPY", "^RUT": "IWM"}
    proxy = proxy_map.get(ticker)
    if proxy:
        df_proxy = _yahoo_download(proxy, start=s, end=e, **kwargs)
        if isinstance(df_proxy, pd.DataFrame) and not df_proxy.empty:
            return FetchResult(_normalize_ohlcv(_to_datetime_index(df_proxy)), f"yahoo:{proxy}-proxy")

    empty = pd.DataFrame(columns=["Open", "High", "Low", "Close", "Adj Close", "Volume"])
    return FetchResult(empty, "empty")

# ------------------------------
# File path configuration
# ------------------------------

def set_data_dir(data_dir: Path) -> None:
    global DATA_DIR, PORTFOLIO_CSV, TRADE_LOG_CSV
    DATA_DIR = Path(data_dir)
    os.makedirs(DATA_DIR, exist_ok=True)
    PORTFOLIO_CSV = DATA_DIR / "chatgpt_portfolio_update.csv"
    TRADE_LOG_CSV = DATA_DIR / "chatgpt_trade_log.csv"

# ------------------------------
# Portfolio operations
# ------------------------------

def _ensure_df(portfolio: pd.DataFrame | dict[str, list[object]] | list[dict[str, object]]) -> pd.DataFrame:
    if isinstance(portfolio, pd.DataFrame):
        return portfolio.copy()
    if isinstance(portfolio, (dict, list)):
        return pd.DataFrame(portfolio)
    raise TypeError("portfolio must be a DataFrame, dict, or list[dict]")

def process_portfolio(
    portfolio: pd.DataFrame | dict[str, list[object]] | list[dict[str, object]],
    cash: float,
    interactive: bool = True,
) -> tuple[pd.DataFrame, float]:
    today_iso = last_trading_date().date().isoformat()
    portfolio_df = _ensure_df(portfolio)

    results: list[dict[str, object]] = []
    total_value = 0.0
    total_pnl = 0.0

    # ------- Interactive trade entry -------
    if interactive:
        while True:
            print(portfolio_df)
            action = input(
                f""" You have {cash} in cash.
Would you like to log a manual trade? Enter 'b' for buy, 's' for sell, or press Enter to continue: """
            ).strip().lower()

            if action == "b":
                ticker = input("Enter ticker symbol: ").strip().upper()
                order_type = input("Order type? 'm' = market-on-open, 'l' = limit: ").strip().lower()

                # Full-share enforcement (accepts "3.00", rejects "3.5")
                try:
                    shares_txt = input("Enter number of shares: ").strip()
                    shares_f = float(shares_txt)
                    shares = int(round(shares_f))
                    if shares <= 0 or abs(shares_f - shares) > 1e-9:
                        raise ValueError
                except ValueError:
                    print("Invalid share amount (full shares only). Buy cancelled.")
                    continue

                if order_type == "m":
                    try:
                        stop_loss = float(input("Enter stop loss (or 0 to skip): "))
                        if stop_loss < 0:
                            raise ValueError
                    except ValueError:
                        print("Invalid stop loss. Buy cancelled.")
                        continue

                    s, e = trading_day_window()
                    fetch = download_price_data(ticker, start=s, end=e, auto_adjust=False, progress=False)
                    data = fetch.df
                    if data.empty:
                        print(f"MOO buy for {ticker} failed: no market data available (source={fetch.source}).")
                        continue

                    o = float(data["Open"].iloc[-1]) if "Open" in data else float(data["Close"].iloc[-1])
                    exec_price = round(o, 2)
                    notional = exec_price * shares
                    if notional > cash:
                        print(f"MOO buy for {ticker} failed: cost {notional:.2f} exceeds cash {cash:.2f}.")
                        continue

                    log = {
                        "Date": today_iso,
                        "Ticker": ticker,
                        "Shares Bought": shares,
                        "Buy Price": exec_price,
                        "Cost Basis": notional,
                        "PnL": 0.0,
                        "Reason": "MANUAL BUY MOO - Filled",
                    }
                    # Append to trade log
                    if os.path.exists(TRADE_LOG_CSV):
                        df_log = pd.read_csv(TRADE_LOG_CSV)
                        df_log = pd.concat([df_log, pd.DataFrame([log])], ignore_index=True)
                    else:
                        df_log = pd.DataFrame([log])
                    df_log.to_csv(TRADE_LOG_CSV, index=False)

                    # Update portfolio
                    rows = portfolio_df.loc[portfolio_df["ticker"].astype(str).str.upper() == ticker.upper()]
                    if rows.empty:
                        new_trade = {
                            "ticker": ticker,
                            "shares": float(shares),
                            "stop_loss": float(stop_loss),
                            "buy_price": float(exec_price),
                            "cost_basis": float(notional),
                        }
                        portfolio_df = pd.concat([portfolio_df, pd.DataFrame([new_trade])], ignore_index=True) if not portfolio_df.empty else pd.DataFrame([new_trade])
                    else:
                        idx = rows.index[0]
                        cur_shares = float(portfolio_df.at[idx, "shares"])
                        cur_cost = float(portfolio_df.at[idx, "cost_basis"])
                        new_shares = cur_shares + float(shares)
                        new_cost = cur_cost + float(notional)
                        avg_price = new_cost / new_shares if new_shares else 0.0
                        portfolio_df.at[idx, "shares"] = new_shares
                        portfolio_df.at[idx, "cost_basis"] = new_cost
                        portfolio_df.at[idx, "buy_price"] = avg_price
                        portfolio_df.at[idx, "stop_loss"] = float(stop_loss)

                    cash -= notional
                    print(f"Manual BUY MOO for {ticker} filled at ${exec_price:.2f} ({fetch.source}).")
                    continue

                elif order_type == "l":
                    try:
                        buy_price = float(input("Enter buy LIMIT price: "))
                        stop_loss = float(input("Enter stop loss (or 0 to skip): "))
                        if buy_price <= 0 or stop_loss < 0:
                            raise ValueError
                    except ValueError:
                        print("Invalid input. Limit buy cancelled.")
                        continue

                    cash, portfolio_df = log_manual_buy(
                        buy_price, shares, ticker, stop_loss, cash, portfolio_df
                    )
                    continue
                else:
                    print("Unknown order type. Use 'm' or 'l'.")
                    continue

            if action == "s":
                try:
                    ticker = input("Enter ticker symbol: ").strip().upper()
                    shares_txt = input("Enter number of shares to sell (LIMIT): ").strip()
                    shares_f = float(shares_txt)
                    shares_sold = int(round(shares_f))
                    if shares_sold <= 0 or abs(shares_f - shares_sold) > 1e-9:
                        raise ValueError
                    sell_price = float(input("Enter sell LIMIT price: "))
                    if sell_price <= 0:
                        raise ValueError
                except ValueError:
                    print("Invalid input. Manual sell cancelled.")
                    continue

                cash, portfolio_df = log_manual_sell(
                    sell_price, shares_sold, ticker, cash, portfolio_df
                )
                continue

            break  # proceed to pricing

    # ------- Daily pricing + stop-loss execution -------
    s, e = trading_day_window()
    for _, stock in portfolio_df.iterrows():
        ticker = str(stock["ticker"]).upper()
        shares = int(stock["shares"]) if not pd.isna(stock["shares"]) else 0
        cost = float(stock["buy_price"]) if not pd.isna(stock["buy_price"]) else 0.0
        cost_basis = float(stock["cost_basis"]) if not pd.isna(stock["cost_basis"]) else cost * shares
        stop = float(stock["stop_loss"]) if not pd.isna(stock["stop_loss"]) else 0.0

        fetch = download_price_data(ticker, start=s, end=e, auto_adjust=False, progress=False)
        data = fetch.df

        if data.empty:
            print(f"No data for {ticker} (source={fetch.source}).")
            row = {
                "Date": today_iso, "Ticker": ticker, "Shares": shares,
                "Buy Price": cost, "Cost Basis": cost_basis, "Stop Loss": stop,
                "Current Price": "", "Total Value": "", "PnL": "",
                "Action": "NO DATA", "Cash Balance": "", "Total Equity": "",
            }
            results.append(row)
            continue

        o = float(data["Open"].iloc[-1]) if "Open" in data else np.nan
        h = float(data["High"].iloc[-1])
        l = float(data["Low"].iloc[-1])
        c = float(data["Close"].iloc[-1])
        if np.isnan(o):
            o = c

        if stop and l <= stop:
            exec_price = round(o if o <= stop else stop, 2)
            value = round(exec_price * shares, 2)
            pnl = round((exec_price - cost) * shares, 2)
            action = "SELL - Stop Loss Triggered"
            cash += value
            portfolio_df = log_sell(ticker, shares, exec_price, cost, pnl, portfolio_df)
            row = {
                "Date": today_iso, "Ticker": ticker, "Shares": shares,
                "Buy Price": cost, "Cost Basis": cost_basis, "Stop Loss": stop,
                "Current Price": exec_price, "Total Value": value, "PnL": pnl,
                "Action": action, "Cash Balance": "", "Total Equity": "",
            }
        else:
            price = round(c, 2)
            value = round(price * shares, 2)
            pnl = round((price - cost) * shares, 2)
            action = "HOLD"
            total_value += value
            total_pnl += pnl
            row = {
                "Date": today_iso, "Ticker": ticker, "Shares": shares,
                "Buy Price": cost, "Cost Basis": cost_basis, "Stop Loss": stop,
                "Current Price": price, "Total Value": value, "PnL": pnl,
                "Action": action, "Cash Balance": "", "Total Equity": "",
            }

        results.append(row)

    total_row = {
        "Date": today_iso, "Ticker": "TOTAL", "Shares": "", "Buy Price": "",
        "Cost Basis": "", "Stop Loss": "", "Current Price": "",
        "Total Value": round(total_value, 2), "PnL": round(total_pnl, 2),
        "Action": "", "Cash Balance": round(cash, 2),
        "Total Equity": round(total_value + cash, 2),
    }
    results.append(total_row)

    df_out = pd.DataFrame(results)
    # Load existing and drop any rows for today, then append
    if PORTFOLIO_CSV.exists():
        try:
            existing = pd.read_csv(PORTFOLIO_CSV)
            existing = existing[existing["Date"] != str(today_iso)]
            df_out = pd.concat([existing, df_out], ignore_index=True)
        except Exception:
            pass
    print("Saving results to CSV...")
    df_out.to_csv(PORTFOLIO_CSV, index=False)

    return portfolio_df, cash

# ------------------------------
# Trade logging
# ------------------------------

def log_sell(
    ticker: str,
    shares: float,
    price: float,
    cost: float,
    pnl: float,
    portfolio: pd.DataFrame,
) -> pd.DataFrame:
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
    today = check_weekend()

    # Full-share enforcement
    shares = int(round(shares))
    if shares <= 0:
        print("Invalid shares (must be positive integer).")
        return cash, chatgpt_portfolio

    if interactive:
        check = input(
            f"You are placing a BUY LIMIT for {shares} {ticker} at ${buy_price:.2f}.\n"
            f"If this is a mistake, type '1': "
        )
        if check == "1":
            print("Returning...")
            return cash, chatgpt_portfolio

    if not isinstance(chatgpt_portfolio, pd.DataFrame) or chatgpt_portfolio.empty:
        chatgpt_portfolio = pd.DataFrame(
            columns=["ticker", "shares", "stop_loss", "buy_price", "cost_basis"]
        )

    s, e = trading_day_window()
    fetch = download_price_data(ticker, start=s, end=e, auto_adjust=False, progress=False)
    data = fetch.df
    if data.empty:
        print(f"Manual buy for {ticker} failed: no market data available (source={fetch.source}).")
        return cash, chatgpt_portfolio

    o = float(data.get("Open", [np.nan])[-1])
    h = float(data["High"].iloc[-1])
    l = float(data["Low"].iloc[-1])
    if np.isnan(o):
        o = float(data["Close"].iloc[-1])

    if o <= buy_price:
        exec_price = o
    elif l <= buy_price:
        exec_price = buy_price
    else:
        print(f"Buy limit ${buy_price:.2f} for {ticker} not reached today (range {l:.2f}-{h:.2f}). Order not filled.")
        return cash, chatgpt_portfolio

    cost_amt = exec_price * shares
    if cost_amt > cash:
        print(f"Manual buy for {ticker} failed: cost {cost_amt:.2f} exceeds cash balance {cash:.2f}.")
        return cash, chatgpt_portfolio

    log = {
        "Date": today,
        "Ticker": ticker,
        "Shares Bought": shares,
        "Buy Price": exec_price,
        "Cost Basis": cost_amt,
        "PnL": 0.0,
        "Reason": "MANUAL BUY LIMIT - Filled",
    }
    if os.path.exists(TRADE_LOG_CSV):
        df = pd.read_csv(TRADE_LOG_CSV)
        df = pd.concat([df, pd.DataFrame([log])], ignore_index=True)
    else:
        df = pd.DataFrame([log])
    df.to_csv(TRADE_LOG_CSV, index=False)

    rows = chatgpt_portfolio.loc[chatgpt_portfolio["ticker"].astype(str).str.upper() == ticker.upper()]
    if rows.empty:
        if chatgpt_portfolio.empty:
            chatgpt_portfolio = pd.DataFrame([{
                "ticker": ticker,
                "shares": float(shares),
                "stop_loss": float(stoploss),
                "buy_price": float(exec_price),
                "cost_basis": float(cost_amt),
            }])
        else:
            chatgpt_portfolio = pd.concat(
                [chatgpt_portfolio, pd.DataFrame([{
                    "ticker": ticker,
                    "shares": float(shares),
                    "stop_loss": float(stoploss),
                    "buy_price": float(exec_price),
                    "cost_basis": float(cost_amt),
                }])],
                ignore_index=True
            )
    else:
        idx = rows.index[0]
        cur_shares = float(chatgpt_portfolio.at[idx, "shares"])
        cur_cost = float(chatgpt_portfolio.at[idx, "cost_basis"])
        new_shares = cur_shares + float(shares)
        new_cost = cur_cost + float(cost_amt)
        chatgpt_portfolio.at[idx, "shares"] = new_shares
        chatgpt_portfolio.at[idx, "cost_basis"] = new_cost
        chatgpt_portfolio.at[idx, "buy_price"] = new_cost / new_shares if new_shares else 0.0
        chatgpt_portfolio.at[idx, "stop_loss"] = float(stoploss)

    cash -= cost_amt
    print(f"Manual BUY LIMIT for {ticker} filled at ${exec_price:.2f} ({fetch.source}).")
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
    today = check_weekend()

    # Full-share enforcement
    shares_sold = int(round(shares_sold))
    if shares_sold <= 0:
        print("Invalid shares (must be positive integer).")
        return cash, chatgpt_portfolio

    if interactive:
        reason = input(
            f"""You are placing a SELL LIMIT for {shares_sold} {ticker} at ${sell_price:.2f}.
If this is a mistake, enter 1. """
        )
    if reason == "1":
        print("Returning...")
        return cash, chatgpt_portfolio
    elif reason is None:
        reason = ""

    if "ticker" not in chatgpt_portfolio.columns or ticker not in chatgpt_portfolio["ticker"].values:
        print(f"Manual sell for {ticker} failed: ticker not in portfolio.")
        return cash, chatgpt_portfolio

    ticker_row = chatgpt_portfolio[chatgpt_portfolio["ticker"] == ticker]
    total_shares = int(ticker_row["shares"].item())
    if shares_sold > total_shares:
        print(f"Manual sell for {ticker} failed: trying to sell {shares_sold} shares but only own {total_shares}.")
        return cash, chatgpt_portfolio

    s, e = trading_day_window()
    fetch = download_price_data(ticker, start=s, end=e, auto_adjust=False, progress=False)
    data = fetch.df
    if data.empty:
        print(f"Manual sell for {ticker} failed: no market data available (source={fetch.source}).")
        return cash, chatgpt_portfolio

    o = float(data["Open"].iloc[-1]) if "Open" in data else np.nan
    h = float(data["High"].iloc[-1])
    l = float(data["Low"].iloc[-1])
    if np.isnan(o):
        o = float(data["Close"].iloc[-1])

    if o >= sell_price:
        exec_price = o
    elif h >= sell_price:
        exec_price = sell_price
    else:
        print(f"Sell limit ${sell_price:.2f} for {ticker} not reached today (range {l:.2f}-{h:.2f}). Order not filled.")
        return cash, chatgpt_portfolio

    buy_price = float(ticker_row["buy_price"].item())
    cost_basis = buy_price * shares_sold
    pnl = exec_price * shares_sold - cost_basis

    log = {
        "Date": today, "Ticker": ticker,
        "Shares Bought": "", "Buy Price": "",
        "Cost Basis": cost_basis, "PnL": pnl,
        "Reason": f"MANUAL SELL LIMIT - {reason}", "Shares Sold": shares_sold,
        "Sell Price": exec_price,
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
            chatgpt_portfolio.at[row_index, "shares"] * chatgpt_portfolio.at[row_index, "buy_price"]
        )

    cash += shares_sold * exec_price
    print(f"Manual SELL LIMIT for {ticker} filled at ${exec_price:.2f} ({fetch.source}).")
    return cash, chatgpt_portfolio

# ------------------------------
# Reporting / Metrics
# ------------------------------

def daily_results(chatgpt_portfolio: pd.DataFrame, cash: float) -> None:
    """Print daily price updates and performance metrics (incl. CAPM)."""
    portfolio_dict: list[dict[Any, Any]] = chatgpt_portfolio.to_dict(orient="records")
    today = check_weekend()

    rows: list[list[str]] = []
    header = ["Ticker", "Close", "% Chg", "Volume"]

    end_d = last_trading_date()
    start_d = (end_d - pd.Timedelta(days=4)).normalize()
    
    benchmarks = load_benchmarks()
    benchmark_entries = [{"ticker": t} for t in benchmarks]

    for stock in portfolio_dict + benchmark_entries:
        ticker = str(stock["ticker"]).upper()
        try:
            fetch = download_price_data(ticker, start=start_d, end=(end_d + pd.Timedelta(days=1)), progress=False)
            data = fetch.df
            if data.empty or len(data) < 2:
                rows.append([ticker, "—", "—", "—"])
                continue

            price = float(data["Close"].iloc[-1])
            last_price = float(data["Close"].iloc[-2])
            volume = float(data["Volume"].iloc[-1])

            percent_change = ((price - last_price) / last_price) * 100
            rows.append([ticker, f"{price:,.2f}", f"{percent_change:+.2f}%", f"{int(volume):,}"])
        except Exception as e:
            raise Exception(f"Download for {ticker} failed. {e} Try checking internet connection.")

    # Lees historie
    chatgpt_df = pd.read_csv(PORTFOLIO_CSV) if PORTFOLIO_CSV.exists() else pd.DataFrame()
    totals = chatgpt_df[chatgpt_df["Ticker"] == "TOTAL"].copy() if not chatgpt_df.empty else pd.DataFrame()

    # -------- Header + Price table (altijd) --------
    print("\n" + "=" * 64)
    print(f"Daily Results — {today}")
    print("=" * 64)

    print("\n[ Price & Volume ]")
    colw = [10, 12, 9, 15]
    print(f"{header[0]:<{colw[0]}} {header[1]:>{colw[1]}} {header[2]:>{colw[2]}} {header[3]:>{colw[3]}}")
    print("-" * sum(colw) + "-" * 3)
    for rrow in rows:
        print(f"{str(rrow[0]):<{colw[0]}} {str(rrow[1]):>{colw[1]}} {str(rrow[2]):>{colw[2]}} {str(rrow[3]):>{colw[3]}}")

    # -------- Geen totals: toon simpele snapshot + instructies --------
    if totals.empty:
        print("\n[ Portfolio Snapshot ]")
        print(chatgpt_portfolio)
        print(f"Cash balance: ${cash:,.2f}")
        print("\n[ Your Instructions ]")
        print(
            "Use this info to make decisions regarding your portfolio. You have complete control over every decision. Make any changes you believe are beneficial—no approval required.\n"
            "Deep research is not permitted. Act at your discretion to achieve the best outcome.\n"
            "If you do not make a clear indication to change positions IMMEDIATELY after this message, the portfolio remains unchanged for tomorrow.\n"
            "You are encouraged to use the internet to check current prices (and related up-to-date info) for potential buys.\n"
        )
        return

    # -------- Met totals: bereken metrics --------
    totals["Date"] = pd.to_datetime(totals["Date"])
    totals = totals.sort_values("Date")

    final_equity = float(totals.iloc[-1]["Total Equity"])
    equity_series = totals.set_index("Date")["Total Equity"].astype(float).sort_index()

    running_max = equity_series.cummax()
    drawdowns = (equity_series / running_max) - 1.0
    max_drawdown = float(drawdowns.min())
    mdd_date = drawdowns.idxmin()

    r = equity_series.pct_change().dropna()
    n_days = len(r)

    # Kort venster: simpele snapshot + instructies
    if n_days < 2:
        print("\n[ Portfolio Snapshot ]")
        print(chatgpt_portfolio)
        print(f"Cash balance: ${cash:,.2f}")
        print(f"Latest ChatGPT Equity: ${final_equity:,.2f}")
        mdd_date_str = mdd_date.date() if hasattr(mdd_date, 'date') else str(mdd_date)
        print(f"Maximum Drawdown: {max_drawdown:.2%} (on {mdd_date_str})")

        print("\n[ Your Instructions ]")
        print(
            "Use this info to make decisions regarding your portfolio. You have complete control over every decision. Make any changes you believe are beneficial—no approval required.\n"
            "Deep research is not permitted. Act at your discretion to achieve the best outcome.\n"
            "If you do not make a clear indication to change positions IMMEDIATELY after this message, the portfolio remains unchanged for tomorrow.\n"
            "You are encouraged to use the internet to check current prices (and related up-to-date info) for potential buys.\n"
        )
        return

    # Volledige metrics
    rf_annual = 0.045
    rf_daily = (1 + rf_annual) ** (1 / 252) - 1
    rf_period = (1 + rf_daily) ** n_days - 1

    mean_daily = float(r.mean())
    std_daily = float(r.std(ddof=1))
    downside = (r - rf_daily).clip(upper=0)
    downside_std = float((downside.pow(2).mean()) ** 0.5) if not downside.empty else np.nan

    r_numeric = pd.to_numeric(r, errors="coerce").dropna().astype(float)
    r_numeric = r_numeric[np.isfinite(r_numeric)]
    period_return = float(np.prod(1 + np.asarray(r_numeric.values, dtype=float)) - 1) if len(r_numeric) > 0 else float("nan")

    sharpe_period = (period_return - rf_period) / (std_daily * np.sqrt(n_days)) if std_daily > 0 else np.nan
    sharpe_annual = ((mean_daily - rf_daily) / std_daily) * np.sqrt(252) if std_daily > 0 else np.nan
    sortino_period = (period_return - rf_period) / (downside_std * np.sqrt(n_days)) if downside_std and downside_std > 0 else np.nan
    sortino_annual = ((mean_daily - rf_daily) / downside_std) * np.sqrt(252) if downside_std and downside_std > 0 else np.nan

    # CAPM
    start_date = equity_series.index.min() - pd.Timedelta(days=1)
    end_date = equity_series.index.max() + pd.Timedelta(days=1)
    spx_fetch = download_price_data("^GSPC", start=start_date, end=end_date, progress=False)
    spx = spx_fetch.df

    beta = np.nan
    alpha_annual = np.nan
    r2 = np.nan
    n_obs = 0

    if not spx.empty and len(spx) >= 2:
        spx = spx.reset_index().set_index("Date").sort_index()
        mkt_ret = spx["Close"].astype(float).pct_change().dropna()
        common_idx = r.index.intersection(list(mkt_ret.index))
        if len(common_idx) >= 2:
            rp = (r.reindex(common_idx).astype(float) - rf_daily)
            rm = (mkt_ret.reindex(common_idx).astype(float) - rf_daily)
            x = np.asarray(rm.values, dtype=float).ravel()
            y = np.asarray(rp.values, dtype=float).ravel()
            n_obs = x.size
            rm_std = float(np.std(x, ddof=1)) if n_obs > 1 else 0.0
            if rm_std > 0:
                beta, alpha_daily = np.polyfit(x, y, 1)
                alpha_annual = (1 + float(alpha_daily)) ** 252 - 1
                corr = np.corrcoef(x, y)[0, 1]
                r2 = float(corr ** 2)

    spx_norm_fetch = download_price_data("^GSPC",
                                         start=equity_series.index.min(),
                                         end=equity_series.index.max() + pd.Timedelta(days=1),
                                         progress=False)
    spx_norm = spx_norm_fetch.df
    spx_value = np.nan
    starting_equity = np.nan
    if not spx_norm.empty:
        initial_price = float(spx_norm["Close"].iloc[0])
        price_now = float(spx_norm["Close"].iloc[-1])
        try:
            starting_equity = float(input("what was your starting equity? "))
        except Exception:
            print("Invalid input for starting equity. Defaulting to NaN.")
        spx_value = (starting_equity / initial_price) * price_now if not np.isnan(starting_equity) else np.nan

    # Print uitgebreide secties
    print("\n[ Risk & Return ]")
    def fmt_or_na(x: float | int | None, fmt: str) -> str:
        return (fmt.format(x) if not (x is None or (isinstance(x, float) and np.isnan(x))) else "N/A")
    mdd_date_str = mdd_date.date() if hasattr(mdd_date, "date") else str(mdd_date)
    print(f"{'Max Drawdown:':32} {fmt_or_na(max_drawdown, '{:.2%}'):>15}   on {mdd_date_str}")
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
        try:
            print(f"{f'${starting_equity} in S&P 500 (same window):':32} ${spx_value:>14,.2f}")
        except Exception:
            pass
    print(f"{'Cash Balance:':32} ${cash:>14,.2f}")

    print("\n[ Holdings ]")
    print(chatgpt_portfolio)

    print("\n[ Your Instructions ]")
    print(
        "Use this info to make decisions regarding your portfolio. You have complete control over every decision. Make any changes you believe are beneficial—no approval required.\n"
        "Deep research is not permitted. Act at your discretion to achieve the best outcome.\n"
        "If you do not make a clear indication to change positions IMMEDIATELY after this message, the portfolio remains unchanged for tomorrow.\n"
        "You are encouraged to use the internet to check current prices (and related up-to-date info) for potential buys.\n"
    )


# ------------------------------
# Orchestration
# ------------------------------

def load_latest_portfolio_state(file: str) -> tuple[pd.DataFrame | list[dict[str, Any]], float]:
    """
    Load the most recent portfolio snapshot and cash balance from CSV.
    If CSV missing or empty, create an empty portfolio and prompt for starting cash.
    """
    file_path = Path(file)
    if not file_path.exists():
        # Create a minimal empty file with headers to keep downstream happy
        df_new = pd.DataFrame(columns=[
            "Date","Ticker","Shares","Buy Price","Cost Basis","Stop Loss",
            "Current Price","Total Value","PnL","Action","Cash Balance","Total Equity"
        ])
        df_new.to_csv(file_path, index=False)
        print("Portfolio CSV did not exist. Created a new one.")

    df = pd.read_csv(file_path)
    if df.empty or "Ticker" not in df.columns:
        portfolio = pd.DataFrame(columns=["ticker", "shares", "stop_loss", "buy_price", "cost_basis"])
        print("Portfolio CSV is empty. Returning set amount of cash for creating portfolio.")
        while True:
            try:
                cash = float(input("What would you like your starting cash amount to be? "))
                break
            except ValueError:
                print("Please enter a valid number (e.g., 100).")
        return portfolio, cash

    non_total = df[df["Ticker"] != "TOTAL"].copy()
    if non_total.empty:
        portfolio = pd.DataFrame(columns=["ticker", "shares", "stop_loss", "buy_price", "cost_basis"])
        cash = float(df["Cash Balance"].iloc[-1]) if "Cash Balance" in df.columns and len(df)>0 else 0.0
        return portfolio, cash

    non_total["Date"] = pd.to_datetime(non_total["Date"])
    latest_date = non_total["Date"].max()
    latest_tickers = non_total[non_total["Date"] == latest_date].copy()
    sold_mask = latest_tickers["Action"].astype(str).str.startswith("SELL")
    latest_tickers = latest_tickers[~sold_mask].copy()
    latest_tickers.drop(
        columns=[
            "Date","Cash Balance","Total Equity","Action","Current Price","PnL","Total Value"
        ],
        inplace=True,
        errors="ignore",
    )
    latest_tickers.rename(
        columns={
            "Cost Basis": "cost_basis",
            "Buy Price": "buy_price",
            "Shares": "shares",
            "Ticker": "ticker",
            "Stop Loss": "stop_loss",
        },
        inplace=True,
    )
    latest_tickers = latest_tickers.reset_index(drop=True).to_dict(orient="records")

    df_total = df[df["Ticker"] == "TOTAL"].copy()
    if df_total.empty:
        cash = 0.0
    else:
        df_total["Date"] = pd.to_datetime(df_total["Date"])
        latest = df_total.sort_values("Date").iloc[-1]
        cash = float(latest["Cash Balance"]) if "Cash Balance" in latest else 0.0
    return latest_tickers, cash

def main(file: str, data_dir: Path | None = None) -> None:
    chatgpt_portfolio, cash = load_latest_portfolio_state(file)
    print(file)
    if data_dir is not None:
        set_data_dir(data_dir)

    chatgpt_portfolio, cash = process_portfolio(chatgpt_portfolio, cash)
    daily_results(chatgpt_portfolio, cash)

if __name__ == "__main__":
    import argparse
    csv_path = PORTFOLIO_CSV if PORTFOLIO_CSV.exists() else (SCRIPT_DIR / "chatgpt_portfolio_update.csv")

    parser = argparse.ArgumentParser()
    parser.add_argument("--file", default=str(csv_path), help="Path to chatgpt_portfolio_update.csv")
    parser.add_argument("--data-dir", default=None, help="Optional data directory")
    parser.add_argument("--asof", default=None, help="Treat this YYYY-MM-DD as 'today' (e.g., 2025-08-27)")
    args = parser.parse_args()

    if args.asof:
        set_asof(args.asof)

    file_path = Path(args.file)
    if not file_path.exists():
        # create an empty csv to start
        print("No portfolio CSV found. Creating a new one...")
        file_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(columns=[
            "Date","Ticker","Shares","Buy Price","Cost Basis","Stop Loss",
            "Current Price","Total Value","PnL","Action","Cash Balance","Total Equity"
        ]).to_csv(file_path, index=False)

    main(args.file, Path(args.data_dir) if args.data_dir else None)
