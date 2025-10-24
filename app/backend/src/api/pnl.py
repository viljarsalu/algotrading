"""PNL API Endpoints - Position Profit & Loss Queries.

This module provides API endpoints for querying PNL data, position analytics,
and performance metrics.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..db.models import Position, User
from ..core.security import get_current_user, verify_jwt_token
from ..bot.pnl_calculator import PNLCalculator, PositionSide, PNLSummary

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pnl", tags=["pnl"])


@router.get("/positions/{position_id}")
async def get_position_pnl(
    position_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get PNL summary for a specific position.

    Args:
        position_id: Position ID
        db: Database session
        current_user: Current authenticated user

    Returns:
        PNL summary for the position
    """
    try:
        # Get position from database
        position = db.query(Position).filter(
            Position.id == position_id,
            Position.user_id == current_user.id
        ).first()

        if not position:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Position not found"
            )

        # Determine if position is open or closed
        is_closed = position.status == "closed"

        # Get entry and exit prices
        entry_price = float(position.entry_price) if position.entry_price else 0.0
        exit_price = float(position.exit_price) if position.exit_price else None
        current_price = float(position.current_price) if position.current_price else 0.0

        # Determine position side
        side = PositionSide[position.side.upper()]

        # Calculate PNL
        if is_closed and exit_price:
            realized_pnl = PNLCalculator.calculate_realized_pnl(
                entry_price=entry_price,
                exit_price=exit_price,
                position_size=float(position.size),
                side=side,
                fees=float(position.total_fees or 0),
            )
            pnl_percentage = PNLCalculator.calculate_pnl_percentage(
                entry_price=entry_price,
                exit_price=exit_price,
                side=side,
            )
            unrealized_pnl = 0.0
        else:
            unrealized_pnl = PNLCalculator.calculate_unrealized_pnl(
                entry_price=entry_price,
                current_price=current_price,
                position_size=float(position.size),
                side=side,
            )
            pnl_percentage = PNLCalculator.calculate_pnl_percentage(
                entry_price=entry_price,
                exit_price=current_price,
                side=side,
            )
            realized_pnl = 0.0

        # Create summary
        summary = PNLSummary(
            position_id=str(position.id),
            symbol=position.symbol,
            side=side,
            entry_price=entry_price,
            exit_price=exit_price,
            current_price=current_price,
            position_size=float(position.size),
            entry_timestamp=position.entry_timestamp,
            exit_timestamp=position.exit_timestamp,
            realized_pnl=realized_pnl,
            unrealized_pnl=unrealized_pnl,
            total_fees=float(position.total_fees or 0),
            pnl_percentage=pnl_percentage,
            status=position.status,
        )

        # Update database with calculated values
        position.realized_pnl = realized_pnl
        position.unrealized_pnl = unrealized_pnl
        position.pnl_percentage = pnl_percentage
        db.commit()

        return summary.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get position PNL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate PNL"
        )


