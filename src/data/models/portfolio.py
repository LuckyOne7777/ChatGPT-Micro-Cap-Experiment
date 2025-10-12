"""
Portfolio data model for the ChatGPT Micro Cap Experiment.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class PortfolioEntry:
    """Represents a single entry in the portfolio."""
    date: datetime
    ticker: str
    shares: float
    buy_price: float
    cost_basis: float
    stop_loss: float
    current_price: float
    total_value: float
    pnl: float
    action: str
    cash_balance: float
    total_equity: float
    
    def is_currently_held(self) -> bool:
        """Check if this position is currently held (shares > 0)."""
        return self.shares > 0