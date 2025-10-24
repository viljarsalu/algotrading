"""
Trading Engine Module - Main Trading Coordination Engine.

This module provides the main trading engine that coordinates all
trading components for per-user trading operations.
"""

import asyncio
import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional, Tuple
from sqlmodel import Session

from .dydx_client import DydxClient
from .telegram_manager import TelegramManager
from .risk_manager import RiskManager, RiskParameters
from .state_manager import PositionManager, StateSynchronizer
from ..db.models import User, Position

logger = logging.getLogger(__name__)


class TradingEngine:
    """Main trading coordination engine for per-user operations."""

    def __init__(self, db_session: Session):
        """Initialize trading engine with database session.

        Args:
            db_session: SQLModel database session
        """
        self.db = db_session
        self.position_manager = PositionManager(db_session)
        self.risk_params = RiskParameters()

    async def execute_trade_signal(
        self,
        user_address: str,
        telegram_token: str,
        telegram_chat_id: str,
        signal_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute complete trade from signal to notification.

        Args:
            user_address: User's wallet address
            telegram_token: Telegram bot token
            telegram_chat_id: Telegram chat ID
            signal_data: Trading signal data

        Returns:
            Trade execution result
        """
        try:
            logger.info(f"Executing trade signal for user {user_address}")

            # Step 1: Validate user and credentials
            user = await self._validate_user_credentials(
                user_address, telegram_token, telegram_chat_id
            )

            if not user:
                return {
                    'success': False,
                    'error': 'Invalid user or credentials',
                    'user_address': user_address,
                }

            # Step 2: Parse and validate signal
            signal = await self._parse_trading_signal(signal_data)
            if not signal['valid']:
                return {
                    'success': False,
                    'error': f'Invalid signal: {signal["error"]}',
                    'user_address': user_address,
                }

            # Step 3: Check risk management
            risk_check = await self._check_risk_limits(user_address, signal)
            if not risk_check['allowed']:
                # Send risk warning notification
                await self._send_risk_notification(
                    telegram_token, telegram_chat_id, risk_check['reason']
                )
                return {
                    'success': False,
                    'error': f'Risk check failed: {risk_check["reason"]}',
                    'user_address': user_address,
                }

            # Step 4: Create dYdX client
            dydx_client = await DydxClient.create_client()

            # Step 5: Execute the trade
            trade_result = await self._execute_trade(
                dydx_client, user_address, signal
            )

            if not trade_result['success']:
                # Send error notification
                await self._send_error_notification(
                    telegram_token, telegram_chat_id,
                    'Trade execution failed', trade_result['error']
                )
                return trade_result

            # Step 6: Create position record
            position = await self._create_position_record(
                user_address, signal, trade_result
            )

            # Step 7: Send success notification
            await self._send_trade_notification(
                telegram_token, telegram_chat_id,
                signal, trade_result, 'success'
            )

            logger.info(f"Trade executed successfully for user {user_address}")

            return {
                'success': True,
                'position_id': position.id,
                'order_id': trade_result['order_id'],
                'symbol': signal['symbol'],
                'side': signal['side'],
                'size': signal['size'],
                'price': trade_result.get('price'),
                'user_address': user_address,
            }

        except Exception as e:
            logger.error(f"Trade execution failed for user {user_address}: {e}")

            # Send error notification
            try:
                await self._send_error_notification(
                    telegram_token, telegram_chat_id,
                    'Trade execution error', str(e)
                )
            except Exception as notification_error:
                logger.error(f"Failed to send error notification: {notification_error}")

            return {
                'success': False,
                'error': str(e),
                'user_address': user_address,
            }

    async def process_tradingview_signal(
        self,
        symbol: str,
        side: str,
        price: Optional[float],
        size: Optional[float],
        **kwargs
    ) -> Dict[str, Any]:
        """Process TradingView webhook signal.

        Args:
            symbol: Trading pair symbol
            side: Trade side ('buy' or 'sell')
            price: Optional limit price
            size: Optional position size
            **kwargs: Additional signal parameters

        Returns:
            Signal processing result
        """
        try:
            # Parse TradingView signal format
            signal = {
                'symbol': symbol,
                'side': side.upper(),
                'price': price,
                'size': size,
                'order_type': 'LIMIT' if price else 'MARKET',
                'timeframe': kwargs.get('timeframe'),
                'strategy': kwargs.get('strategy'),
                'timestamp': datetime.utcnow(),
            }

            # Validate signal
            if not signal['symbol'] or signal['side'] not in ['BUY', 'SELL']:
                return {
                    'valid': False,
                    'error': 'Invalid symbol or side',
                }

            return {
                'valid': True,
                'signal': signal,
            }

        except Exception as e:
            logger.error(f"TradingView signal processing error: {e}")
            return {
                'valid': False,
                'error': str(e),
            }

    async def manage_position_lifecycle(
        self,
        position_id: int,
        dydx_client: DydxClient
    ) -> Dict[str, Any]:
        """Monitor and manage single position lifecycle.

        Args:
            position_id: Position ID to manage
            dydx_client: Authenticated dYdX client

        Returns:
            Position management result
        """
        try:
            # Get position from database
            position = await self.position_manager.get_position(position_id)
            if not position:
                return {
                    'success': False,
                    'error': f'Position {position_id} not found',
                }

            # Sync with dYdX
            synced_position = await StateSynchronizer.sync_position_with_dydx(
                position, dydx_client
            )

            # Check if position should be closed
            should_close, close_reason = await self._check_position_close_conditions(
                synced_position, dydx_client
            )

            if should_close:
                # Close the position
                close_result = await self._close_position_with_orders(
                    synced_position, dydx_client, close_reason
                )

                if close_result['success']:
                    # Update position in database
                    await self.position_manager.close_position(
                        position_id=position_id,
                        closing_price=close_result['closing_price'],
                        pnl=close_result['pnl']
                    )

                    return {
                        'success': True,
                        'action': 'closed',
                        'reason': close_reason,
                        'closing_price': close_result['closing_price'],
                        'pnl': close_result['pnl'],
                    }

            return {
                'success': True,
                'action': 'monitored',
                'status': synced_position.status,
            }

        except Exception as e:
            logger.error(f"Position lifecycle management failed for {position_id}: {e}")
            return {
                'success': False,
                'error': str(e),
            }

    async def _validate_user_credentials(
        self,
        user_address: str,
        dydx_mnemonic: str,
        telegram_token: str,
        telegram_chat_id: str
    ) -> Optional[User]:
        """Validate user credentials and permissions."""
        try:
            # Get user from database
            user = self.db.exec(
                select(User).where(User.wallet_address == user_address)
            ).first()

            if not user:
                logger.error(f"User not found: {user_address}")
                return None

            # Validate mnemonic format (basic check)
            if not dydx_mnemonic or len(dydx_mnemonic.split()) < 12:
                logger.error(f"Invalid dYdX mnemonic for user {user_address}")
                return None

            # Validate Telegram credentials
            if not telegram_token or not telegram_chat_id:
                logger.error(f"Invalid Telegram credentials for user {user_address}")
                return None

            return user

        except Exception as e:
            logger.error(f"User validation error for {user_address}: {e}")
            return None

    async def _parse_trading_signal(self, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and validate trading signal data."""
        try:
            # Extract required fields
            symbol = signal_data.get('symbol')
            side = signal_data.get('side', '').upper()
            size = signal_data.get('size')
            price = signal_data.get('price')

            # Validate required fields
            if not symbol:
                return {
                    'valid': False,
                    'error': 'Symbol is required',
                }

            if side not in ['BUY', 'SELL']:
                return {
                    'valid': False,
                    'error': f'Invalid side: {side}',
                }

            if not size or float(size) <= 0:
                return {
                    'valid': False,
                    'error': 'Valid size is required',
                }

            # Determine order type
            order_type = 'LIMIT' if price else 'MARKET'

            return {
                'valid': True,
                'symbol': symbol,
                'side': side,
                'size': float(size),
                'price': float(price) if price else None,
                'order_type': order_type,
            }

        except Exception as e:
            return {
                'valid': False,
                'error': f'Signal parsing error: {str(e)}',
            }

    async def _check_risk_limits(
        self,
        user_address: str,
        signal: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check if trade complies with risk management rules."""
        try:
            # Get current positions
            current_positions = await self.position_manager.get_user_positions(
                user_address, status='open'
            )

            # Check position limits
            limits_ok, limits_reason = RiskManager.check_position_limits(
                current_positions=[
                    {
                        'notional_value': float(p.entry_price * p.size),
                        'symbol': p.symbol,
                    }
                    for p in current_positions
                ],
                new_position_size=float(signal['size']),
                max_positions=self.risk_params.max_positions
            )

            if not limits_ok:
                return {
                    'allowed': False,
                    'reason': limits_reason,
                }

            # Validate order parameters
            valid, error = RiskManager.validate_order_parameters(
                symbol=signal['symbol'],
                side=signal['side'],
                size=signal['size'],
                price=signal['price']
            )

            if not valid:
                return {
                    'allowed': False,
                    'reason': error,
                }

            return {
                'allowed': True,
                'reason': 'Risk checks passed',
            }

        except Exception as e:
            logger.error(f"Risk check error for {user_address}: {e}")
            return {
                'allowed': False,
                'reason': f'Risk check error: {str(e)}',
            }

    async def _execute_trade(
        self,
        dydx_client: DydxClient,
        user_address: str,
        signal: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the actual trade on dYdX."""
        try:
            if signal['order_type'] == 'MARKET':
                # Place market order
                result = await DydxClient.place_market_order(
                    client=dydx_client,
                    symbol=signal['symbol'],
                    side=signal['side'],
                    size=str(signal['size'])
                )
            else:
                # Place limit order
                result = await DydxClient.place_limit_order(
                    client=dydx_client,
                    symbol=signal['symbol'],
                    side=signal['side'],
                    size=str(signal['size']),
                    price=str(signal['price'])
                )

            if result['success']:
                return {
                    'success': True,
                    'order_id': result['order_id'],
                    'price': result.get('price'),
                }
            else:
                return {
                    'success': False,
                    'error': result['error'],
                }

        except Exception as e:
            logger.error(f"Trade execution error for {user_address}: {e}")
            return {
                'success': False,
                'error': str(e),
            }

    async def _create_position_record(
        self,
        user_address: str,
        signal: Dict[str, Any],
        trade_result: Dict[str, Any]
    ) -> Position:
        """Create position record in database."""
        # Create position
        position = await self.position_manager.create_position(
            user_address=user_address,
            symbol=signal['symbol'],
            side=signal['side'],
            entry_price=signal['price'] if signal['order_type'] == 'LIMIT' else 0,  # Market orders get filled price later
            size=signal['size'],
            dydx_order_id=trade_result['order_id']
        )

        return position

    async def _send_trade_notification(
        self,
        telegram_token: str,
        telegram_chat_id: str,
        signal: Dict[str, Any],
        trade_result: Dict[str, Any],
        status: str
    ):
        """Send trade notification via Telegram."""
        try:
            # Format notification message
            message = await TelegramManager.format_trade_notification(
                symbol=signal['symbol'],
                side=signal['side'],
                size=str(signal['size']),
                price=str(signal.get('price', 'MARKET')),
                order_type=signal['order_type'],
                status=status
            )

            # Send notification
            await TelegramManager.send_notification(
                token=telegram_token,
                chat_id=telegram_chat_id,
                message=message
            )

        except Exception as e:
            logger.error(f"Failed to send trade notification: {e}")

    async def _send_risk_notification(
        self,
        telegram_token: str,
        telegram_chat_id: str,
        reason: str
    ):
        """Send risk warning notification."""
        try:
            message = await TelegramManager.format_risk_warning_notification(
                warning_type='POSITION_LIMIT',
                symbol='N/A',
                current_value=0,
                limit_value=0,
                details={'reason': reason}
            )

            await TelegramManager.send_notification(
                token=telegram_token,
                chat_id=telegram_chat_id,
                message=message
            )

        except Exception as e:
            logger.error(f"Failed to send risk notification: {e}")

    async def _send_error_notification(
        self,
        telegram_token: str,
        telegram_chat_id: str,
        operation: str,
        error: str
    ):
        """Send error notification."""
        try:
            message = await TelegramManager.format_error_notification(
                operation=operation,
                error=error
            )

            await TelegramManager.send_notification(
                token=telegram_token,
                chat_id=telegram_chat_id,
                message=message
            )

        except Exception as e:
            logger.error(f"Failed to send error notification: {e}")

    async def _check_position_close_conditions(
        self,
        position: Position,
        dydx_client: DydxClient
    ) -> Tuple[bool, str]:
        """Check if position should be closed."""
        try:
            # Get current market price
            market_price_result = await DydxClient.get_market_price(
                dydx_client, position.symbol
            )

            if not market_price_result['success']:
                return False, 'Cannot get market price'

            current_price = float(market_price_result['price'])

            # Simple close conditions (can be made more sophisticated)
            # Close if price moved significantly against position
            price_change = abs(current_price - float(position.entry_price)) / float(position.entry_price)

            if price_change > 0.05:  # 5% move
                return True, f'Price moved {price_change:.1%} against position'

            return False, 'No close conditions met'

        except Exception as e:
            logger.error(f"Close condition check error for position {position.id}: {e}")
            return False, f'Check error: {str(e)}'

    async def _close_position_with_orders(
        self,
        position: Position,
        dydx_client: DydxClient,
        reason: str
    ) -> Dict[str, Any]:
        """Close position by cancelling orders and updating state."""
        try:
            # Cancel any open orders for this position
            if position.dydx_order_id:
                await DydxClient.cancel_order(dydx_client, position.dydx_order_id)

            if position.tp_order_id:
                await DydxClient.cancel_order(dydx_client, position.tp_order_id)

            if position.sl_order_id:
                await DydxClient.cancel_order(dydx_client, position.sl_order_id)

            # Get final price for P&L calculation
            market_price_result = await DydxClient.get_market_price(
                dydx_client, position.symbol
            )

            closing_price = float(market_price_result['price']) if market_price_result['success'] else float(position.entry_price)

            # Calculate P&L (simplified)
            pnl = (closing_price - float(position.entry_price)) * float(position.size)

            return {
                'success': True,
                'closing_price': closing_price,
                'pnl': pnl,
            }

        except Exception as e:
            logger.error(f"Position close error for {position.id}: {e}")
            return {
                'success': False,
                'error': str(e),
            }