@router.get("/summary")
async def get_pnl_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get PNL summary for all user positions.

    Returns:
        Overall PNL statistics
    """
    try:
        # Get all positions
        positions = db.query(Position).filter(
            Position.user_id == current_user.id
        ).all()

        # Calculate totals
        total_realized = sum(float(p.realized_pnl or 0) for p in positions)
        total_unrealized = sum(float(p.unrealized_pnl or 0) for p in positions)
        total_pnl = total_realized + total_unrealized
        total_fees = sum(float(p.total_fees or 0) for p in positions)

        # Get closed positions
        closed_positions = [p for p in positions if p.status == "closed"]
        open_positions = [p for p in positions if p.status == "open"]

        # Calculate win rate
        closed_pnls = [float(p.realized_pnl or 0) for p in closed_positions]
        winning_positions = [pnl for pnl in closed_pnls if pnl > 0]
        win_rate = (
            len(winning_positions) / len(closed_pnls)
            if closed_pnls
            else 0
        )

        # Calculate average win/loss
        if winning_positions:
            average_win = sum(winning_positions) / len(winning_positions)
        else:
            average_win = 0.0

        losing_pnls = [pnl for pnl in closed_pnls if pnl < 0]
        if losing_pnls:
            average_loss = sum(losing_pnls) / len(losing_pnls)
        else:
            average_loss = 0.0

        # Calculate profit factor
        gross_profit = sum(winning_positions) if winning_positions else 0
        gross_loss = abs(sum(losing_pnls)) if losing_pnls else 0
        profit_factor = (
            gross_profit / gross_loss if gross_loss > 0 else 0
        )

        return {
            "total_realized_pnl": total_realized,
            "total_unrealized_pnl": total_unrealized,
            "total_pnl": total_pnl,
            "total_fees": total_fees,
            "win_rate": win_rate,
            "average_win": average_win,
            "average_loss": average_loss,
            "profit_factor": profit_factor,
            "positions_count": len(positions),
            "closed_positions_count": len(closed_positions),
            "open_positions_count": len(open_positions),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get PNL summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate PNL summary"
        )


@router.get("/history")
async def get_pnl_history(
    limit: int = 50,
    offset: int = 0,
    symbol: Optional[str] = None,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get PNL history for user positions.

    Args:
        limit: Number of positions to return
        offset: Offset for pagination
        symbol: Optional symbol filter
        status_filter: Optional status filter (open/closed)
        db: Database session
        current_user: Current authenticated user

    Returns:
        List of positions with PNL data
    """
    try:
        # Build query
        query = db.query(Position).filter(Position.user_id == current_user.id)

        # Apply filters
        if symbol:
            query = query.filter(Position.symbol == symbol)
        if status_filter:
            query = query.filter(Position.status == status_filter)

        # Get total count
        total_count = query.count()

        # Apply pagination
        positions = query.order_by(Position.entry_timestamp.desc()).offset(
            offset
        ).limit(limit).all()

        # Convert to PNL summaries
        summaries = []
        for position in positions:
            try:
                entry_price = float(position.entry_price) if position.entry_price else 0.0
                exit_price = float(position.exit_price) if position.exit_price else None
                current_price = float(position.current_price) if position.current_price else 0.0

                side = PositionSide[position.side.upper()]

                if position.status == "closed" and exit_price:
                    realized_pnl = PNLCalculator.calculate_realized_pnl(
                        entry_price=entry_price,
                        exit_price=exit_price,
                        position_size=float(position.size),
                        side=side,
                        fees=float(position.total_fees or 0),
                    )
                    pnl_percentage = PNLCalculator.calculate_pnl_percentage(
                        entry_price=entry_price,
                        exit_price=exit_price,
                        side=side,
                    )
                    unrealized_pnl = 0.0
                else:
                    unrealized_pnl = PNLCalculator.calculate_unrealized_pnl(
                        entry_price=entry_price,
                        current_price=current_price,
                        position_size=float(position.size),
                        side=side,
                    )
                    pnl_percentage = PNLCalculator.calculate_pnl_percentage(
                        entry_price=entry_price,
                        exit_price=current_price,
                        side=side,
                    )
                    realized_pnl = 0.0

                summary = PNLSummary(
                    position_id=str(position.id),
                    symbol=position.symbol,
                    side=side,
                    entry_price=entry_price,
                    exit_price=exit_price,
                    current_price=current_price,
                    position_size=float(position.size),
                    entry_timestamp=position.entry_timestamp,
                    exit_timestamp=position.exit_timestamp,
                    realized_pnl=realized_pnl,
                    unrealized_pnl=unrealized_pnl,
                    total_fees=float(position.total_fees or 0),
                    pnl_percentage=pnl_percentage,
                    status=position.status,
                )
                summaries.append(summary.to_dict())

            except Exception as e:
                logger.error(f"Error processing position {position.id}: {e}")
                continue

        return {
            "positions": summaries,
            "total_count": total_count,
            "limit": limit,
            "offset": offset,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get PNL history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve PNL history"
        )


@router.get("/performance")
async def get_performance_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get detailed performance metrics.

    Returns:
        Comprehensive performance statistics
    """
    try:
        # Get all closed positions
        closed_positions = db.query(Position).filter(
            Position.user_id == current_user.id,
            Position.status == "closed"
        ).all()

        if not closed_positions:
            return {
                "message": "No closed positions",
                "timestamp": datetime.utcnow().isoformat(),
            }

        # Convert to PNL data
        pnl_data = []
        for position in closed_positions:
            entry_price = float(position.entry_price) if position.entry_price else 0.0
            exit_price = float(position.exit_price) if position.exit_price else 0.0
            side = PositionSide[position.side.upper()]

            realized_pnl = PNLCalculator.calculate_realized_pnl(
                entry_price=entry_price,
                exit_price=exit_price,
                position_size=float(position.size),
                side=side,
                fees=float(position.total_fees or 0),
            )

            pnl_data.append({
                "realized_pnl": realized_pnl,
                "symbol": position.symbol,
            })

        # Calculate metrics
        win_rate = PNLCalculator.calculate_win_rate(
            [{"realized_pnl": p["realized_pnl"]} for p in pnl_data]
        )
        average_win = PNLCalculator.calculate_average_win(
            [{"realized_pnl": p["realized_pnl"]} for p in pnl_data]
        )
        average_loss = PNLCalculator.calculate_average_loss(
            [{"realized_pnl": p["realized_pnl"]} for p in pnl_data]
        )
        profit_factor = PNLCalculator.calculate_profit_factor(
            [{"realized_pnl": p["realized_pnl"]} for p in pnl_data]
        )
        max_drawdown = PNLCalculator.calculate_max_drawdown(
            [{"realized_pnl": p["realized_pnl"]} for p in pnl_data]
        )

        total_pnl = sum(p["realized_pnl"] for p in pnl_data)
        total_trades = len(pnl_data)

        return {
            "total_trades": total_trades,
            "total_pnl": total_pnl,
            "win_rate": win_rate,
            "average_win": average_win,
            "average_loss": average_loss,
            "profit_factor": profit_factor,
            "max_drawdown": max_drawdown,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate performance metrics"
        )
