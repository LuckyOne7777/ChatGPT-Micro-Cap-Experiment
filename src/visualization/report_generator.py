"""
Base report generator for the ChatGPT Micro Cap Experiment.
This module defines the abstract base class for generating reports in multiple formats.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import pandas as pd


class ReportContent:
    """Container for report content that can be rendered in multiple formats."""
    
    def __init__(self, report_date: str = None):
        self.report_date = report_date or datetime.now().strftime("%Y-%m-%d")
        self.title = "ChatGPT Micro Cap Experiment"
        self.subtitle = "Professional Financial Performance Report"
        self.sections = []
        self.metrics = {}
        self.plots = {}
        self.tables = {}
        self.disclaimer = "This is a 6-month live trading experiment with real money ($100 initial investment) managed by ChatGPT. Past performance does not guarantee future results. This report is for educational and research purposes only."
        
    def add_section(self, section_id: str, title: str, content: List[Dict[str, Any]]):
        """Add a section to the report."""
        self.sections.append({
            'id': section_id,
            'title': title,
            'content': content
        })
        
    def set_metrics(self, metrics: Dict[str, Any]):
        """Set the metrics for the executive summary."""
        self.metrics = metrics
        
    def set_risk_metrics(self, risk_metrics: Dict[str, Any], advanced_risk_metrics: Dict[str, Any]):
        """Set the risk metrics for the risk metrics section."""
        self.metrics['risk_metrics'] = risk_metrics
        self.metrics['advanced_risk_metrics'] = advanced_risk_metrics
        
    def set_win_loss_metrics(self, win_loss_metrics: Dict[str, Any]):
        """Set the win/loss metrics for the win/loss analysis section."""
        self.metrics['win_loss_metrics'] = win_loss_metrics
        
    def add_plot(self, plot_id: str, title: str, path: str):
        """Add a plot to the report."""
        self.plots[plot_id] = {
            'title': title,
            'path': path
        }
        
    def add_table(self, table_id: str, title: str, data: pd.DataFrame):
        """Add a table to the report."""
        self.tables[table_id] = {
            'title': title,
            'data': data
        }


class ReportGenerator(ABC):
    """Abstract base class for report generators."""
    
    def __init__(self, reports_dir: Path):
        self.reports_dir = reports_dir
    
    @staticmethod
    def create_reports_directory(report_date: str = None) -> Path:
        """Create reports directory with specified date or current date subdirectory."""
        if report_date:
            # Validate date format
            try:
                datetime.strptime(report_date, "%Y-%m-%d")
                current_date = report_date
            except ValueError:
                raise SystemExit(f"Invalid date format '{report_date}'. Use YYYY-MM-DD.")
        else:
            current_date = datetime.now().strftime("%Y-%m-%d")
        reports_dir = Path("Reports") / current_date
        reports_dir.mkdir(parents=True, exist_ok=True)
        return reports_dir
    
    @abstractmethod
    def generate_report(self, content: ReportContent) -> str:
        """Generate a report from the provided content.
        
        Args:
            content: ReportContent object containing all the report data
            
        Returns:
            str: Path to the generated report file
        """
        pass
    
    @abstractmethod
    def _render_header(self, content: ReportContent) -> str:
        """Render the report header."""
        pass
    
    @abstractmethod
    def _render_navigation(self, content: ReportContent) -> str:
        """Render the navigation section."""
        pass
    
    @abstractmethod
    def _render_executive_summary(self, content: ReportContent) -> str:
        """Render the executive summary section."""
        pass
    
    @abstractmethod
    def _render_sections(self, content: ReportContent) -> str:
        """Render all sections of the report."""
        pass
    
    @abstractmethod
    def _render_footer(self, content: ReportContent) -> str:
        """Render the report footer."""
        pass