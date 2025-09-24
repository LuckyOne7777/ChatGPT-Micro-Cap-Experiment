"""
Main entry point for the ChatGPT Micro Cap Experiment report generator.
"""

import pandas as pd
from datetime import datetime
from cli.arguments import parse_args
from data.loaders.portfolio_loader import PortfolioLoader
from data.loaders.trade_loader import TradeLoader
from analysis.roi_analyzer import ROIAnalyzer
from analysis.drawdown_analyzer import DrawdownAnalyzer
from analysis.risk_analyzer import RiskAnalyzer
from analysis.performance_analyzer import PerformanceAnalyzer
from analysis.cash_analyzer import CashAnalyzer
from visualization.plot_generator import PlotGenerator
from visualization.html_generator import HTMLGenerator
from visualization.markdown_generator import MarkdownGenerator
from visualization.report_generator import ReportContent
from utils.helpers import download_sp500
from pathlib import Path


def main():
    """Main function to generate the financial report."""
    # Parse command line arguments
    args = parse_args()
    
    # Initialize loaders
    portfolio_loader = PortfolioLoader(args.data_dir)
    trade_loader = TradeLoader(args.data_dir)
    
    # Load data
    portfolio_df = portfolio_loader.load_portfolio_data(args.date)
    portfolio_totals = portfolio_loader.load_portfolio_totals(args.date)
    trade_df = trade_loader.load_trade_data(args.date)
    
    # Initialize analyzers
    roi_analyzer = ROIAnalyzer(portfolio_loader)
    drawdown_analyzer = DrawdownAnalyzer()
    risk_analyzer = RiskAnalyzer()
    performance_analyzer = PerformanceAnalyzer()
    cash_analyzer = CashAnalyzer(portfolio_loader)
    
    # Create reports directory
    reports_dir = HTMLGenerator.create_reports_directory(args.date)
    print(f"Saving reports to: {reports_dir}")
    
    # Initialize generators
    plot_generator = PlotGenerator(reports_dir)
    html_generator = HTMLGenerator(reports_dir)
    markdown_generator = MarkdownGenerator(reports_dir)
    
    # Perform analyses
    current_stocks_roi = roi_analyzer.calculate_stock_roi(portfolio_df)
    all_stocks_roi = roi_analyzer.calculate_all_stocks_roi(portfolio_df, trade_df)
    current_portfolio_roi = roi_analyzer.calculate_current_portfolio_roi(portfolio_df)
    
    # For separate ROI calculation, we need the portfolio data including TOTAL rows
    portfolio_df_with_totals = pd.concat([portfolio_df, portfolio_totals], ignore_index=True)
    separate_portfolio_roi = roi_analyzer.calculate_separate_portfolio_roi(portfolio_df_with_totals)
    
    drawdown_data = drawdown_analyzer.calculate_all_drawdowns(portfolio_df)
    
    # Calculate daily performance
    daily_data = performance_analyzer.calculate_daily_performance(portfolio_totals)
    
    # Calculate ROI over time
    roi_time_df = performance_analyzer.calculate_roi_over_time(portfolio_df, trade_df)
    
    # Get date range
    start_date = pd.Timestamp("2025-06-27")
    end_date = portfolio_totals["Date"].max()
    sp500 = download_sp500(start_date, end_date)
    
    # Calculate cash positions
    dates = sorted(trade_df['Date'].dt.date.unique())
    actual_cash_balances = cash_analyzer.calculate_daily_cash_with_actual_balance(trade_df)
    portfolio_values = cash_analyzer.get_portfolio_values_by_date(portfolio_df, dates)
    stock_values = cash_analyzer.get_stock_values_by_date(portfolio_df, dates)

    cash_data = {
        'actual_cash': actual_cash_balances,
        'portfolio_values': portfolio_values,
        'stock_values': stock_values
    }
    
    # Generate plots
    performance_plot = plot_generator.generate_performance_comparison_plot(portfolio_totals, sp500)
    print(f"Saved performance comparison plot to: {performance_plot}")
    
    # Generate cash position plot
    cash_plot = plot_generator.generate_cash_position_plot(cash_data)
    print(f"Saved cash position plot to: {cash_plot}")
    
    roi_plot = plot_generator.generate_roi_bars_plot(current_stocks_roi)
    print(f"Saved ROI bars plot to: {roi_plot}")
    
    composition_plot = plot_generator.generate_portfolio_composition_plot(all_stocks_roi)
    print(f"Saved portfolio composition plot to: {composition_plot}")
    
    # Generate additional plots
    roi_drawdown_plot = plot_generator.generate_roi_drawdown_dashboard(current_stocks_roi, drawdown_data, all_stocks_roi)
    print(f"Saved ROI/Drawdown dashboard to: {roi_drawdown_plot}")
    
    comparative_plot = plot_generator.generate_comparative_roi_dashboard(all_stocks_roi, current_portfolio_roi)
    print(f"Saved comparative ROI dashboard to: {comparative_plot}")
    
    daily_performance_plot = plot_generator.generate_daily_performance_plot(daily_data)
    print(f"Saved daily performance plot to: {daily_performance_plot}")
    
    position_analysis_plot = plot_generator.generate_position_size_analysis(all_stocks_roi)
    print(f"Saved position analysis plot to: {position_analysis_plot}")
    
    sector_analysis_plot = plot_generator.generate_sector_analysis(all_stocks_roi)
    print(f"Saved sector analysis plot to: {sector_analysis_plot}")
    
    # Calculate win/loss metrics
    win_loss_metrics = performance_analyzer.calculate_win_loss_metrics(all_stocks_roi)
    
    win_loss_plot = plot_generator.generate_win_loss_analysis(win_loss_metrics)
    print(f"Saved win/loss analysis plot to: {win_loss_plot}")
    
    roi_over_time_plot = plot_generator.generate_roi_over_time_plot(roi_time_df)
    print(f"Saved ROI over time plot to: {roi_over_time_plot}")
    
    individual_drawdown_plot = plot_generator.generate_individual_drawdown_plot(portfolio_df)
    print(f"Saved individual drawdown plot to: {individual_drawdown_plot}")
    
    # Calculate advanced risk metrics
    advanced_risk_metrics = risk_analyzer.calculate_advanced_risk_metrics(portfolio_totals)
    print(f"Advanced risk metrics calculated: Sortino Ratio = {advanced_risk_metrics['sortino_ratio']:.2f}")
    
    risk_return_plot = plot_generator.generate_risk_return_plot(portfolio_totals)
    print(f"Saved risk-return plot to: {risk_return_plot}")
    
    # Get the latest cash balance from portfolio data
    latest_portfolio_data = portfolio_loader.load_portfolio_totals(args.date)
    latest_entry = latest_portfolio_data.iloc[-1]
    current_cash_balance = latest_entry['Cash Balance'] if not latest_portfolio_data.empty and 'Cash Balance' in latest_entry else 0.0
    total_portfolio_value = latest_entry['Total Equity'] if not latest_portfolio_data.empty and 'Total Equity' in latest_entry else 0.0

    # Calculate portfolio-level metrics with cash balance
    summary_stats = risk_analyzer.calculate_risk_metrics(all_stocks_roi, drawdown_data, current_cash_balance)
    
    # Add separate ROI to summary stats
    summary_stats['separate_roi_pct'] = separate_portfolio_roi['separate_roi_pct']
    
    # Add cash balance to summary stats (already included in calculate_risk_metrics, but keeping for backward compatibility)
    summary_stats['cash_balance'] = current_cash_balance
    
    # Calculate volatility metrics
    volatility_metrics = risk_analyzer.calculate_portfolio_volatility(portfolio_totals)
    
    def add_totals_row(df):
        """Add a totals row to a DataFrame with financial data."""
        if df.empty or len(df.columns) <= 1:
            return df
        
        # Create totals row
        totals_row = {}
        for col in df.columns:
            if col == "Ticker":
                totals_row[col] = "TOTAL"
            elif col == "Shares":
                # Sum shares
                try:
                    total = df[col].astype(float).sum()
                    totals_row[col] = f"{total:.1f}"
                except:
                    totals_row[col] = "-"
            elif col == "ROI (%)":
                # For ROI, we'll calculate a weighted average based on Cost Basis ($)
                if "Cost Basis ($)" in df.columns and "Realized Proceeds ($)" in df.columns and "Market Value ($)" in df.columns:
                    # Convert formatted strings back to numbers
                    try:
                        cost_basis_nums = df["Cost Basis ($)"].str.replace('$', '').str.replace(',', '').astype(float)
                        proceeds_nums = df["Realized Proceeds ($)"].str.replace('$', '').str.replace(',', '').astype(float)
                        market_value_nums = df["Market Value ($)"].str.replace('$', '').str.replace(',', '').astype(float)
                        total_cost = cost_basis_nums.sum()
                        total_proceeds = proceeds_nums.sum()
                        total_market_value = market_value_nums.sum()
                        if total_cost > 0:
                            # Correct formula: ROI = ((Proceeds + Market Value) / Cost Basis - 1) * 100
                            weighted_roi = ((total_proceeds + total_market_value) / total_cost - 1) * 100
                            totals_row[col] = f"{weighted_roi:.2f}%"
                        else:
                            totals_row[col] = "0.00%"
                    except:
                        totals_row[col] = "-"
                else:
                    totals_row[col] = "-"
            else:
                # For other numeric columns, sum them up
                try:
                    # Convert formatted strings back to numbers
                    if col in df.columns:
                        numeric_values = df[col].str.replace('$', '').str.replace(',', '').astype(float)
                        total = numeric_values.sum()
                        totals_row[col] = f"${total:.2f}"
                    else:
                        totals_row[col] = "-"
                except:
                    totals_row[col] = "-"
        
        # Add the totals row to the dataframe
        totals_df = pd.DataFrame([totals_row])
        return pd.concat([df, totals_df], ignore_index=True)
    
    # Format all stocks ROI table
    all_stocks_display = all_stocks_roi.copy()
    # Reorder columns to place Realized Proceeds ($) next to Cost Basis ($)
    column_order = ["Ticker", "Shares", "Cost Basis ($)", "Realized Proceeds ($)", "Market Value ($)", "ROI (%)", "Net Gain/Loss ($)"]
    # Only reorder columns that exist in the DataFrame
    available_columns = [col for col in column_order if col in all_stocks_display.columns]
    all_stocks_display = all_stocks_display[available_columns]
    all_stocks_display["Cost Basis ($)"] = all_stocks_display["Cost Basis ($)"].apply(lambda x: f"${x:.2f}")
    all_stocks_display["Realized Proceeds ($)"] = all_stocks_display["Realized Proceeds ($)"].apply(lambda x: f"${x:.2f}")
    all_stocks_display["Market Value ($)"] = all_stocks_display["Market Value ($)"].apply(lambda x: f"${x:.2f}")
    all_stocks_display["ROI (%)"] = all_stocks_display["ROI (%)"].apply(lambda x: f"{x:.2f}%")
    all_stocks_display["Net Gain/Loss ($)"] = all_stocks_display["Net Gain/Loss ($)"].apply(lambda x: f"${x:.2f}")
    # Add totals row
    all_stocks_display = add_totals_row(all_stocks_display)
    
    # Format current portfolio ROI table
    current_stocks_display = current_portfolio_roi.copy()
    # Reorder columns to place Realized Proceeds ($) next to Cost Basis ($)
    column_order = ["Ticker", "Shares", "Cost Basis ($)", "Realized Proceeds ($)", "Market Value ($)", "ROI (%)", "Net Gain/Loss ($)"]
    # Only reorder columns that exist in the DataFrame
    available_columns = [col for col in column_order if col in current_stocks_display.columns]
    current_stocks_display = current_stocks_display[available_columns]
    current_stocks_display["Cost Basis ($)"] = current_stocks_display["Cost Basis ($)"].apply(lambda x: f"${x:.2f}")
    current_stocks_display["Realized Proceeds ($)"] = current_stocks_display["Realized Proceeds ($)"].apply(lambda x: f"${x:.2f}")
    current_stocks_display["Market Value ($)"] = current_stocks_display["Market Value ($)"].apply(lambda x: f"${x:.2f}")
    current_stocks_display["ROI (%)"] = current_stocks_display["ROI (%)"].apply(lambda x: f"{x:.2f}%")
    current_stocks_display["Net Gain/Loss ($)"] = current_stocks_display["Net Gain/Loss ($)"].apply(lambda x: f"${x:.2f}")
    # Add totals row
    current_stocks_display = add_totals_row(current_stocks_display)
    
    # Calculate invested value (holdings) - market value of currently held stocks
    # Extract numeric values from the formatted Market Value column (excluding the TOTAL row)
    market_values = current_stocks_display[:-1]["Market Value ($)"].str.replace('$', '').str.replace(',', '').astype(float)
    current_holdings_market_value = market_values.sum()
    
    # Convert to HTML tables
    all_stocks_table_html = html_generator.dataframe_to_html_table(all_stocks_display, "All Stocks Ever Purchased ROI Analysis")
    current_stocks_table_html = html_generator.dataframe_to_html_table(current_stocks_display, "Currently Held Stocks ROI Analysis")
    
    # Generate HTML report (existing method for backward compatibility)
    html_generator.generate_professional_index_html(
        performance_plot, roi_plot, composition_plot, 
        roi_drawdown_plot, comparative_plot,
        daily_performance_plot, position_analysis_plot,
        sector_analysis_plot, win_loss_plot, roi_over_time_plot,
        individual_drawdown_plot, risk_return_plot,
        cash_plot,
        all_stocks_table_html, current_stocks_table_html, 
        summary_stats, summary_stats, volatility_metrics,
        win_loss_metrics, advanced_risk_metrics,
        args.date
    )
    print(f"Saved professional index.html to: {reports_dir / 'index.html'}")
    
    # Create ReportContent object for new template system
    report_content = ReportContent(args.date)
    
    # Set metrics for the report
    summary_stats['invested_value_holdings'] = current_holdings_market_value
    report_content.set_metrics({
        'summary_stats': summary_stats,
        'volatility_metrics': volatility_metrics,
        'win_loss_metrics': win_loss_metrics
    })
    
    # Set risk metrics for the report
    report_content.set_risk_metrics(summary_stats, advanced_risk_metrics)
    report_content.set_win_loss_metrics(win_loss_metrics)
    
    # Add sections to the report
    # Performance Analysis Section
    performance_content = [
        {'type': 'plot', 'title': 'Portfolio Performance vs. Benchmark', 'path': performance_plot},
        {'type': 'plot', 'title': 'Daily Performance', 'path': daily_performance_plot},
        {'type': 'plot', 'title': 'ROI Over Time', 'path': roi_over_time_plot},
        {'type': 'plot', 'title': 'Individual Stock Drawdowns', 'path': individual_drawdown_plot},
        {'type': 'plot', 'title': 'Risk-Return Profile', 'path': risk_return_plot},
        {'type': 'plot', 'title': 'Risk-Return Dashboard', 'path': roi_drawdown_plot},
        {'type': 'plot', 'title': 'Cash Position Analysis', 'path': cash_plot},
        {'type': 'text', 'text': 'This chart shows the daily portfolio composition as a stacked bar chart, combining cash position and total stock market value. Each bar represents a trading day, with the cash position at the base and the total value of all stocks stacked on top. Value labels show the cash amount, stock value, and total portfolio value for each day. Negative cash balances indicate either additional cash was added during the period or trades were executed with margin/borrowed funds.'}
    ]
    report_content.add_section('performance-analysis', 'Performance Analysis', performance_content)
    
    # Portfolio Composition Section
    composition_content = [
        {'type': 'plot', 'title': 'Current Holdings Analysis', 'path': composition_plot},
        {'type': 'plot', 'title': 'Position Size Analysis', 'path': position_analysis_plot},
        {'type': 'plot', 'title': 'Category Analysis', 'path': sector_analysis_plot},
        {'type': 'plot', 'title': 'Comparative Portfolio Analysis', 'path': comparative_plot}
    ]
    report_content.add_section('portfolio-composition', 'Portfolio Composition & Allocation', composition_content)
    
    # Risk Metrics Section
    report_content.add_section('risk-metrics', 'Risk Metrics', [])
    
    # Win/Loss Analysis Section
    win_loss_content = [
        {'type': 'plot', 'title': 'Win/Loss Distribution', 'path': win_loss_plot}
    ]
    report_content.add_section('win-loss-analysis', 'Win/Loss Analysis', win_loss_content)
    
    # Detailed Position Analysis Section
    position_content = [
        {'type': 'table', 'title': 'All Stocks Ever Purchased', 'data': all_stocks_display},
        {'type': 'table', 'title': 'Currently Held Stocks', 'data': current_stocks_display}
    ]
    report_content.add_section('detailed-position-analysis', 'Detailed Position Analysis', position_content)
    
    # Generate HTML report using new template system
    html_report_path = html_generator.generate_report(report_content)
    print(f"Saved HTML report to: {html_report_path}")
    
    # Generate Markdown report
    markdown_report_path = markdown_generator.generate_report(report_content)
    print(f"Saved Markdown report to: {markdown_report_path}")
    
    # Print summary to console
    print("\n" + "="*80)
    print("CHATGPT MICRO CAP EXPERIMENT - PROFESSIONAL FINANCIAL REPORT")
    print("="*80)
    # Use the specified report date if provided, otherwise use current date
    if args.date:
        try:
            report_datetime = datetime.strptime(args.date, "%Y-%m-%d")
            formatted_report_date = report_datetime.strftime('%Y-%m-%d')
        except ValueError:
            formatted_report_date = datetime.now().strftime('%Y-%m-%d')
    else:
        formatted_report_date = datetime.now().strftime('%Y-%m-%d')
    print(f"Report Date: {formatted_report_date}")
    print(f"Total Portfolio Value: ${summary_stats['total_value']:.2f}")
    print(f"Trade ROI: {summary_stats['overall_roi']:.2f}% ({ '+$' if summary_stats['absolute_gain'] >= 0 else '-$' }{abs(summary_stats['absolute_gain']):.2f})")
    print(f"Portfolio ROI: {summary_stats['separate_roi_pct']:.2f}%")
    print(f"Annualized Volatility: {volatility_metrics['annualized_volatility']:.2f}%")
    print(f"Sharpe Ratio: {volatility_metrics['sharpe_ratio']:.2f}")
    print(f"Win Rate: {win_loss_metrics['win_rate']:.1f}% ({win_loss_metrics['winning_positions']}/{win_loss_metrics['total_positions']})")
    print(f"Average Win: {win_loss_metrics['avg_win']:.1f}% | Average Loss: {win_loss_metrics['avg_loss']:.1f}%")
    
    print("\nRisk Metrics:")
    print("-"*30)
    print(f"Average Drawdown: {summary_stats['avg_drawdown']:.2f}%")
    print(f"Worst Drawdown: {summary_stats['worst_drawdown_value']:.2f}% ({summary_stats['worst_drawdown_ticker']})")
    print(f"Best Drawdown: {summary_stats['best_drawdown_value']:.2f}% ({summary_stats['best_drawdown_ticker']})")
    print(f"Stocks with >10% Drawdown: {summary_stats['significant_drawdown_count']}")
    
    print(f"\nReports saved to: {reports_dir}")
    print("Open 'index.html' in your browser to view the full professional report.")
    print("Open 'index.md' to view the Markdown version of the report.")


if __name__ == "__main__":
    main()