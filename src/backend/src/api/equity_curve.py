"""Equity Curve API - Portfolio Growth Tracking.

This module provides endpoints for tracking portfolio equity over time,
showing starting capital vs current portfolio value with growth metrics.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..core.security import get_current_user
from ..db.models import User, Position
from ..bot.pnl_calculator import PNLCalculator, PositionSide

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/equity", tags=["equity"])


@router.get("/curve")
async def get_equity_curve(
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get equity curve data for portfolio tracking.

    Shows starting capital vs current portfolio value over time.

    Args:
        days: Number of days to retrieve (default 30)
        db: Database session
        current_user: Current authenticated user

    Returns:
        Equity curve data with timestamps and values
    """
    try:
        # Get all positions for user
        positions = db.query(Position).filter(
            Position.user_id == current_user.id
        ).all()

        if not positions:
            return {
                "status": "success",
                "starting_capital": 0,
                "current_equity": 0,
                "growth_amount": 0,
                "growth_percentage": 0,
                "curve_data": [],
                "message": "No positions found",
            }

        # Get starting capital (from user profile or first position)
        starting_capital = float(current_user.starting_capital or 10000)

        # Calculate current equity
        total_realized_pnl = sum(
            float(p.realized_pnl or 0) for p in positions
        )
        total_unrealized_pnl = sum(
            float(p.unrealized_pnl or 0) for p in positions
        )
        current_equity = starting_capital + total_realized_pnl + total_unrealized_pnl

        # Calculate growth
        growth_amount = current_equity - starting_capital
        growth_percentage = (growth_amount / starting_capital * 100) if starting_capital > 0 else 0

        # Generate equity curve data points
        curve_data = _generate_equity_curve(
            positions=positions,
            starting_capital=starting_capital,
            days=days
        )

        return {
            "status": "success",
            "starting_capital": starting_capital,
            "current_equity": current_equity,
            "growth_amount": growth_amount,
            "growth_percentage": growth_percentage,
            "curve_data": curve_data,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get equity curve: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve equity curve"
        )


