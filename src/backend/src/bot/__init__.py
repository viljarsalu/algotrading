"""
dYdX Trading Bot Package - Core Trading Engine Components.

This package provides a complete stateless trading engine for dYdX protocol
with per-user credential handling and database integration.
"""

from .dydx_client import DydxClient
from .telegram_manager import TelegramManager
from .risk_manager import RiskManager, RiskParameters
from .state_manager import PositionManager, StateSynchronizer
from .trading_engine import TradingEngine

__version__ = "1.0.0"
__all__ = [
    "DydxClient",
    "TelegramManager",
    "RiskManager",
    "RiskParameters",
    "PositionManager",
    "StateSynchronizer",
    "TradingEngine",
]