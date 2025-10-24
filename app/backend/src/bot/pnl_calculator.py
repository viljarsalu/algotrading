"""PNL Calculator - Position Profit & Loss Calculations.

This module provides comprehensive PNL calculation functions for trading positions,
including realized and unrealized PNL, fees, and performance metrics.
"""

import logging
from typing import Dict, Any, Optional, Tuple, List
from decimal import Decimal
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class PositionSide(Enum):
    """Position side enumeration."""
    LONG = "LONG"
    SHORT = "SHORT"


class PNLCalculator:
    """Calculate PNL for trading positions."""

    @staticmethod
    def parse_fill_data(fill: Dict[str, Any]) -> Dict[str, Any]:
        """Parse raw fill data from dYdX API.

        Args:
            fill: Raw fill record from API

        Returns:
            Parsed fill data with converted values
        """
        # dYdX uses quantums (smallest unit)
        # 1 token = 1e6 quantums
        quantums_per_token = 1e6

        size = Decimal(fill.get("quantums", 0)) / Decimal(quantums_per_token)
        price = Decimal(fill.get("price", 0)) / Decimal(1e9)  # Price in quantums
        quote_amount = Decimal(fill.get("quoteAmount", 0)) / Decimal(1e18)

        return {
            "id": fill.get("id"),
            "order_id": fill.get("orderId"),
            "side": fill.get("side"),  # BUY or SELL
            "size": float(size),
            "price": float(price),
            "quote_amount": float(quote_amount),
            "timestamp": fill.get("createdAt"),
            "height": fill.get("createdAtHeight"),
        }

    @staticmethod
    def calculate_average_entry_price(
        fills: List[Dict[str, Any]], side: PositionSide
    ) -> float:
        """Calculate average entry price from fills.

        Args:
            fills: List of fill records
            side: Position side (LONG or SHORT)

        Returns:
            Average entry price
        """
        if not fills:
            return 0.0

        # Filter fills by side
        side_str = "BUY" if side == PositionSide.LONG else "SELL"
        entry_fills = [f for f in fills if f["side"] == side_str]

        if not entry_fills:
            return 0.0

        # Calculate weighted average price
        total_size = sum(f["size"] for f in entry_fills)
        total_cost = sum(f["size"] * f["price"] for f in entry_fills)

        if total_size == 0:
            return 0.0

        average_price = total_cost / total_size
        return average_price

    @staticmethod
    def calculate_exit_price(
        fills: List[Dict[str, Any]], side: PositionSide
    ) -> float:
        """Calculate average exit price from fills.

        Args:
            fills: List of fill records
            side: Position side (LONG or SHORT)

        Returns:
            Average exit price
        """
        if not fills:
            return 0.0

        # Filter fills by opposite side (exit fills)
        side_str = "SELL" if side == PositionSide.LONG else "BUY"
        exit_fills = [f for f in fills if f["side"] == side_str]

        if not exit_fills:
            return 0.0

        # Calculate weighted average price
        total_size = sum(f["size"] for f in exit_fills)
        total_cost = sum(f["size"] * f["price"] for f in exit_fills)

        if total_size == 0:
            return 0.0

        average_price = total_cost / total_size
        return average_price

    @staticmethod
    def calculate_realized_pnl(
        entry_price: float,
        exit_price: float,
        position_size: float,
        side: PositionSide,
        fees: float = 0.0,
    ) -> float:
        """Calculate realized PNL for a closed position.

        Args:
            entry_price: Average entry price
            exit_price: Average exit price
            position_size: Total position size
            side: Position side (LONG or SHORT)
            fees: Total trading fees paid

        Returns:
            Realized PNL (positive = profit, negative = loss)
        """
        if entry_price == 0 or position_size == 0:
            return 0.0

        # Calculate price difference
        price_diff = exit_price - entry_price

        # For LONG positions: profit if exit > entry
        # For SHORT positions: profit if exit < entry (so negate)
        if side == PositionSide.LONG:
            pnl = price_diff * position_size
        else:  # SHORT
            pnl = -price_diff * position_size

        # Subtract fees
        pnl -= fees

        return pnl

    @staticmethod
    def calculate_unrealized_pnl(
        entry_price: float,
        current_price: float,
        position_size: float,
        side: PositionSide,
    ) -> float:
        """Calculate unrealized PNL for an open position.

        Args:
            entry_price: Entry price
            current_price: Current market price
            position_size: Position size
            side: Position side

        Returns:
            Unrealized PNL
        """
        if entry_price == 0 or position_size == 0:
            return 0.0

        price_diff = current_price - entry_price

        if side == PositionSide.LONG:
            unrealized_pnl = price_diff * position_size
        else:  # SHORT
            unrealized_pnl = -price_diff * position_size

        return unrealized_pnl

    @staticmethod
    def calculate_pnl_percentage(
        entry_price: float,
        exit_price: float,
        side: PositionSide,
    ) -> float:
        """Calculate PNL as percentage of entry price.

        Args:
            entry_price: Average entry price
            exit_price: Average exit price
            side: Position side

        Returns:
            PNL percentage (e.g., 5.0 for 5% profit)
        """
        if entry_price == 0:
            return 0.0

        price_diff = exit_price - entry_price

        if side == PositionSide.LONG:
            pnl_pct = (price_diff / entry_price) * 100
        else:  # SHORT
            pnl_pct = (-price_diff / entry_price) * 100

        return pnl_pct

    @staticmethod
    def calculate_total_fees(fills: List[Dict[str, Any]]) -> float:
        """Calculate total trading fees from fills.

        Args:
            fills: List of fill records

        Returns:
            Total fees in quote currency
        """
        total_fees = 0.0

        for fill in fills:
            # dYdX includes fees in the quote amount
            # Fee calculation: size * price * fee_rate
            # Typical fee rate: 0.05% (0.0005)
            size = fill.get("size", 0)
            price = fill.get("price", 0)
            fee_rate = 0.0005  # 0.05% default

            fee = size * price * fee_rate
            total_fees += fee

        return total_fees

    @staticmethod
    def calculate_funding_fees(
        position_size: float,
        funding_rate: float,
        hours_held: float,
    ) -> float:
        """Calculate funding fees for perpetual positions.

        Args:
            position_size: Position size
            funding_rate: Funding rate (typically 0.0001 to 0.001)
            hours_held: Number of hours position was held

        Returns:
            Funding fees paid
        """
        # Funding is typically paid every 8 hours
        # funding_fee = position_size * funding_rate * (hours_held / 8)
        funding_periods = hours_held / 8
        funding_fees = position_size * funding_rate * funding_periods

        return funding_fees

    @staticmethod
    def calculate_roi(
        realized_pnl: float,
        initial_margin: float,
    ) -> float:
        """Calculate Return on Investment (ROI).

        Args:
            realized_pnl: Realized PNL
            initial_margin: Initial margin used

        Returns:
            ROI percentage
        """
        if initial_margin == 0:
            return 0.0

        roi = (realized_pnl / initial_margin) * 100
        return roi

    @staticmethod
    def calculate_win_rate(
        closed_positions: List[Dict[str, Any]],
    ) -> float:
        """Calculate win rate from closed positions.

        Args:
            closed_positions: List of closed position records

        Returns:
            Win rate (0.0 to 1.0)
        """
        if not closed_positions:
            return 0.0

        winning_positions = [
            p for p in closed_positions if p.get("realized_pnl", 0) > 0
        ]

        win_rate = len(winning_positions) / len(closed_positions)
        return win_rate

    @staticmethod
    def calculate_average_win(
        closed_positions: List[Dict[str, Any]],
    ) -> float:
        """Calculate average winning trade.

        Args:
            closed_positions: List of closed position records

        Returns:
            Average PNL of winning trades
        """
        winning_positions = [
            p for p in closed_positions if p.get("realized_pnl", 0) > 0
        ]

        if not winning_positions:
            return 0.0

        total_wins = sum(p.get("realized_pnl", 0) for p in winning_positions)
        average_win = total_wins / len(winning_positions)

        return average_win

    @staticmethod
    def calculate_average_loss(
        closed_positions: List[Dict[str, Any]],
    ) -> float:
        """Calculate average losing trade.

        Args:
            closed_positions: List of closed position records

        Returns:
            Average PNL of losing trades
        """
        losing_positions = [
            p for p in closed_positions if p.get("realized_pnl", 0) < 0
        ]

        if not losing_positions:
            return 0.0

        total_losses = sum(p.get("realized_pnl", 0) for p in losing_positions)
        average_loss = total_losses / len(losing_positions)

        return average_loss

    @staticmethod
    def calculate_profit_factor(
        closed_positions: List[Dict[str, Any]],
    ) -> float:
        """Calculate profit factor (gross profit / gross loss).

        Args:
            closed_positions: List of closed position records

        Returns:
            Profit factor (higher is better, >1.0 is profitable)
        """
        winning_positions = [
            p for p in closed_positions if p.get("realized_pnl", 0) > 0
        ]
        losing_positions = [
            p for p in closed_positions if p.get("realized_pnl", 0) < 0
        ]

        gross_profit = sum(p.get("realized_pnl", 0) for p in winning_positions)
        gross_loss = abs(sum(p.get("realized_pnl", 0) for p in losing_positions))

        if gross_loss == 0:
            return 0.0 if gross_profit == 0 else float("inf")

        profit_factor = gross_profit / gross_loss
        return profit_factor

    @staticmethod
    def calculate_max_drawdown(
        closed_positions: List[Dict[str, Any]],
    ) -> float:
        """Calculate maximum drawdown from closed positions.

        Args:
            closed_positions: List of closed position records

        Returns:
            Maximum drawdown percentage
        """
        if not closed_positions:
            return 0.0

        cumulative_pnl = 0.0
        peak = 0.0
        max_drawdown = 0.0

        for position in closed_positions:
            cumulative_pnl += position.get("realized_pnl", 0)
            if cumulative_pnl > peak:
                peak = cumulative_pnl

            drawdown = peak - cumulative_pnl
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        if peak == 0:
            return 0.0

        max_drawdown_pct = (max_drawdown / peak) * 100
        return max_drawdown_pct


