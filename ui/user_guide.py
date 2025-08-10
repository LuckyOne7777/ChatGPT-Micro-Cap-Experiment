import streamlit as st


def show_user_guide() -> None:
    """Display the user guide with helpful information."""
    with st.expander("📚 User Guide", expanded=True):
        st.subheader("🚀 Getting Started")
        st.markdown(
            """
            Welcome to the **AI Assisted Trading Portfolio Manager**! This application helps you track and manage your investment portfolio with powerful analytics.

            ### 1. **Initial Setup**
            - **Add Cash**: Start by adding funds to your account using the cash management section on the Dashboard
            - **Fresh Start**: The application begins with a clean slate - no existing positions or history

            ### 2. **Dashboard Overview**
            Navigate to the **Dashboard** (main page) to:
            - View your current cash balance and total portfolio value
            - See all your current holdings with real-time prices
            - Monitor unrealized gains/losses for each position
            - Access buy and sell forms for trading

            ### 3. **Trading Operations**
            - **Buying Stocks**: Use the buy form to purchase shares by entering ticker symbol, quantity, and price
            - **Selling Stocks**: Use the sell form to close positions (full or partial sales)
            - **Real-time Validation**: All trades are validated against current market prices
            - **Automatic Updates**: Portfolio values update automatically with live market data

            ### 4. **Watchlist Management**
            Visit the **Watchlist** page to:
            - Add ticker symbols to track potential investments
            - Monitor real-time prices for stocks you're interested in
            - Quickly buy stocks directly from your watchlist
            - Remove tickers you're no longer watching

            ### 5. **Performance Tracking**
            The **Performance** page provides:
            - Historical portfolio performance charts
            - Key performance indicators (KPIs) and metrics
            - Date range filtering for custom analysis
            - Visual performance comparisons over time
            """
        )

        st.subheader("💡 Key Features")
        st.markdown(
            """
            - **Real-time Market Data**: Powered by Yahoo Finance for live stock prices
            - **SQLite Database**: All data stored locally in `data/trading.db`
            - **Comprehensive Testing**: 82% test coverage ensures reliability
            - **Responsive Design**: Clean, modern interface optimized for all devices
            - **Data Export**: Download portfolio snapshots as CSV files
            """
        )

        st.subheader("🛡️ Risk Management")
        st.markdown(
            """
            - **Position Monitoring**: Track individual position sizes and exposure
            - **Real-time P&L**: Monitor gains and losses as they happen
            - **Cash Management**: Maintain adequate cash reserves for new opportunities
            - **Portfolio Diversification**: Spread risk across multiple positions
            """
        )

        st.subheader("🔧 Technical Notes")
        st.markdown(
            """
            - **Data Storage**: Portfolio data persists between sessions in local SQLite database
            - **Market Hours**: Stock prices update during market hours (live data may have delays)
            - **Offline Capability**: Core functionality works without internet (using last known prices)
            - **Testing**: Run `pytest` in the project directory to execute the test suite
            """
        )
