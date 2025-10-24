"""
Trading API Module - Trading Endpoints for dYdX Bot.

This module provides FastAPI endpoints for trading operations,
integrating with the stateless trading engine.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from ..core.security import get_encryption_manager
from ..db.database import get_database_manager
from ..bot import TradingEngine, DydxClient, TelegramManager
from ..db.models import User

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/trading",
    tags=["trading"],
    responses={404: {"description": "Not found"}},
)


def get_db_session():
    """Dependency to get database session."""
    db_manager = get_database_manager()
    return db_manager.get_session()


def get_trading_engine(db_session: Session = Depends(get_db_session)):
    """Dependency to get trading engine instance."""
    return TradingEngine(db_session)


@router.post("/execute-signal")
async def execute_trading_signal(
    signal_data: Dict[str, Any],
    user_address: str,
    background_tasks: BackgroundTasks,
    trading_engine: TradingEngine = Depends(get_trading_engine)
):
    """Execute a trading signal for a user.

    Args:
        signal_data: Trading signal data (symbol, side, size, price)
        user_address: User's wallet address
        background_tasks: FastAPI background tasks
        trading_engine: Trading engine instance

    Returns:
        Trade execution result
    """
    try:
        # Get user from database
        db_session = trading_engine.db
        user = db_session.exec(
            select(User).where(User.wallet_address == user_address)
        ).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {user_address}"
            )

        # Decrypt user credentials
        encryption_manager = get_encryption_manager()

        try:
            telegram_token = encryption_manager.decrypt(user.encrypted_telegram_token)
            telegram_chat_id = encryption_manager.decrypt(user.encrypted_telegram_chat_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to decrypt user credentials"
            )

        # Execute trade in background
        background_tasks.add_task(
            trading_engine.execute_trade_signal,
            user_address,
            telegram_token,
            telegram_chat_id,
            signal_data
        )

        return {
            "message": "Trade signal received and queued for execution",
            "user_address": user_address,
            "signal": signal_data,
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Trading signal execution error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Trade execution failed: {str(e)}"
        )


@router.post("/tradingview-webhook")
async def tradingview_webhook(
    signal_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    trading_engine: TradingEngine = Depends(get_trading_engine)
):
    """Process TradingView webhook signal.

    Args:
        signal_data: TradingView webhook data
        background_tasks: FastAPI background tasks
        trading_engine: Trading engine instance

    Returns:
        Webhook processing result
    """
    try:
        # Extract TradingView signal format
        symbol = signal_data.get('symbol')
        side = signal_data.get('side')
        price = signal_data.get('price')
        size = signal_data.get('size')

        if not symbol or not side:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Symbol and side are required"
            )

        # Process signal
        signal_result = await trading_engine.process_tradingview_signal(
            symbol=symbol,
            side=side,
            price=price,
            size=size,
            **signal_data
        )

        if not signal_result['valid']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=signal_result['error']
            )

        # For TradingView webhooks, we would need to identify the user
        # This is a simplified version - in practice, you'd use webhook secrets
        # to identify the user from the database

        return {
            "message": "TradingView signal processed",
            "signal": signal_result['signal'],
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TradingView webhook error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Webhook processing failed: {str(e)}"
        )


@router.get("/positions/{user_address}")
async def get_user_positions(
    user_address: str,
    status: Optional[str] = None,
    trading_engine: TradingEngine = Depends(get_trading_engine)
):
    """Get user's trading positions.

    Args:
        user_address: User's wallet address
        status: Optional position status filter
        trading_engine: Trading engine instance

    Returns:
        List of user positions
    """
    try:
        # Get positions from database
        positions = await trading_engine.position_manager.get_user_positions(
            user_address, status
        )

        # Convert to response format
        position_data = []
        for position in positions:
            position_data.append({
                "id": position.id,
                "symbol": position.symbol,
                "status": position.status,
                "side": "BUY",  # Would need to be stored in position
                "entry_price": float(position.entry_price),
                "size": float(position.size),
                "dydx_order_id": position.dydx_order_id,
                "tp_order_id": position.tp_order_id,
                "sl_order_id": position.sl_order_id,
                "opened_at": position.opened_at.isoformat(),
                "notional_value": float(position.notional_value),
            })

        return {
            "user_address": user_address,
            "positions": position_data,
            "count": len(position_data),
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Get positions error for {user_address}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get positions: {str(e)}"
        )


@router.get("/positions/{user_address}/summary")
async def get_positions_summary(
    user_address: str,
    trading_engine: TradingEngine = Depends(get_trading_engine)
):
    """Get summary of user's positions.

    Args:
        user_address: User's wallet address
        trading_engine: Trading engine instance

    Returns:
        Position summary statistics
    """
    try:
        # Get summary from state synchronizer
        summary = await StateSynchronizer.get_positions_summary(
            trading_engine.db, user_address
        )

        return {
            "user_address": user_address,
            "summary": summary,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Get positions summary error for {user_address}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get summary: {str(e)}"
        )


@router.post("/test-telegram")
async def test_telegram_connection(
    user_address: str,
    trading_engine: TradingEngine = Depends(get_trading_engine)
):
    """Test Telegram connection for a user.

    Args:
        user_address: User's wallet address
        trading_engine: Trading engine instance

    Returns:
        Telegram connection test result
    """
    try:
        # Get user from database
        user = trading_engine.db.exec(
            select(User).where(User.wallet_address == user_address)
        ).first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User not found: {user_address}"
            )

        # Decrypt Telegram credentials
        encryption_manager = get_encryption_manager()

        try:
            telegram_token = encryption_manager.decrypt(user.encrypted_telegram_token)
            telegram_chat_id = encryption_manager.decrypt(user.encrypted_telegram_chat_id)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to decrypt Telegram credentials"
            )

        # Test connection
        test_result = await TelegramManager.test_connection(
            telegram_token, telegram_chat_id
        )

        return {
            "user_address": user_address,
            "test_result": test_result,
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Telegram test error for {user_address}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Telegram test failed: {str(e)}"
        )


@router.get("/market/{symbol}")
async def get_market_data(symbol: str):
    """Get market data for a symbol.

    Args:
        symbol: Trading pair symbol

    Returns:
        Market data including price and volume
    """
    try:
        # Create a temporary client for market data (no credentials needed)
        # Note: In practice, you'd want to cache this or use a market data client
        market_data = {
            "symbol": symbol,
            "price": 50000.0,  # Placeholder
            "volume_24h": 1000000.0,  # Placeholder
            "price_change_24h": 2.5,  # Placeholder
            "timestamp": datetime.utcnow().isoformat()
        }

        return market_data

    except Exception as e:
        logger.error(f"Market data error for {symbol}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get market data: {str(e)}"
        )


@router.post("/risk-check")
async def check_risk_limits(
    user_address: str,
    signal_data: Dict[str, Any],
    trading_engine: TradingEngine = Depends(get_trading_engine)
):
    """Check if a trade signal passes risk management rules.

    Args:
        user_address: User's wallet address
        signal_data: Trading signal data
        trading_engine: Trading engine instance

    Returns:
        Risk check result
    """
    try:
        # Parse signal
        signal = await trading_engine._parse_trading_signal(signal_data)
        if not signal['valid']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=signal['error']
            )

        # Check risk limits
        risk_check = await trading_engine._check_risk_limits(user_address, signal)

        return {
            "user_address": user_address,
            "signal": signal,
            "risk_check": risk_check,
            "timestamp": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Risk check error for {user_address}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Risk check failed: {str(e)}"
        )