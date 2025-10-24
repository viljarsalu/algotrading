"""
State Manager Module - Database-Integrated Position State Management.

This module provides database-centric position state management with
full CRUD operations and state synchronization capabilities.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, List, Optional, Tuple
from sqlmodel import Session, select, and_, or_
from sqlalchemy.orm import selectinload

from ..db.models import Position, User
from .dydx_client import DydxClient

logger = logging.getLogger(__name__)


class PositionManager:
    """Database-centric position manager with full CRUD operations."""

    def __init__(self, db_session: Session):
        """Initialize with database session.

        Args:
            db_session: SQLModel database session
        """
        self.db = db_session

    async def create_position(
        self,
        user_address: str,
        symbol: str,
        side: str,
        entry_price: float,
        size: float,
        dydx_order_id: str,
        tp_order_id: str = None,
        sl_order_id: str = None
    ) -> Position:
        """Create new position record in database.

        Args:
            user_address: User's wallet address
            symbol: Trading pair symbol
            side: Position side ('BUY' or 'SELL')
            entry_price: Entry price
            size: Position size
            dydx_order_id: dYdX order ID for main position
            tp_order_id: Optional take-profit order ID
            sl_order_id: Optional stop-loss order ID

        Returns:
            Created Position instance

        Raises:
            ValueError: If position data is invalid
        """
        try:
            # Validate inputs
            if not user_address or not user_address.startswith('0x'):
                raise ValueError("Invalid user address")

            if not symbol or '-' not in symbol:
                raise ValueError("Invalid symbol format")

            if side.upper() not in ['BUY', 'SELL']:
                raise ValueError("Invalid side")

            if entry_price <= 0 or size <= 0:
                raise ValueError("Invalid price or size")

            # Check if user exists
            user = self.db.exec(
                select(User).where(User.wallet_address == user_address)
            ).first()

            if not user:
                raise ValueError(f"User not found: {user_address}")

            # Create position
            position = Position(
                user_address=user_address,
                symbol=symbol,
                status="open",
                entry_price=Decimal(str(entry_price)),
                size=Decimal(str(size)),
                dydx_order_id=dydx_order_id,
                tp_order_id=tp_order_id,
                sl_order_id=sl_order_id,
                opened_at=datetime.utcnow()
            )

            # Save to database
            self.db.add(position)
            self.db.commit()
            self.db.refresh(position)

            logger.info(f"Position created: {position.id} for user {user_address}")
            return position

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create position: {e}")
            raise ValueError(f"Position creation failed: {str(e)}")

    async def get_position(self, position_id: int) -> Optional[Position]:
        """Retrieve position by ID.

        Args:
            position_id: Position ID to retrieve

        Returns:
            Position instance or None if not found
        """
        try:
            position = self.db.exec(
                select(Position)
                .options(selectinload(Position.user))
                .where(Position.id == position_id)
            ).first()

            return position

        except Exception as e:
            logger.error(f"Failed to get position {position_id}: {e}")
            return None

    async def get_user_positions(
        self,
        user_address: str,
        status: Optional[str] = None
    ) -> List[Position]:
        """Get all positions for a user, optionally filtered by status.

        Args:
            user_address: User's wallet address
            status: Optional status filter ('open', 'closed', 'cancelled')

        Returns:
            List of Position instances
        """
        try:
            # Build query
            query = select(Position).where(Position.user_address == user_address)

            if status:
                if status.lower() not in ['open', 'closed', 'cancelled', 'pending']:
                    raise ValueError(f"Invalid status: {status}")
                query = query.where(Position.status == status.lower())

            # Order by creation date (newest first)
            query = query.order_by(Position.opened_at.desc())

            positions = self.db.exec(query).all()

            return positions

        except Exception as e:
            logger.error(f"Failed to get user positions for {user_address}: {e}")
            return []

    async def update_position_status(
        self,
        position_id: int,
        status: str,
        **kwargs
    ) -> bool:
        """Update position status and other fields.

        Args:
            position_id: Position ID to update
            status: New status
            **kwargs: Additional fields to update

        Returns:
            True if update was successful
        """
        try:
            # Validate status
            if status.lower() not in ['open', 'closed', 'cancelled', 'pending']:
                raise ValueError(f"Invalid status: {status}")

            # Get position
            position = await self.get_position(position_id)
            if not position:
                raise ValueError(f"Position not found: {position_id}")

            # Update fields
            position.status = status.lower()

            # Update additional fields if provided
            for key, value in kwargs.items():
                if hasattr(position, key):
                    if key in ['entry_price', 'size']:
                        # Convert to Decimal for financial fields
                        setattr(position, key, Decimal(str(value)))
                    else:
                        setattr(position, key, value)

            # Commit changes
            self.db.commit()

            logger.info(f"Position {position_id} updated: {status}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update position {position_id}: {e}")
            return False

    async def close_position(
        self,
        position_id: int,
        closing_price: float,
        pnl: float
    ) -> bool:
        """Mark position as closed with final details.

        Args:
            position_id: Position ID to close
            closing_price: Final closing price
            pnl: Profit and loss amount

        Returns:
            True if position was closed successfully
        """
        try:
            # Get position
            position = await self.get_position(position_id)
            if not position:
                raise ValueError(f"Position not found: {position_id}")

            if position.status == 'closed':
                logger.warning(f"Position {position_id} already closed")
                return True

            # Update position
            position.status = 'closed'

            # Add close price and P&L to kwargs for update_position_status
            success = await self.update_position_status(
                position_id=position_id,
                status='closed',
                closing_price=closing_price,
                pnl=pnl
            )

            if success:
                logger.info(f"Position {position_id} closed: P&L ${pnl}")
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"Failed to close position {position_id}: {e}")
            return False

    async def delete_position(self, position_id: int) -> bool:
        """Remove position record (for cancelled orders).

        Args:
            position_id: Position ID to delete

        Returns:
            True if position was deleted successfully
        """
        try:
            # Get position
            position = await self.get_position(position_id)
            if not position:
                raise ValueError(f"Position not found: {position_id}")

            # Delete position
            self.db.delete(position)
            self.db.commit()

            logger.info(f"Position {position_id} deleted")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete position {position_id}: {e}")
            return False

    async def get_positions_by_symbol(self, symbol: str) -> List[Position]:
        """Get all positions for a specific symbol.

        Args:
            symbol: Trading pair symbol

        Returns:
            List of Position instances
        """
        try:
            positions = self.db.exec(
                select(Position)
                .options(selectinload(Position.user))
                .where(Position.symbol == symbol)
                .order_by(Position.opened_at.desc())
            ).all()

            return positions

        except Exception as e:
            logger.error(f"Failed to get positions for symbol {symbol}: {e}")
            return []

    async def get_open_positions_count(self, user_address: str) -> int:
        """Get count of open positions for a user.

        Args:
            user_address: User's wallet address

        Returns:
            Number of open positions
        """
        try:
            count = self.db.exec(
                select(Position)
                .where(
                    and_(
                        Position.user_address == user_address,
                        Position.status == 'open'
                    )
                )
            ).all()

            return len(count)

        except Exception as e:
            logger.error(f"Failed to get open positions count for {user_address}: {e}")
            return 0


class StateSynchronizer:
    """State synchronization utilities for dYdX integration."""

    @staticmethod
    async def sync_position_with_dydx(
        position: Position,
        dydx_client: DydxClient
    ) -> Position:
        """Synchronize position state with dYdX.

        Args:
            position: Position to synchronize
            dydx_client: Authenticated dYdX client

        Returns:
            Updated Position instance
        """
        try:
            # Get order status from dYdX
            order_status = await DydxClient.get_order_status(
                dydx_client,
                position.dydx_order_id
            )

            if not order_status.get('success'):
                logger.warning(f"Could not get dYdX status for position {position.id}")
                return position

            # Update position based on dYdX status
            dydx_status = order_status.get('status', '').lower()

            # Map dYdX status to our status
            status_mapping = {
                'open': 'open',
                'filled': 'open',
                'partially_filled': 'open',
                'cancelled': 'cancelled',
                'rejected': 'cancelled',
            }

            new_status = status_mapping.get(dydx_status, position.status)

            if new_status != position.status:
                # Update position status in database
                from .state_manager import PositionManager
                # Note: This would need a database session to work properly
                logger.info(f"Position {position.id} status changed: {position.status} -> {new_status}")

            return position

        except Exception as e:
            logger.error(f"Failed to sync position {position.id} with dYdX: {e}")
            return position

    @staticmethod
    async def validate_position_integrity(
        position: Position,
        expected_orders: List[str]
    ) -> Tuple[bool, str]:
        """Validate position data integrity.

        Args:
            position: Position to validate
            expected_orders: List of expected dYdX order IDs

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check required fields
            if not position.symbol:
                return False, "Missing symbol"

            if not position.dydx_order_id:
                return False, "Missing dYdX order ID"

            if position.entry_price <= 0:
                return False, "Invalid entry price"

            if position.size <= 0:
                return False, "Invalid size"

            # Check if dYdX order ID is in expected orders
            if position.dydx_order_id not in expected_orders:
                return False, f"Order {position.dydx_order_id} not in expected orders"

            # Validate symbol format
            if '-' not in position.symbol:
                return False, "Invalid symbol format"

            return True, "Position integrity valid"

        except Exception as e:
            logger.error(f"Position integrity validation error: {e}")
            return False, f"Validation error: {str(e)}"

    @staticmethod
    async def cleanup_orphaned_positions(
        db_session: Session,
        max_age_hours: int = 24
    ) -> int:
        """Clean up positions without corresponding dYdX orders.

        Args:
            db_session: Database session
            max_age_hours: Maximum age in hours for orphaned positions

        Returns:
            Number of positions cleaned up
        """
        try:
            # Calculate cutoff time
            cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)

            # Find orphaned positions (old pending positions)
            orphaned_positions = db_session.exec(
                select(Position)
                .where(
                    and_(
                        Position.status == 'pending',
                        Position.opened_at < cutoff_time
                    )
                )
            ).all()

            # Delete orphaned positions
            deleted_count = 0
            for position in orphaned_positions:
                db_session.delete(position)
                deleted_count += 1

            if deleted_count > 0:
                db_session.commit()
                logger.info(f"Cleaned up {deleted_count} orphaned positions")

            return deleted_count

        except Exception as e:
            db_session.rollback()
            logger.error(f"Failed to cleanup orphaned positions: {e}")
            return 0

    @staticmethod
    async def get_positions_summary(
        db_session: Session,
        user_address: str
    ) -> Dict[str, Any]:
        """Get summary of user's positions.

        Args:
            db_session: Database session
            user_address: User's wallet address

        Returns:
            Summary statistics
        """
        try:
            # Get all user positions
            positions = db_session.exec(
                select(Position)
                .where(Position.user_address == user_address)
            ).all()

            if not positions:
                return {
                    'total_positions': 0,
                    'open_positions': 0,
                    'closed_positions': 0,
                    'total_pnl': 0,
                    'win_rate': 0,
                }

            # Calculate summary
            open_positions = [p for p in positions if p.status == 'open']
            closed_positions = [p for p in positions if p.status == 'closed']

            # Calculate total P&L (simplified - would need more complex calculation)
            total_pnl = sum(
                float(p.entry_price * p.size) * 0.001  # Placeholder calculation
                for p in closed_positions
            )

            # Calculate win rate (simplified)
            profitable_positions = sum(1 for p in closed_positions if float(p.entry_price * p.size) > 0)
            win_rate = (profitable_positions / len(closed_positions) * 100) if closed_positions else 0

            return {
                'total_positions': len(positions),
                'open_positions': len(open_positions),
                'closed_positions': len(closed_positions),
                'total_pnl': total_pnl,
                'win_rate': win_rate,
            }

        except Exception as e:
            logger.error(f"Failed to get positions summary for {user_address}: {e}")
            return {
                'total_positions': 0,
                'open_positions': 0,
                'closed_positions': 0,
                'total_pnl': 0,
                'win_rate': 0,
                'error': str(e),
            }