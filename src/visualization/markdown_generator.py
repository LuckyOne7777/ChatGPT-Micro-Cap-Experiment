"""
Markdown report generation for the ChatGPT Micro Cap Experiment.
"""

import pandas as pd
from pathlib import Path
import os
from datetime import datetime
from .report_generator import ReportGenerator, ReportContent


class MarkdownGenerator(ReportGenerator):
    """Generator for Markdown reports."""
    
    def __init__(self, reports_dir: Path):
        super().__init__(reports_dir)
    
    def generate_report(self, content: ReportContent) -> str:
        """Generate a Markdown report from the provided content."""
        markdown_content = self._render_header(content)
        markdown_content += self._render_table_of_contents(content)
        markdown_content += self._render_executive_summary(content)
        markdown_content += self._render_sections(content)
        markdown_content += self._render_footer(content)
        
        # Save the markdown file
        md_path = self.reports_dir / "index.md"
        with open(md_path, "w") as f:
            f.write(markdown_content)
        return str(md_path)
    
    def _render_header(self, content: ReportContent) -> str:
        """Render the report header."""
        # Format the report date for display
        try:
            report_datetime = datetime.strptime(content.report_date, "%Y-%m-%d")
            formatted_report_date = report_datetime.strftime('%B %d, %Y')
        except ValueError:
            formatted_report_date = datetime.now().strftime('%B %d, %Y')
            
        return f"""# {content.title}
## {content.subtitle}

**Report Date:** {formatted_report_date}

---
"""
    
    def _render_table_of_contents(self, content: ReportContent) -> str:
        """Render the table of contents."""
        toc = "## Table of Contents\n\n"
        
        # Add executive summary
        toc += "- [Executive Summary](#executive-summary)\n"
        
        # Add all sections
        for i, section in enumerate(content.sections, 1):
            # Convert section title to lowercase and replace spaces with hyphens for anchor links
            anchor = section['title'].lower().replace(' ', '-').replace('/', '-').replace('&', 'and')
            toc += f"- [{section['title']}](#{anchor})\n"
            
            # Add subsections if they exist in the content
            for item in section['content']:
                if item['type'] == 'plot' or item['type'] == 'table':
                    # Create a subsection anchor
                    sub_anchor = item['title'].lower().replace(' ', '-').replace('/', '-').replace('&', 'and')
                    toc += f"  - [{item['title']}](#{sub_anchor})\n"
        
        # Add footer
        toc += "---\n\n"
        
        return toc
    
    def _render_executive_summary(self, content: ReportContent) -> str:
        """Render the executive summary section."""
        # Extract metrics for the summary
        summary_stats = content.metrics.get('summary_stats', {})
        volatility_metrics = content.metrics.get('volatility_metrics', {})
        win_loss_metrics = content.metrics.get('win_loss_metrics', {})
        
        summary = """## Executive Summary

> **Disclaimer:** This is a 6-month live trading experiment with real money ($100 initial investment) managed by ChatGPT. Past performance does not guarantee future results. This report is for educational and research purposes only.

### Key Metrics

| Metric | Value |
|--------|-------|
| Total Portfolio Value | ${:.2f} |
| Trade ROI | {:.2f}% ({}) |
| Portfolio ROI | {:.2f}% |
| Annualized Volatility | {:.2f}% |
| Sharpe Ratio | {:.2f} |
| Invested Value (Holdings) | ${:.2f} |

""".format(
            summary_stats.get('total_value', 0),
            summary_stats.get('overall_roi', 0),
            '${:.2f}'.format(summary_stats.get('absolute_gain', 0)),
            summary_stats.get('separate_roi_pct', 0),
            volatility_metrics.get('annualized_volatility', 0),
            volatility_metrics.get('sharpe_ratio', 0),
            summary_stats.get('invested_value_holdings', 0)
        )
        
        return summary
    
    def _render_navigation(self, content: ReportContent) -> str:
        """Render the navigation section."""
        # For Markdown, we use a table of contents instead of navigation
        return self._render_table_of_contents(content)
    
    def _render_sections(self, content: ReportContent) -> str:
        """Render all sections of the report."""
        sections_md = ""
        
        for section in content.sections:
            # Convert section title to lowercase and replace spaces with hyphens for anchor links
            anchor = section['title'].lower().replace(' ', '-').replace('/', '-').replace('&', 'and')
            
            section_md = f"## {section['title']}\n\n"
            
            # Special handling for Risk Metrics section
            if section['title'] == 'Risk Metrics':
                section_md += self._render_risk_metrics_section(content)
            # Special handling for Win/Loss Analysis section
            elif section['title'] == 'Win/Loss Analysis':
                section_md += self._render_win_loss_metrics_section(content)
                # Render section content normally
                for item in section['content']:
                    if item['type'] == 'plot':
                        # Create a subsection anchor
                        sub_anchor = item['title'].lower().replace(' ', '-').replace('/', '-').replace('&', 'and')
                        plot_name = os.path.basename(item['path'])
                        section_md += f"### {item['title']}\n\n"
                        section_md += f"![{item['title']}]({plot_name})\n\n"
            else:
                # Render section content
                for item in section['content']:
                    if item['type'] == 'plot':
                        # Create a subsection anchor
                        sub_anchor = item['title'].lower().replace(' ', '-').replace('/', '-').replace('&', 'and')
                        plot_name = os.path.basename(item['path'])
                        section_md += f"### {item['title']}\n\n"
                        section_md += f"![{item['title']}]({plot_name})\n\n"
                    elif item['type'] == 'table':
                        # Create a subsection anchor
                        sub_anchor = item['title'].lower().replace(' ', '-').replace('/', '-').replace('&', 'and')
                        section_md += f"### {item['title']}\n\n"
                        section_md += self._dataframe_to_markdown_table(item['data'])
                        section_md += "\n"
                    elif item['type'] == 'text':
                        section_md += f"{item['text']}\n\n"
            
            sections_md += section_md
        
        return sections_md
    
    def _dataframe_to_markdown_table(self, df: pd.DataFrame) -> str:
        """Convert a DataFrame to a Markdown table with proper formatting for TOTAL rows."""
        if df.empty:
            return "No data available\n"
        
        # Create the markdown table
        markdown_table = ""
        
        # Header row
        markdown_table += "| " + " | ".join(df.columns) + " |\n"
        markdown_table += "| " + " | ".join(["---"] * len(df.columns)) + " |\n"
        
        # Data rows
        for _, row in df.iterrows():
            # Check if this is a TOTAL row
            if str(row.iloc[0]).strip() == "TOTAL":
                # Format the TOTAL row with bold styling
                formatted_row = "|**" + "**|**".join(str(val) for val in row) + "**|\n"
                markdown_table += formatted_row
            else:
                markdown_table += "| " + " | ".join(str(val) for val in row) + " |\n"
        
        return markdown_table
    
    def _render_risk_metrics_section(self, content: ReportContent) -> str:
        """Render the risk metrics section with all 7 metrics."""
        risk_metrics = content.metrics.get('risk_metrics', {})
        advanced_risk_metrics = content.metrics.get('advanced_risk_metrics', {})
        
        risk_md = "### Risk Metrics Dashboard\n\n"
        
        # Create a markdown table for the risk metrics
        risk_md += "| Metric | Value | Description |\n"
        risk_md += "|--------|-------|-------------|\n"
        risk_md += f"| Average Drawdown | {risk_metrics.get('avg_drawdown', 0):.2f}% | Across All Positions |\n"
        risk_md += f"| Worst Drawdown | {risk_metrics.get('worst_drawdown_value', 0):.2f}% | {risk_metrics.get('worst_drawdown_ticker', 'N/A')} |\n"
        risk_md += f"| Best Drawdown | {risk_metrics.get('best_drawdown_value', 0):.2f}% | {risk_metrics.get('best_drawdown_ticker', 'N/A')} |\n"
        risk_md += f"| High Drawdown Stocks | {risk_metrics.get('significant_drawdown_count', 0)} | >10% Drawdown |\n"
        risk_md += f"| Sortino Ratio | {advanced_risk_metrics.get('sortino_ratio', 0):.2f} | Downside Risk-Adjusted Return |\n"
        risk_md += f"| Max Consecutive Wins | {advanced_risk_metrics.get('max_consecutive_wins', 0)} | Trading Days |\n"
        risk_md += f"| Max Consecutive Losses | {advanced_risk_metrics.get('max_consecutive_losses', 0)} | Trading Days |\n\n"
        
        return risk_md
    
    def _render_win_loss_metrics_section(self, content: ReportContent) -> str:
        """Render the win/loss metrics section with all 4 metrics."""
        win_loss_metrics = content.metrics.get('win_loss_metrics', {})
        
        win_loss_md = "### Win/Loss Metrics Dashboard\n\n"
        
        # Create a markdown table for the win/loss metrics
        win_loss_md += "| Metric | Value | Description |\n"
        win_loss_md += "|--------|-------|-------------|\n"
        win_loss_md += f"| Win Rate | {win_loss_metrics.get('win_rate', 0):.1f}% | {win_loss_metrics.get('winning_positions', 0)}/{win_loss_metrics.get('total_positions', 0)} Positions |\n"
        win_loss_md += f"| Average Win | {win_loss_metrics.get('avg_win', 0):.1f}% | Profitable Positions |\n"
        win_loss_md += f"| Average Loss | {win_loss_metrics.get('avg_loss', 0):.1f}% | Losing Positions |\n"
        win_loss_md += f"| Best Position | {win_loss_metrics.get('best_position', {}).get('ROI (%)', 0):.1f}% | {win_loss_metrics.get('best_position', {}).get('Ticker', 'N/A')} |\n\n"
        
        return win_loss_md
    
    def _render_footer(self, content: ReportContent) -> str:
        """Render the report footer."""
        return f"""## Footer

ChatGPT Micro Cap Experiment | Professional Financial Report | Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

This report is automatically generated and should be reviewed by a qualified financial professional before making investment decisions.
"""