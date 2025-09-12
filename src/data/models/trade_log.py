"""
Trade log data model for the ChatGPT Micro Cap Experiment.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class TradeEntry:
    """Represents a single entry in the trade log."""
    date: datetime
    ticker: str
    shares_bought: float
    buy_price: float
    cost_basis: float
    pnl: float
    reason: str
    shares_sold: float
    sell_price: float