class PNLSummary:
    """PNL calculation summary."""

    def __init__(
        self,
        position_id: str,
        symbol: str,
        side: PositionSide,
        entry_price: float,
        exit_price: Optional[float],
        current_price: Optional[float],
        position_size: float,
        entry_timestamp: datetime,
        exit_timestamp: Optional[datetime],
        realized_pnl: float,
        unrealized_pnl: float,
        total_fees: float,
        pnl_percentage: float,
        status: str,
    ):
        """Initialize PNL summary.

        Args:
            position_id: Position ID
            symbol: Trading pair symbol
            side: Position side
            entry_price: Entry price
            exit_price: Exit price (None if open)
            current_price: Current market price
            position_size: Position size
            entry_timestamp: Entry timestamp
            exit_timestamp: Exit timestamp (None if open)
            realized_pnl: Realized PNL
            unrealized_pnl: Unrealized PNL
            total_fees: Total fees
            pnl_percentage: PNL percentage
            status: Position status (open/closed)
        """
        self.position_id = position_id
        self.symbol = symbol
        self.side = side
        self.entry_price = entry_price
        self.exit_price = exit_price
        self.current_price = current_price
        self.position_size = position_size
        self.entry_timestamp = entry_timestamp
        self.exit_timestamp = exit_timestamp
        self.realized_pnl = realized_pnl
        self.unrealized_pnl = unrealized_pnl
        self.total_fees = total_fees
        self.pnl_percentage = pnl_percentage
        self.status = status

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "position_id": self.position_id,
            "symbol": self.symbol,
            "side": self.side.value,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "current_price": self.current_price,
            "position_size": self.position_size,
            "entry_timestamp": (
                self.entry_timestamp.isoformat()
                if self.entry_timestamp
                else None
            ),
            "exit_timestamp": (
                self.exit_timestamp.isoformat()
                if self.exit_timestamp
                else None
            ),
            "realized_pnl": self.realized_pnl,
            "unrealized_pnl": self.unrealized_pnl,
            "total_fees": self.total_fees,
            "pnl_percentage": self.pnl_percentage,
            "status": self.status,
        }