@router.get("/summary")
async def get_equity_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get equity summary with key metrics.

    Returns:
        Equity summary with growth metrics
    """
    try:
        positions = db.query(Position).filter(
            Position.user_id == current_user.id
        ).all()

        starting_capital = float(current_user.starting_capital or 10000)

        total_realized_pnl = sum(
            float(p.realized_pnl or 0) for p in positions
        )
        total_unrealized_pnl = sum(
            float(p.unrealized_pnl or 0) for p in positions
        )
        current_equity = starting_capital + total_realized_pnl + total_unrealized_pnl

        growth_amount = current_equity - starting_capital
        growth_percentage = (growth_amount / starting_capital * 100) if starting_capital > 0 else 0

        # Calculate max equity (peak)
        max_equity = starting_capital
        for position in positions:
            entry_price = float(position.entry_price or 0)
            exit_price = float(position.exit_price or 0)
            current_price = float(position.current_price or 0)
            size = float(position.size or 0)
            side = PositionSide[position.side.upper()]

            # Calculate max possible equity for this position
            if position.status == "closed" and exit_price:
                position_pnl = PNLCalculator.calculate_realized_pnl(
                    entry_price=entry_price,
                    exit_price=exit_price,
                    position_size=size,
                    side=side,
                    fees=float(position.total_fees or 0),
                )
            else:
                position_pnl = PNLCalculator.calculate_unrealized_pnl(
                    entry_price=entry_price,
                    current_price=current_price,
                    position_size=size,
                    side=side,
                )

            max_equity = max(max_equity, starting_capital + position_pnl)

        # Calculate drawdown
        max_drawdown = ((max_equity - current_equity) / max_equity * 100) if max_equity > 0 else 0

        return {
            "status": "success",
            "starting_capital": starting_capital,
            "current_equity": current_equity,
            "growth_amount": growth_amount,
            "growth_percentage": growth_percentage,
            "max_equity": max_equity,
            "max_drawdown": max_drawdown,
            "total_realized_pnl": total_realized_pnl,
            "total_unrealized_pnl": total_unrealized_pnl,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get equity summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve equity summary"
        )


@router.get("/milestones")
async def get_equity_milestones(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get equity milestones (10%, 25%, 50%, 100% growth, etc).

    Returns:
        Milestones achieved and remaining
    """
    try:
        positions = db.query(Position).filter(
            Position.user_id == current_user.id
        ).all()

        starting_capital = float(current_user.starting_capital or 10000)

        total_realized_pnl = sum(
            float(p.realized_pnl or 0) for p in positions
        )
        total_unrealized_pnl = sum(
            float(p.unrealized_pnl or 0) for p in positions
        )
        current_equity = starting_capital + total_realized_pnl + total_unrealized_pnl

        growth_percentage = (
            (current_equity - starting_capital) / starting_capital * 100
        ) if starting_capital > 0 else 0

        # Define milestones
        milestones = [
            {"percentage": 10, "label": "10% Growth", "target": starting_capital * 1.10},
            {"percentage": 25, "label": "25% Growth", "target": starting_capital * 1.25},
            {"percentage": 50, "label": "50% Growth", "target": starting_capital * 1.50},
            {"percentage": 100, "label": "100% Growth (2x)", "target": starting_capital * 2.00},
            {"percentage": 200, "label": "200% Growth (3x)", "target": starting_capital * 3.00},
            {"percentage": 500, "label": "500% Growth (6x)", "target": starting_capital * 6.00},
        ]

        achieved = []
        remaining = []

        for milestone in milestones:
            if current_equity >= milestone["target"]:
                achieved.append({
                    **milestone,
                    "achieved": True,
                    "achieved_at": datetime.utcnow().isoformat(),
                })
            else:
                remaining_amount = milestone["target"] - current_equity
                remaining.append({
                    **milestone,
                    "achieved": False,
                    "remaining_amount": remaining_amount,
                    "progress_percentage": (current_equity / milestone["target"] * 100),
                })

        return {
            "status": "success",
            "current_growth_percentage": growth_percentage,
            "achieved_milestones": achieved,
            "remaining_milestones": remaining,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get equity milestones: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve equity milestones"
        )


def _generate_equity_curve(
    positions: List[Any],
    starting_capital: float,
    days: int = 30,
) -> List[Dict[str, Any]]:
    """Generate equity curve data points.

    Args:
        positions: List of positions
        starting_capital: Starting capital amount
        days: Number of days to generate

    Returns:
        List of equity curve data points
    """
    curve_data = []
    now = datetime.utcnow()

    # Generate daily data points
    for i in range(days + 1):
        date = now - timedelta(days=days - i)
        date_str = date.strftime("%Y-%m-%d")

        # Calculate equity for this date
        daily_pnl = 0

        for position in positions:
            entry_time = position.entry_timestamp
            exit_time = position.exit_timestamp

            # Skip if position hasn't started yet
            if entry_time and entry_time > date:
                continue

            # Calculate PNL for this date
            if position.status == "closed" and exit_time and exit_time <= date:
                # Position closed before or on this date
                daily_pnl += float(position.realized_pnl or 0)
            elif position.status == "open" or (exit_time and exit_time > date):
                # Position open or will close after this date
                entry_price = float(position.entry_price or 0)
                current_price = float(position.current_price or 0)
                size = float(position.size or 0)
                side = PositionSide[position.side.upper()]

                if entry_price > 0:
                    unrealized = PNLCalculator.calculate_unrealized_pnl(
                        entry_price=entry_price,
                        current_price=current_price,
                        position_size=size,
                        side=side,
                    )
                    daily_pnl += unrealized

        equity = starting_capital + daily_pnl

        curve_data.append({
            "date": date_str,
            "timestamp": date.isoformat(),
            "equity": equity,
            "pnl": daily_pnl,
            "growth_percentage": (
                (equity - starting_capital) / starting_capital * 100
            ) if starting_capital > 0 else 0,
        })

    return curve_data
