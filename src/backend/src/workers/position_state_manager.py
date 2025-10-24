"""
Position State Management Module - Position State Evaluation Logic.

This module handles the logic for evaluating position states and determining
when positions should be closed based on TP/SL orders and market conditions.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal
from datetime import datetime

from ..db.models import Position

logger = logging.getLogger(__name__)


class PositionStateManager:
    """Manages position state evaluation and closure decisions."""

    @staticmethod
    async def evaluate_position_state(
        position: Position,
        dydx_orders: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Determine if position should be closed based on order status.

        Args:
            position: Position to evaluate
            dydx_orders: Order status data from dYdX

        Returns:
            Tuple of (should_close, reason)
        """
        try:
            orders = dydx_orders.get('orders', {})

            # Check take profit order
            tp_should_close, tp_reason = await PositionStateManager._evaluate_tp_order(
                position, orders.get('tp', {})
            )

            if tp_should_close:
                return True, f"Take Profit: {tp_reason}"

            # Check stop loss order
            sl_should_close, sl_reason = await PositionStateManager._evaluate_sl_order(
                position, orders.get('sl', {})
            )

            if sl_should_close:
                return True, f"Stop Loss: {sl_reason}"

            # Check entry order status
            entry_should_close, entry_reason = await PositionStateManager._evaluate_entry_order(
                position, orders.get('entry', {})
            )

            if entry_should_close:
                return True, f"Entry Order: {entry_reason}"

            # Check for market-based conditions
            market_should_close, market_reason = await PositionStateManager._evaluate_market_conditions(
                position, orders
            )

            if market_should_close:
                return True, f"Market: {market_reason}"

            return False, "Position is active"

        except Exception as e:
            logger.error(f"Error evaluating position state for {position.id}: {e}")
            return False, f"Evaluation error: {str(e)}"

    @staticmethod
    async def _evaluate_tp_order(position: Position, tp_order: Dict[str, Any]) -> Tuple[bool, str]:
        """Evaluate take profit order status."""
        try:
            if not tp_order or tp_order.get('status') == 'NOT_FOUND':
                return False, "TP order not found"

            status = tp_order.get('status', '').upper()

            # Check if TP order is filled
            if status == 'FILLED':
                return True, "Take profit order filled"

            # Check if TP order is partially filled
            if status == 'PARTIALLY_FILLED':
                remaining_size = tp_order.get('remaining_size')
                if remaining_size and float(remaining_size) > 0:
                    return True, "Take profit order partially filled"
                else:
                    return False, "TP order partially filled but complete"

            # Check for error states
            if status in ['CANCELLED', 'EXPIRED']:
                return True, f"TP order {status.lower()}"

            return False, f"TP order status: {status}"

        except Exception as e:
            logger.error(f"Error evaluating TP order for position {position.id}: {e}")
            return False, f"TP evaluation error: {str(e)}"

    @staticmethod
    async def _evaluate_sl_order(position: Position, sl_order: Dict[str, Any]) -> Tuple[bool, str]:
        """Evaluate stop loss order status."""
        try:
            if not sl_order or sl_order.get('status') == 'NOT_FOUND':
                return False, "SL order not found"

            status = sl_order.get('status', '').upper()

            # Check if SL order is filled
            if status == 'FILLED':
                return True, "Stop loss order filled"

            # Check if SL order is partially filled
            if status == 'PARTIALLY_FILLED':
                remaining_size = sl_order.get('remaining_size')
                if remaining_size and float(remaining_size) > 0:
                    return True, "Stop loss order partially filled"
                else:
                    return False, "SL order partially filled but complete"

            # Check for error states
            if status in ['CANCELLED', 'EXPIRED']:
                return True, f"SL order {status.lower()}"

            return False, f"SL order status: {status}"

        except Exception as e:
            logger.error(f"Error evaluating SL order for position {position.id}: {e}")
            return False, f"SL evaluation error: {str(e)}"

    @staticmethod
    async def _evaluate_entry_order(position: Position, entry_order: Dict[str, Any]) -> Tuple[bool, str]:
        """Evaluate entry order status."""
        try:
            if not entry_order or entry_order.get('status') == 'NOT_FOUND':
                return False, "Entry order not found"

            status = entry_order.get('status', '').upper()

            # Check if entry order is filled (position should be fully opened)
            if status == 'FILLED':
                # Position is fully opened, continue monitoring TP/SL
                return False, "Entry order filled"

            # Check if entry order is partially filled
            if status == 'PARTIALLY_FILLED':
                remaining_size = entry_order.get('remaining_size')
                original_size = entry_order.get('size')

                if remaining_size and original_size:
                    filled_ratio = 1 - (float(remaining_size) / float(original_size))
                    if filled_ratio > 0.95:  # 95% filled
                        return False, f"Entry order {filled_ratio:.1%} filled"

                return False, "Entry order partially filled"

            # Check for error states
            if status in ['CANCELLED', 'EXPIRED']:
                return True, f"Entry order {status.lower()}"

            # Check if entry order failed
            if status in ['REJECTED', 'ERROR']:
                return True, f"Entry order {status.lower()}"

            return False, f"Entry order status: {status}"

        except Exception as e:
            logger.error(f"Error evaluating entry order for position {position.id}: {e}")
            return False, f"Entry evaluation error: {str(e)}"

    @staticmethod
    async def _evaluate_market_conditions(position: Position, orders: Dict[str, Any]) -> Tuple[bool, str]:
        """Evaluate market-based conditions for position closure."""
        try:
            # This is a simplified implementation
            # In a real system, you might want to check:
            # - Price volatility
            # - Market news/events
            # - Risk management rules
            # - Time-based exits
            # - Trailing stops

            # For now, we'll implement a simple time-based check
            # Close positions that have been open too long (e.g., 24 hours)
            if position.opened_at:
                hours_open = (datetime.utcnow() - position.opened_at).total_seconds() / 3600

                # Close positions open for more than 24 hours as a safety measure
                if hours_open > 24:
                    return True, f"Position open for {hours_open:.1f} hours"

            return False, "Market conditions normal"

        except Exception as e:
            logger.error(f"Error evaluating market conditions for position {position.id}: {e}")
            return False, f"Market evaluation error: {str(e)}"

    @staticmethod
    async def calculate_position_pnl(
        position: Position,
        closing_price: float,
        closing_size: float
    ) -> float:
        """Calculate final P&L for position closure.

        Args:
            position: Position being closed
            closing_price: Price at closure
            closing_size: Size at closure

        Returns:
            Calculated P&L
        """
        try:
            entry_price = float(position.entry_price)
            position_size = float(position.size)

            # Calculate P&L based on position side
            # Note: This is a simplified calculation
            # In reality, you'd need to know if this was a long or short position
            price_change = closing_price - entry_price
            pnl = price_change * position_size

            return pnl

        except Exception as e:
            logger.error(f"Error calculating P&L for position {position.id}: {e}")
            return 0.0

    @staticmethod
    async def determine_closing_reason(
        tp_order_status: str,
        sl_order_status: str,
        entry_order_status: str
    ) -> str:
        """Determine why position was closed (TP, SL, or manual).

        Args:
            tp_order_status: Take profit order status
            sl_order_status: Stop loss order status
            entry_order_status: Entry order status

        Returns:
            Closing reason string
        """
        try:
            # Check TP order first
            if tp_order_status.upper() in ['FILLED', 'PARTIALLY_FILLED']:
                return "TAKE_PROFIT"

            # Check SL order
            if sl_order_status.upper() in ['FILLED', 'PARTIALLY_FILLED']:
                return "STOP_LOSS"

            # Check entry order issues
            if entry_order_status.upper() in ['CANCELLED', 'EXPIRED', 'REJECTED']:
                return "ENTRY_FAILED"

            # Default to manual or market condition
            return "MARKET_CONDITION"

        except Exception as e:
            logger.error(f"Error determining closing reason: {e}")
            return "UNKNOWN"

    @staticmethod
    async def validate_position_closure(
        position: Position,
        closing_data: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Validate position closure data integrity.

        Args:
            position: Position being closed
            closing_data: Closure data from dYdX

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Validate position is actually open
            if position.status != "open":
                return False, f"Position {position.id} is not open (status: {position.status})"

            # Validate closing data structure
            if not closing_data:
                return False, "Closing data is empty"

            # Validate required fields
            required_fields = ['closing_price', 'closing_size', 'timestamp']
            for field in required_fields:
                if field not in closing_data:
                    return False, f"Missing required field: {field}"

            # Validate price is reasonable
            closing_price = closing_data.get('closing_price', 0)
            if closing_price <= 0:
                return False, f"Invalid closing price: {closing_price}"

            # Validate size is reasonable
            closing_size = closing_data.get('closing_size', 0)
            if closing_size <= 0:
                return False, f"Invalid closing size: {closing_size}"

            # Validate price is not too far from entry (basic sanity check)
            entry_price = float(position.entry_price)
            price_change_pct = abs(closing_price - entry_price) / entry_price

            if price_change_pct > 0.5:  # 50% price change seems extreme
                logger.warning(f"Large price change detected for position {position.id}: {price_change_pct:.2%}")

            return True, "Valid"

        except Exception as e:
            logger.error(f"Error validating position closure for {position.id}: {e}")
            return False, f"Validation error: {str(e)}"

    @staticmethod
    async def get_position_summary(position: Position, orders: Dict[str, Any]) -> Dict[str, Any]:
        """Get comprehensive position summary for monitoring.

        Args:
            position: Position to summarize
            orders: Order data from dYdX

        Returns:
            Position summary data
        """
        try:
            summary = {
                'position_id': position.id,
                'symbol': position.symbol,
                'status': position.status,
                'entry_price': float(position.entry_price),
                'size': float(position.size),
                'opened_at': position.opened_at.isoformat() if position.opened_at else None,
                'orders': {
                    'entry': orders.get('entry', {}).get('status', 'UNKNOWN'),
                    'tp': orders.get('tp', {}).get('status', 'UNKNOWN'),
                    'sl': orders.get('sl', {}).get('status', 'UNKNOWN'),
                },
                'health': 'good',
                'issues': []
            }

            # Check for potential issues
            issues = []

            # Check if position has been open too long
            if position.opened_at:
                hours_open = (datetime.utcnow() - position.opened_at).total_seconds() / 3600
                if hours_open > 48:
                    issues.append(f"Position open for {hours_open:.1f} hours")
                    summary['health'] = 'warning'

            # Check if orders are missing
            if summary['orders']['tp'] == 'NOT_FOUND':
                issues.append("Take profit order not found")
                summary['health'] = 'warning'

            if summary['orders']['sl'] == 'NOT_FOUND':
                issues.append("Stop loss order not found")
                summary['health'] = 'warning'

            # Check if entry order is not filled
            if summary['orders']['entry'] not in ['FILLED', 'PARTIALLY_FILLED']:
                issues.append(f"Entry order not filled (status: {summary['orders']['entry']})")
                summary['health'] = 'warning'

            summary['issues'] = issues

            return summary

        except Exception as e:
            logger.error(f"Error creating position summary for {position.id}: {e}")
            return {
                'position_id': position.id,
                'error': str(e),
                'health': 'error'
            }

    @staticmethod
    async def should_trigger_emergency_close(position: Position, market_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if position should be emergency closed due to extreme market conditions.

        Args:
            position: Position to evaluate
            market_data: Current market data

        Returns:
            Tuple of (should_close, reason)
        """
        try:
            # Check for extreme price movements
            current_price = market_data.get('price')
            if not current_price:
                return False, "No market price available"

            entry_price = float(position.entry_price)
            price_change_pct = abs(current_price - entry_price) / entry_price

            # Emergency close if price moved more than 20%
            if price_change_pct > 0.20:
                return True, f"Emergency close: {price_change_pct:.1%} price movement"

            # Check for extreme volatility (if available)
            # This would require additional market data

            return False, "No emergency conditions"

        except Exception as e:
            logger.error(f"Error checking emergency close for position {position.id}: {e}")
            return False, f"Emergency check error: {str(e)}"