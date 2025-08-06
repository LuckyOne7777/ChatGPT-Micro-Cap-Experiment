from datetime import datetime
import pandas as pd
import streamlit as st

from data.portfolio import save_portfolio_snapshot
from services.session import init_session_state
from ui.watchlist import show_watchlist_sidebar
from ui.onboarding import show_onboarding
from ui.cash import show_cash_section
from ui.forms import show_buy_form, show_sell_form
from ui.summary import build_daily_summary


def render_dashboard() -> None:
    """Render the main dashboard tab."""

    init_session_state()

    show_watchlist_sidebar()
    show_onboarding()

    feedback = st.session_state.pop("feedback", None)
    if feedback:
        kind, text = feedback
        getattr(st, kind)(text)

    if st.session_state.get("needs_cash", False):
        st.subheader("Initialize Portfolio")
        with st.form("init_cash_form", clear_on_submit=True):
            start_cash_raw = st.text_input(
                "Enter starting cash", key="start_cash", placeholder="0.00"
            )
            init_submit = st.form_submit_button("Set Starting Cash")
        if init_submit:
            try:
                start_cash = float(start_cash_raw)
                if start_cash <= 0:
                    raise ValueError
            except ValueError:
                st.session_state.feedback = (
                    "error",
                    "Please enter a positive number.",
                )
            else:
                st.session_state.cash = start_cash
                st.session_state.needs_cash = False
                save_portfolio_snapshot(
                    st.session_state.portfolio, st.session_state.cash
                )
                st.session_state.feedback = (
                    "success",
                    f"Starting cash of ${start_cash:.2f} recorded.",
                )
            st.session_state.pop("start_cash", None)
            st.rerun()
    else:
        summary_df = save_portfolio_snapshot(
            st.session_state.portfolio, st.session_state.cash
        )

        summary_df = summary_df.rename(
            columns={
                "date": "Date",
                "ticker": "Ticker",
                "shares": "Shares",
                "cost_basis": "Cost Basis",
                "stop_loss": "Stop Loss",
                "current_price": "Current Price",
                "total_value": "Total Value",
                "pnl": "PnL",
                "action": "Action",
                "cash_balance": "Cash Balance",
                "total_equity": "Total Equity",
            }
        )

        show_cash_section()

        port_table = summary_df[summary_df["Ticker"] != "TOTAL"].copy()
        header_cols = st.columns([4, 1, 1])
        with header_cols[0]:
            st.subheader("Current Portfolio")
        with header_cols[1]:
            auto_refresh = st.checkbox(
                "Auto-refresh every 30 min",
                key="auto_refresh",
                label_visibility="visible",
            )
        with header_cols[2]:
            if st.button("🔄", key="refresh_portfolio", help="Refresh portfolio"):
                st.experimental_rerun()

        if port_table.empty:
            st.info(
                "Your portfolio is empty. Use the Buy form below to add your first position."
            )
        else:
            if auto_refresh:
                try:  # pragma: no cover - optional dependency
                    from streamlit_autorefresh import st_autorefresh

                    st_autorefresh(interval=30 * 60 * 1000, key="portfolio_refresh")
                except Exception:  # pragma: no cover - import-time failure
                    st.warning(
                        "Install streamlit-autorefresh for auto refresh support."
                    )

            st.caption(
                f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )

            numeric_cols = [
                "Shares",
                "Cost Basis",
                "Current Price",
                "Stop Loss",
                "Total Value",
                "PnL",
            ]
            for col in numeric_cols:
                if col in port_table.columns:
                    port_table[col] = pd.to_numeric(port_table[col], errors="coerce")

            if {"Current Price", "Cost Basis"}.issubset(port_table.columns):
                port_table["Pct Change"] = (
                    (port_table["Current Price"] - port_table["Cost Basis"])
                    / port_table["Cost Basis"]
                ) * 100

            port_table.rename(
                columns={"Cost Basis": "Buy Price", "Total Value": "Value"},
                inplace=True,
            )

            for col in [
                "Shares",
                "Buy Price",
                "Current Price",
                "Stop Loss",
                "Value",
                "PnL",
                "Pct Change",
            ]:
                if col in port_table:
                    port_table[col] = pd.to_numeric(port_table[col], errors="coerce")

            def highlight_stop(row: pd.Series) -> list[str]:
                stop = row.get("Stop Loss")
                price = row.get("Current Price")
                if pd.isna(stop) or pd.isna(price):
                    return [""] * len(row)
                color = "#ffcccc" if price <= stop else ""
                return [f"background-color: {color}"] * len(row)

            def highlight_pct(val: float) -> str:
                if pd.isna(val):
                    return ""
                color = "green" if val > 0 else "red" if val < 0 else ""
                return f"color: {color}"

            def color_pnl(val: float) -> str:
                if pd.isna(val):
                    return ""
                color = "green" if val > 0 else "red" if val < 0 else ""
                return f"color: {color}"

            def fmt_currency(x):
                try:
                    v = float(x)
                    return f"${v:,.2f}"
                except Exception:
                    return ""

            def fmt_percent(x):
                try:
                    v = float(x)
                    sign = "+" if v > 0 else ""
                    arrow = "\u2191" if v > 0 else ("\u2193" if v < 0 else "")
                    return f"{sign}{v:.1f}% {arrow}".strip()
                except Exception:
                    return ""

            def fmt_shares(x):
                try:
                    return f"{int(float(x)):,}"
                except Exception:
                    return ""

            formatters = {}
            if "Shares" in port_table:
                formatters["Shares"] = fmt_shares
            for c in ["Buy Price", "Current Price", "Stop Loss", "Value", "PnL"]:
                if c in port_table:
                    formatters[c] = fmt_currency
            if "Pct Change" in port_table:
                formatters["Pct Change"] = fmt_percent

            numeric_display = list(formatters.keys())

            styled = port_table.style.format(formatters).set_properties(
                subset=numeric_display, **{"text-align": "right"}
            )
            if "Pct Change" in port_table:
                styled = styled.applymap(highlight_pct, subset=["Pct Change"])
            if "PnL" in port_table:
                styled = styled.applymap(color_pnl, subset=["PnL"])
            styled = styled.apply(highlight_stop, axis=1).set_table_styles(
                [
                    {
                        "selector": "th",
                        "props": [
                            ("font-size", "16px"),
                            ("text-align", "center"),
                        ],
                    },
                    {
                        "selector": "td",
                        "props": [
                            ("font-size", "16px"),
                            ("color", "black"),
                        ],
                    },
                ]
            )

            column_config = {
                "Stop Loss": st.column_config.NumberColumn(
                    "Stop Loss", help="Price at which the stock will be sold to limit loss"
                ),
                "Pct Change": st.column_config.NumberColumn(
                    "Pct Change", help="Percentage change since purchase"
                ),
                "PnL": st.column_config.NumberColumn("PnL", help="Profit or loss"),
                "Value": st.column_config.NumberColumn("Value", help="Current market value"),
                "Buy Price": st.column_config.NumberColumn(
                    "Buy Price", help="Average price paid per share"
                ),
            }
            st.dataframe(
                styled,
                use_container_width=True,
                column_config=column_config,
                hide_index=True,
            )

        show_buy_form()
        if not port_table.empty:
            show_sell_form()

        st.subheader("Daily Summary")
        if st.button("Generate Daily Summary"):
            if not summary_df.empty:
                st.session_state.daily_summary = build_daily_summary(summary_df)
            else:
                st.info("No summary available.")
        if st.session_state.get("daily_summary"):
            st.code(st.session_state.daily_summary, language="markdown")
            st.button(
                "Dismiss Summary",
                key="dismiss_summary",
                on_click=lambda: st.session_state.update(daily_summary=""),
            )

        if st.session_state.get("error_log"):
            st.subheader("Error Log")
            for line in st.session_state.error_log:
                st.text(line)
