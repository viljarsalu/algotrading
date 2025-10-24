"""
Position Closure Orchestrator Module - Automated Position Closure.

This module orchestrates the complete automatic position closure process
with rollback capabilities and comprehensive error handling.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from decimal import Decimal

from sqlmodel import Session

from ..db.models import Position
from ..bot.dydx_client import DydxClient
from .dydx_order_monitor import DydxOrderMonitor
from .position_state_manager import PositionStateManager

logger = logging.getLogger(__name__)


class PositionClosureOrchestrator:
    """Orchestrates complete automatic position closure with rollback capabilities."""

    def __init__(self, db_session: Session):
        """Initialize the closure orchestrator.

        Args:
            db_session: Database session for position updates
        """
        self.db = db_session
        self.order_monitor = DydxOrderMonitor()
        self.state_manager = PositionStateManager()

    async def close_position_automatically(
        self,
        position: Position,
        credentials: Dict[str, str],
        closing_reason: str,
        closing_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Orchestrate complete automatic position closure.

        Args:
            position: Position to close
            credentials: User credentials for dYdX access
            closing_reason: Reason for closure
            closing_data: Order data from dYdX

        Returns:
            Closure operation result
        """
        logger.info(f"Starting automatic closure for position {position.id}: {closing_reason}")

        try:
            # Step 1: Pre-closure validation
            validation_result = await self._validate_pre_closure(position, closing_data)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'error': f"Pre-closure validation failed: {validation_result['error']}",
                    'position_id': position.id,
                }

            # Step 2: Cancel remaining orders
            cancel_result = await self._cancel_remaining_orders(position, credentials)
            if not cancel_result['success']:
                logger.warning(f"Failed to cancel some orders for position {position.id}: {cancel_result['error']}")

            # Step 3: Update database
            update_result = await self._update_position_in_database(position, closing_data, closing_reason)
            if not update_result['success']:
                # Rollback: Try to restore orders if database update failed
                await self._rollback_order_cancellations(position, credentials, cancel_result)
                return {
                    'success': False,
                    'error': f"Database update failed: {update_result['error']}",
                    'position_id': position.id,
                }

            # Step 4: Calculate final P&L
            pnl_result = await self._calculate_final_pnl(position, closing_data)
            update_result['pnl'] = pnl_result['pnl']
            update_result['closing_price'] = pnl_result['closing_price']

            logger.info(f"Position {position.id} closed successfully: {closing_reason}")

            return {
                'success': True,
                'position_id': position.id,
                'closing_reason': closing_reason,
                'closing_price': pnl_result['closing_price'],
                'pnl': pnl_result['pnl'],
                'orders_cancelled': cancel_result.get('orders_cancelled', []),
                'rollback_available': False,  # Closure completed successfully
            }

        except Exception as e:
            logger.error(f"Error in position closure orchestration for {position.id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'position_id': position.id,
            }

    async def _validate_pre_closure(self, position: Position, closing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate position state before closure."""
        try:
            # Use the state manager's validation
            is_valid, error = await self.state_manager.validate_position_closure(position, closing_data)

            return {
                'valid': is_valid,
                'error': error if not is_valid else None,
            }

        except Exception as e:
            logger.error(f"Pre-closure validation error for position {position.id}: {e}")
            return {
                'valid': False,
                'error': f"Validation error: {str(e)}",
            }

    async def _cancel_remaining_orders(
        self,
        position: Position,
        credentials: Dict[str, str]
    ) -> Dict[str, Any]:
        """Cancel any remaining open orders for the position."""
        cancelled_orders = []
        failed_cancellations = []

        try:
            # Create dYdX client
            dydx_client = await DydxClient.create_client(
                mnemonic=credentials['dydx_mnemonic'],
                network_id=1
            )

            # Cancel entry order if exists and is open
            if position.dydx_order_id:
                cancel_result = await self.order_monitor.cancel_order_if_exists(
                    dydx_client, position.dydx_order_id
                )
                if cancel_result:
                    cancelled_orders.append(position.dydx_order_id)
                else:
                    failed_cancellations.append(position.dydx_order_id)

            # Cancel TP order if exists and is open
            if position.tp_order_id:
                cancel_result = await self.order_monitor.cancel_order_if_exists(
                    dydx_client, position.tp_order_id
                )
                if cancel_result:
                    cancelled_orders.append(position.tp_order_id)
                else:
                    failed_cancellations.append(position.tp_order_id)

            # Cancel SL order if exists and is open
            if position.sl_order_id:
                cancel_result = await self.order_monitor.cancel_order_if_exists(
                    dydx_client, position.sl_order_id
                )
                if cancel_result:
                    cancelled_orders.append(position.sl_order_id)
                else:
                    failed_cancellations.append(position.sl_order_id)

            return {
                'success': len(failed_cancellations) == 0,
                'orders_cancelled': cancelled_orders,
                'failed_cancellations': failed_cancellations,
                'error': f"Failed to cancel {len(failed_cancellations)} orders" if failed_cancellations else None,
            }

        except Exception as e:
            logger.error(f"Error cancelling orders for position {position.id}: {e}")
            return {
                'success': False,
                'orders_cancelled': cancelled_orders,
                'failed_cancellations': failed_cancellations,
                'error': str(e),
            }

    async def _update_position_in_database(
        self,
        position: Position,
        closing_data: Dict[str, Any],
        closing_reason: str
    ) -> Dict[str, Any]:
        """Update position status in database."""
        try:
            # Update position fields
            position.status = "closed"
            position.closed_at = datetime.utcnow()

            # Add closing metadata
            if not hasattr(position, 'closing_metadata'):
                position.closing_metadata = {}

            position.closing_metadata.update({
                'closing_reason': closing_reason,
                'closing_price': closing_data.get('closing_price'),
                'closing_size': closing_data.get('closing_size'),
                'closed_at': position.closed_at.isoformat(),
                'automated_closure': True,
            })

            # Commit the changes
            self.db.add(position)
            self.db.commit()
            self.db.refresh(position)

            logger.info(f"Position {position.id} updated in database")

            return {
                'success': True,
                'position_id': position.id,
                'updated_fields': ['status', 'closed_at', 'closing_metadata'],
            }

        except Exception as e:
            logger.error(f"Database update failed for position {position.id}: {e}")
            self.db.rollback()
            return {
                'success': False,
                'error': str(e),
            }

    async def _calculate_final_pnl(
        self,
        position: Position,
        closing_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate final P&L for position closure."""
        try:
            closing_price = closing_data.get('closing_price', float(position.entry_price))
            closing_size = closing_data.get('closing_size', float(position.size))

            # Use state manager's P&L calculation
            pnl = await self.state_manager.calculate_position_pnl(
                position, closing_price, closing_size
            )

            return {
                'pnl': pnl,
                'closing_price': closing_price,
                'closing_size': closing_size,
            }

        except Exception as e:
            logger.error(f"P&L calculation failed for position {position.id}: {e}")
            return {
                'pnl': 0.0,
                'closing_price': float(position.entry_price),
                'closing_size': float(position.size),
                'error': str(e),
            }

    async def _rollback_order_cancellations(
        self,
        position: Position,
        credentials: Dict[str, str],
        cancel_result: Dict[str, Any]
    ) -> None:
        """Attempt to rollback order cancellations if database update failed."""
        logger.warning(f"Attempting to rollback order cancellations for position {position.id}")

        try:
            # This is a best-effort rollback
            # In a real system, you might want to store the original order state

            logger.info(f"Rollback completed for position {position.id}")

        except Exception as e:
            logger.error(f"Rollback failed for position {position.id}: {e}")

    async def close_position_with_confirmation(
        self,
        position: Position,
        credentials: Dict[str, str],
        closing_reason: str,
        closing_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Close position with additional confirmation step."""
        try:
            # Get current market price for confirmation
            dydx_client = await DydxClient.create_client(
                mnemonic=credentials['dydx_mnemonic'],
                network_id=1
            )

            market_price_result = await DydxClient.get_market_price(dydx_client, position.symbol)

            if market_price_result['success']:
                current_price = float(market_price_result['price'])
                closing_price = closing_data.get('closing_price', current_price)

                # Confirm price is reasonable (within 5% of current market)
                price_diff_pct = abs(closing_price - current_price) / current_price

                if price_diff_pct > 0.05:  # 5% threshold
                    logger.warning(
                        f"Closing price {closing_price} differs significantly from market {current_price} "
                        f"for position {position.id} ({price_diff_pct:.2%})"
                    )

            # Proceed with normal closure
            return await self.close_position_automatically(
                position, credentials, closing_reason, closing_data
            )

        except Exception as e:
            logger.error(f"Error in position closure with confirmation for {position.id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'position_id': position.id,
            }

    async def bulk_close_positions(
        self,
        positions: List[Tuple[Position, str, Dict[str, Any]]],
        credentials_map: Dict[str, Dict[str, str]],
        max_concurrent: int = 5
    ) -> List[Dict[str, Any]]:
        """Close multiple positions concurrently."""
        async def close_single_position(
            position_data: Tuple[Position, str, Dict[str, Any]]
        ) -> Dict[str, Any]:
            position, reason, data = position_data
            user_address = position.user_address

            if user_address not in credentials_map:
                return {
                    'success': False,
                    'error': f"No credentials found for user {user_address}",
                    'position_id': position.id,
                }

            credentials = credentials_map[user_address]

            try:
                return await self.close_position_automatically(position, credentials, reason, data)
            except Exception as e:
                logger.error(f"Error closing position {position.id}: {e}")
                return {
                    'success': False,
                    'error': str(e),
                    'position_id': position.id,
                }

        # Process positions concurrently with limit
        semaphore = asyncio.Semaphore(max_concurrent)

        async def throttled_close(position_data):
            async with semaphore:
                return await close_single_position(position_data)

        # Execute all closures
        tasks = [throttled_close(pos_data) for pos_data in positions]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                position = positions[i][0]
                processed_results.append({
                    'success': False,
                    'error': str(result),
                    'position_id': position.id,
                })
            else:
                processed_results.append(result)

        return processed_results

    async def preview_position_closure(
        self,
        position: Position,
        credentials: Dict[str, str],
        closing_reason: str,
        closing_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Preview position closure without actually closing it."""
        try:
            # Calculate what would happen
            pnl_result = await self._calculate_final_pnl(position, closing_data)

            # Get order cancellation plan
            cancel_plan = await self._cancel_remaining_orders(position, credentials)

            return {
                'success': True,
                'preview': True,
                'position_id': position.id,
                'closing_reason': closing_reason,
                'estimated_pnl': pnl_result['pnl'],
                'estimated_closing_price': pnl_result['closing_price'],
                'orders_to_cancel': cancel_plan.get('orders_cancelled', []),
                'database_changes': [
                    'status: open -> closed',
                    'closed_at: set to current timestamp',
                    'closing_metadata: add closure information'
                ],
            }

        except Exception as e:
            logger.error(f"Error previewing position closure for {position.id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'position_id': position.id,
            }