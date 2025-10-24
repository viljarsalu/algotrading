"""Trading Logic Audit - Verify Best Practices and Compliance.

This module provides comprehensive auditing of trading logic, order lifecycle,
and position management against dYdX v4 best practices.
"""

import logging
from typing import Dict, Any, List, Tuple, Optional
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)


class OrderStatus(Enum):
    """dYdX order status enumeration."""
    PENDING = "PENDING"
    OPEN = "OPEN"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class TimeInForce(Enum):
    """Time in force options for dYdX orders."""
    GTT = "GTT"  # Good-Till-Time
    IOC = "IOC"  # Immediate-or-Cancel
    FOK = "FOK"  # Fill-or-Kill


class TradingAudit:
    """Audit trading logic against best practices."""

    @staticmethod
    def validate_order_parameters(
        symbol: str,
        side: str,
        size: float,
        price: Optional[float] = None,
        time_in_force: str = "GTT",
    ) -> Tuple[bool, List[str]]:
        """Validate order parameters against dYdX specifications.

        Args:
            symbol: Trading pair symbol (e.g., 'BTC-USD')
            side: Order side ('BUY' or 'SELL')
            size: Order size
            price: Order price (required for limit orders)
            time_in_force: Time in force ('GTT', 'IOC', 'FOK')

        Returns:
            Tuple of (is_valid, list of errors)
        """
        errors = []

        # Validate symbol format
        if not symbol or "-" not in symbol:
            errors.append(f"Invalid symbol format: {symbol} (expected: BASE-QUOTE)")

        # Validate side
        if side.upper() not in ["BUY", "SELL"]:
            errors.append(f"Invalid side: {side} (must be BUY or SELL)")

        # Validate size
        if size <= 0:
            errors.append(f"Invalid size: {size} (must be positive)")

        # Validate price for limit orders
        if time_in_force != "IOC" and (price is None or price <= 0):
            errors.append(f"Invalid price: {price} (must be positive for {time_in_force})")

        # Validate time in force
        try:
            TimeInForce[time_in_force.upper()]
        except KeyError:
            errors.append(
                f"Invalid time_in_force: {time_in_force} "
                f"(must be GTT, IOC, or FOK)"
            )

        return len(errors) == 0, errors

    @staticmethod
    def validate_order_lifecycle(
        order_id: str,
        current_status: str,
        previous_status: Optional[str] = None,
    ) -> Tuple[bool, List[str]]:
        """Validate order status transitions.

        Args:
            order_id: Order ID
            current_status: Current order status
            previous_status: Previous order status

        Returns:
            Tuple of (is_valid, list of errors)
        """
        errors = []

        # Validate status is valid
        try:
            OrderStatus[current_status.upper()]
        except KeyError:
            errors.append(
                f"Invalid order status: {current_status} "
                f"(must be PENDING, OPEN, FILLED, PARTIALLY_FILLED, "
                f"CANCELLED, REJECTED, or EXPIRED)"
            )
            return False, errors

        # Validate status transitions
        valid_transitions = {
            "PENDING": ["OPEN", "REJECTED"],
            "OPEN": ["FILLED", "PARTIALLY_FILLED", "CANCELLED", "EXPIRED"],
            "PARTIALLY_FILLED": ["FILLED", "CANCELLED", "EXPIRED"],
            "FILLED": [],  # Terminal state
            "CANCELLED": [],  # Terminal state
            "REJECTED": [],  # Terminal state
            "EXPIRED": [],  # Terminal state
        }

        if previous_status:
            previous_upper = previous_status.upper()
            current_upper = current_status.upper()

            if previous_upper not in valid_transitions:
                errors.append(f"Unknown previous status: {previous_status}")
            elif current_upper not in valid_transitions[previous_upper]:
                errors.append(
                    f"Invalid status transition: {previous_status} → {current_status}"
                )

        return len(errors) == 0, errors

    @staticmethod
    def validate_position_lifecycle(
        position_id: str,
        entry_order_status: str,
        tp_order_status: Optional[str] = None,
        sl_order_status: Optional[str] = None,
    ) -> Tuple[bool, List[str]]:
        """Validate position lifecycle and order relationships.

        Args:
            position_id: Position ID
            entry_order_status: Entry order status
            tp_order_status: Take profit order status
            sl_order_status: Stop loss order status

        Returns:
            Tuple of (is_valid, list of errors)
        """
        errors = []

        # Entry order must be filled or partially filled
        entry_upper = entry_order_status.upper()
        if entry_upper not in ["FILLED", "PARTIALLY_FILLED", "OPEN"]:
            errors.append(
                f"Entry order must be FILLED, PARTIALLY_FILLED, or OPEN, "
                f"got {entry_order_status}"
            )

        # If entry is filled, TP/SL should exist
        if entry_upper == "FILLED":
            if not tp_order_status:
                errors.append("Take profit order missing for filled entry")
            if not sl_order_status:
                errors.append("Stop loss order missing for filled entry")

        # TP/SL orders should be OPEN or FILLED
        if tp_order_status:
            tp_upper = tp_order_status.upper()
            if tp_upper not in ["OPEN", "FILLED", "PARTIALLY_FILLED"]:
                errors.append(
                    f"TP order should be OPEN or FILLED, got {tp_order_status}"
                )

        if sl_order_status:
            sl_upper = sl_order_status.upper()
            if sl_upper not in ["OPEN", "FILLED", "PARTIALLY_FILLED"]:
                errors.append(
                    f"SL order should be OPEN or FILLED, got {sl_order_status}"
                )

        return len(errors) == 0, errors

    @staticmethod
    def validate_tp_sl_orders(
        entry_price: float,
        tp_price: float,
        sl_price: float,
        side: str,
    ) -> Tuple[bool, List[str]]:
        """Validate take profit and stop loss price levels.

        Args:
            entry_price: Entry price
            tp_price: Take profit price
            sl_price: Stop loss price
            side: Position side ('BUY' or 'SELL')

        Returns:
            Tuple of (is_valid, list of errors)
        """
        errors = []

        if entry_price <= 0:
            errors.append(f"Invalid entry price: {entry_price}")
        if tp_price <= 0:
            errors.append(f"Invalid TP price: {tp_price}")
        if sl_price <= 0:
            errors.append(f"Invalid SL price: {sl_price}")

        if side.upper() == "BUY":
            # For LONG: TP should be above entry, SL below entry
            if tp_price <= entry_price:
                errors.append(
                    f"TP price ({tp_price}) must be above entry ({entry_price}) "
                    f"for LONG position"
                )
            if sl_price >= entry_price:
                errors.append(
                    f"SL price ({sl_price}) must be below entry ({entry_price}) "
                    f"for LONG position"
                )
        elif side.upper() == "SELL":
            # For SHORT: TP should be below entry, SL above entry
            if tp_price >= entry_price:
                errors.append(
                    f"TP price ({tp_price}) must be below entry ({entry_price}) "
                    f"for SHORT position"
                )
            if sl_price <= entry_price:
                errors.append(
                    f"SL price ({sl_price}) must be above entry ({entry_price}) "
                    f"for SHORT position"
                )

        return len(errors) == 0, errors

    @staticmethod
    def validate_partial_fill_handling(
        original_size: float,
        filled_size: float,
        remaining_size: float,
    ) -> Tuple[bool, List[str]]:
        """Validate partial fill calculations.

        Args:
            original_size: Original order size
            filled_size: Filled size
            remaining_size: Remaining size

        Returns:
            Tuple of (is_valid, list of errors)
        """
        errors = []

        # Check sum
        total = filled_size + remaining_size
        if abs(total - original_size) > 0.0001:  # Allow small floating point error
            errors.append(
                f"Size mismatch: {filled_size} + {remaining_size} != {original_size}"
            )

        # Check ranges
        if filled_size < 0:
            errors.append(f"Filled size cannot be negative: {filled_size}")
        if remaining_size < 0:
            errors.append(f"Remaining size cannot be negative: {remaining_size}")
        if filled_size > original_size:
            errors.append(f"Filled size ({filled_size}) exceeds original ({original_size})")

        return len(errors) == 0, errors

    @staticmethod
    def validate_order_cancellation(
        order_status: str,
        reason: Optional[str] = None,
    ) -> Tuple[bool, List[str]]:
        """Validate order cancellation logic.

        Args:
            order_status: Current order status
            reason: Cancellation reason

        Returns:
            Tuple of (is_valid, list of errors)
        """
        errors = []

        status_upper = order_status.upper()

        # Can only cancel OPEN or PARTIALLY_FILLED orders
        if status_upper not in ["OPEN", "PARTIALLY_FILLED"]:
            errors.append(
                f"Cannot cancel order with status {order_status} "
                f"(only OPEN or PARTIALLY_FILLED can be cancelled)"
            )

        # Reason should be provided
        if not reason:
            errors.append("Cancellation reason should be provided")

        return len(errors) == 0, errors

    @staticmethod
    def validate_position_closure(
        position_status: str,
        entry_order_status: str,
        tp_order_status: Optional[str] = None,
        sl_order_status: Optional[str] = None,
    ) -> Tuple[bool, List[str]]:
        """Validate position closure logic.

        Args:
            position_status: Position status
            entry_order_status: Entry order status
            tp_order_status: TP order status
            sl_order_status: SL order status

        Returns:
            Tuple of (is_valid, list of errors)
        """
        errors = []

        # Position must be OPEN to close
        if position_status.upper() != "OPEN":
            errors.append(
                f"Cannot close position with status {position_status} "
                f"(must be OPEN)"
            )

        # Entry order must be filled
        if entry_order_status.upper() not in ["FILLED", "PARTIALLY_FILLED"]:
            errors.append(
                f"Entry order must be filled to close position, "
                f"got {entry_order_status}"
            )

        # TP or SL should be filled (or one of them)
        tp_filled = tp_order_status and tp_order_status.upper() == "FILLED"
        sl_filled = sl_order_status and sl_order_status.upper() == "FILLED"

        if not (tp_filled or sl_filled):
            # Allow manual closure without TP/SL filled
            logger.warning("Position closure without TP/SL filled (manual closure)")

        return len(errors) == 0, errors

    @staticmethod
    def generate_audit_report(
        positions: List[Dict[str, Any]],
        orders: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generate comprehensive audit report.

        Args:
            positions: List of position records
            orders: List of order records

        Returns:
            Audit report with findings
        """
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_positions": len(positions),
            "total_orders": len(orders),
            "issues": [],
            "warnings": [],
            "statistics": {
                "positions_by_status": {},
                "orders_by_status": {},
                "tp_sl_coverage": 0,
                "partial_fill_count": 0,
            },
        }

        # Analyze positions
        for position in positions:
            status = position.get("status", "unknown")
            report["statistics"]["positions_by_status"][status] = (
                report["statistics"]["positions_by_status"].get(status, 0) + 1
            )

            # Check TP/SL coverage
            if position.get("status") == "open":
                if position.get("tp_order_id") and position.get("sl_order_id"):
                    report["statistics"]["tp_sl_coverage"] += 1

        # Analyze orders
        for order in orders:
            status = order.get("status", "unknown")
            report["statistics"]["orders_by_status"][status] = (
                report["statistics"]["orders_by_status"].get(status, 0) + 1
            )

            # Check partial fills
            if status == "PARTIALLY_FILLED":
                report["statistics"]["partial_fill_count"] += 1

        # Calculate TP/SL coverage percentage
        open_positions = report["statistics"]["positions_by_status"].get("open", 0)
        if open_positions > 0:
            coverage = (
                report["statistics"]["tp_sl_coverage"] / open_positions * 100
            )
            report["statistics"]["tp_sl_coverage_pct"] = coverage
        else:
            report["statistics"]["tp_sl_coverage_pct"] = 0

        return report


class AuditLogger:
    """Logging for trading audit events."""

    @staticmethod
    def log_order_created(
        order_id: str,
        symbol: str,
        side: str,
        size: float,
        price: Optional[float] = None,
    ) -> None:
        """Log order creation."""
        logger.info(
            f"Order created: {order_id} | {symbol} {side} {size} @ {price}"
        )

    @staticmethod
    def log_order_status_change(
        order_id: str,
        previous_status: str,
        new_status: str,
    ) -> None:
        """Log order status change."""
        logger.info(
            f"Order status changed: {order_id} | {previous_status} → {new_status}"
        )

    @staticmethod
    def log_position_opened(
        position_id: str,
        symbol: str,
        side: str,
        size: float,
        entry_price: float,
    ) -> None:
        """Log position opening."""
        logger.info(
            f"Position opened: {position_id} | {symbol} {side} {size} @ {entry_price}"
        )

    @staticmethod
    def log_position_closed(
        position_id: str,
        symbol: str,
        exit_price: float,
        pnl: float,
        reason: str,
    ) -> None:
        """Log position closure."""
        logger.info(
            f"Position closed: {position_id} | {symbol} @ {exit_price} | "
            f"PNL: {pnl} | Reason: {reason}"
        )

    @staticmethod
    def log_validation_error(
        entity_type: str,
        entity_id: str,
        errors: List[str],
    ) -> None:
        """Log validation errors."""
        logger.error(
            f"Validation error in {entity_type} {entity_id}: "
            f"{'; '.join(errors)}"
        )

    @staticmethod
    def log_audit_issue(
        issue_type: str,
        description: str,
        severity: str = "WARNING",
    ) -> None:
        """Log audit issue."""
        if severity == "ERROR":
            logger.error(f"Audit issue ({issue_type}): {description}")
        elif severity == "WARNING":
            logger.warning(f"Audit issue ({issue_type}): {description}")
        else:
            logger.info(f"Audit issue ({issue_type}): {description}")
