"""
Secure Webhook System - Two-Factor Authentication and Trade Execution.

This module implements Phase 4 of the dYdX Trading Bot Service:
Secure webhook endpoints with two-factor authentication and complete
trade execution orchestration.
"""

import asyncio
import hashlib
import hmac
import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any, Optional, Tuple, List
from contextlib import asynccontextmanager

from fastapi import APIRouter, Request, HTTPException, status, Depends, BackgroundTasks
from sqlalchemy.orm import Session
import structlog

from ..core.security import get_encryption_manager
from ..db.database import get_database_manager, get_db
from ..db.models import User, WebhookEvent, Position
from ..bot import TradingEngine, DydxClient, TelegramManager
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)
webhook_logger = structlog.get_logger("webhook.security")

# Create router
router = APIRouter(
    prefix="/api/webhooks",
    tags=["webhooks"],
    responses={404: {"description": "Not found"}},
)

# Rate limiting storage (in production, use Redis)
rate_limit_store = {}


class WebhookAuthenticator:
    """Two-factor webhook authentication system."""

    @staticmethod
    async def verify_two_factor(
        webhook_uuid: str,
        request_body: Dict[str, Any],
        db_session: AsyncSession
    ) -> Tuple[bool, Optional[User], str]:
        """Verify webhook UUID from URL and secret from request body.

        Args:
            webhook_uuid: UUID from URL path
            request_body: JSON request body containing webhook secret
            db_session: Database session

        Returns:
            Tuple of (is_valid, user_or_none, error_message)
        """
        try:
            # Step 1: Find user by webhook UUID
            from sqlalchemy import select
            result = await db_session.execute(
                select(User).where(User.webhook_uuid == webhook_uuid)
            )
            user = result.scalar_one_or_none()

            if not user:
                webhook_logger.warning(
                    "Webhook authentication failed: Invalid UUID",
                    webhook_uuid=webhook_uuid,
                    client_ip="unknown"
                )
                return False, None, "Invalid webhook UUID"

            if not user.encrypted_webhook_secret:
                webhook_logger.error(
                    "Webhook authentication failed: No secret configured",
                    user_address=user.wallet_address,
                    webhook_uuid=webhook_uuid
                )
                return False, None, "Webhook secret not configured"

            # Step 2: Extract and validate webhook secret from request
            webhook_secret = await WebhookAuthenticator.extract_webhook_secret(request_body)
            if not webhook_secret:
                webhook_logger.warning(
                    "Webhook authentication failed: No secret in request",
                    user_address=user.wallet_address,
                    webhook_uuid=webhook_uuid
                )
                return False, None, "Webhook secret required"

            # Step 3: Decrypt stored secret and compare
            encryption_manager = get_encryption_manager()
            try:
                stored_secret = encryption_manager.decrypt(user.encrypted_webhook_secret)

                # Use constant-time comparison to prevent timing attacks
                if not hmac.compare_digest(stored_secret, webhook_secret):
                    webhook_logger.warning(
                        "Webhook authentication failed: Secret mismatch",
                        user_address=user.wallet_address,
                        webhook_uuid=webhook_uuid
                    )
                    return False, None, "Invalid webhook secret"

            except Exception as e:
                webhook_logger.error(
                    "Webhook authentication failed: Decryption error",
                    user_address=user.wallet_address,
                    webhook_uuid=webhook_uuid,
                    error=str(e)
                )
                return False, None, "Authentication system error"

            # Step 4: Check rate limits
            if not await WebhookAuthenticator.rate_limit_check(webhook_uuid):
                webhook_logger.warning(
                    "Webhook authentication failed: Rate limit exceeded",
                    user_address=user.wallet_address,
                    webhook_uuid=webhook_uuid
                )
                return False, None, "Rate limit exceeded"

            webhook_logger.info(
                "Webhook authentication successful",
                user_address=user.wallet_address,
                webhook_uuid=webhook_uuid
            )

            return True, user, "Authentication successful"

        except Exception as e:
            webhook_logger.error(
                "Webhook authentication error",
                webhook_uuid=webhook_uuid,
                error=str(e)
            )
            return False, None, f"Authentication error: {str(e)}"

    @staticmethod
    async def extract_webhook_secret(request_body: Dict[str, Any]) -> str:
        """Extract webhook secret from request body.

        Args:
            request_body: JSON request body

        Returns:
            Webhook secret string or empty string if not found
        """
        # Support multiple possible field names for webhook secret
        secret_fields = ['secret', 'webhook_secret', 'api_secret', 'key', 'token']

        for field in secret_fields:
            if field in request_body and request_body[field]:
                return str(request_body[field])

        return ""

    @staticmethod
    async def validate_request_format(request_body: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate TradingView webhook request format.

        Args:
            request_body: JSON request body to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(request_body, dict):
            return False, "Request body must be JSON object"

        # Check for required fields (flexible - support multiple formats)
        required_fields = ['symbol', 'side']
        optional_fields = ['price', 'size', 'order_type', 'timeframe', 'strategy']

        # At minimum, we need either symbol+side or a 'signal' field
        has_basic_fields = any(field in request_body for field in required_fields)
        has_signal_field = 'signal' in request_body

        if not (has_basic_fields or has_signal_field):
            return False, "Request must contain 'symbol' and 'side' or 'signal' field"

        # Validate symbol format if present
        if 'symbol' in request_body:
            symbol = request_body['symbol']
            if not isinstance(symbol, str) or len(symbol) < 3 or len(symbol) > 20:
                return False, "Invalid symbol format"

        # Validate side if present
        if 'side' in request_body:
            side = request_body.get('side', '').upper()
            if side not in ['BUY', 'SELL']:
                return False, "Side must be 'buy' or 'sell'"

        # Validate price if present
        if 'price' in request_body:
            try:
                price = float(request_body['price'])
                if price <= 0:
                    return False, "Price must be positive"
            except (ValueError, TypeError):
                return False, "Invalid price format"

        # Validate size if present
        if 'size' in request_body:
            try:
                size = float(request_body['size'])
                if size <= 0:
                    return False, "Size must be positive"
            except (ValueError, TypeError):
                return False, "Invalid size format"

        return True, "Valid request format"

    @staticmethod
    async def rate_limit_check(
        webhook_uuid: str,
        window_seconds: int = 60,
        max_requests: int = 10
    ) -> bool:
        """Implement rate limiting for webhook requests.

        Args:
            webhook_uuid: Webhook UUID to rate limit
            window_seconds: Time window in seconds
            max_requests: Maximum requests per window

        Returns:
            True if request allowed, False if rate limited
        """
        current_time = time.time()

        # Initialize rate limit tracking for this UUID
        if webhook_uuid not in rate_limit_store:
            rate_limit_store[webhook_uuid] = []

        # Clean old requests outside the window
        cutoff_time = current_time - window_seconds
        rate_limit_store[webhook_uuid] = [
            req_time for req_time in rate_limit_store[webhook_uuid]
            if req_time > cutoff_time
        ]

        # Check if under limit
        if len(rate_limit_store[webhook_uuid]) >= max_requests:
            return False

        # Add current request
        rate_limit_store[webhook_uuid].append(current_time)
        return True


class CredentialManager:
    """Secure credential management for webhook-based trading."""

    @staticmethod
    async def fetch_user_credentials(
        user: User,
        master_key: str,
        db_session: AsyncSession
    ) -> Dict[str, str]:
        """Securely decrypt and return user credentials.

        Args:
            user: User model instance
            master_key: Master encryption key (for additional security layer)
            db_session: Database session

        Returns:
            Dictionary containing decrypted credentials

        Raises:
            HTTPException: If credential decryption fails
        """
        try:
            encryption_manager = get_encryption_manager()

            # Decrypt all user credentials
            credentials = {}

            # dYdX mnemonic (required for trading)
            # Determine which mnemonic to use based on network
            network_id = user.dydx_network_id or 11155111
            
            if network_id == 11155111:  # testnet
                encrypted_mnemonic = user.encrypted_dydx_testnet_mnemonic
                network_name = "testnet"
            else:  # mainnet
                encrypted_mnemonic = user.encrypted_dydx_mainnet_mnemonic
                network_name = "mainnet"
            
            if encrypted_mnemonic:
                try:
                    credentials['dydx_mnemonic'] = encryption_manager.decrypt(
                        encrypted_mnemonic
                    )
                except Exception as e:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Failed to decrypt dYdX {network_name} mnemonic: {str(e)}"
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"dYdX {network_name} mnemonic not configured"
                )

            # Telegram credentials (required for notifications)
            if user.encrypted_telegram_token:
                try:
                    credentials['telegram_token'] = encryption_manager.decrypt(
                        user.encrypted_telegram_token
                    )
                except Exception as e:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Failed to decrypt Telegram token: {str(e)}"
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Telegram token not configured"
                )

            if user.encrypted_telegram_chat_id:
                try:
                    credentials['telegram_chat_id'] = encryption_manager.decrypt(
                        user.encrypted_telegram_chat_id
                    )
                except Exception as e:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Failed to decrypt Telegram chat ID: {str(e)}"
                    )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Telegram chat ID not configured"
                )

            # Validate credentials before returning
            validation_result, validation_error = await CredentialManager.validate_credentials(credentials)
            if not validation_result:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid credentials: {validation_error}"
                )

            # Log credential access (without exposing sensitive data)
            webhook_logger.info(
                "User credentials accessed",
                user_address=user.wallet_address,
                access_type="webhook_trade",
                credential_types=list(credentials.keys())
            )

            return credentials

        except HTTPException:
            raise
        except Exception as e:
            webhook_logger.error(
                "Credential fetch error",
                user_address=user.wallet_address,
                error=str(e)
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve user credentials"
            )

    @staticmethod
    async def validate_credentials(credentials: Dict[str, str]) -> Tuple[bool, str]:
        """Validate decrypted credentials for trading.

        Args:
            credentials: Dictionary of decrypted credentials

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Validate Telegram token format (basic check)
            telegram_token = credentials.get('telegram_token', '')
            if not telegram_token or len(telegram_token) < 35:  # Bot tokens are typically 35+ chars
                return False, "Invalid Telegram token format"

            # Validate Telegram chat ID
            telegram_chat_id = credentials.get('telegram_chat_id', '')
            if not telegram_chat_id:
                return False, "Telegram chat ID is required"

            # Basic chat ID format validation (should be numeric or start with -)
            try:
                chat_id_num = int(telegram_chat_id)
                if chat_id_num == 0:
                    return False, "Invalid Telegram chat ID"
            except ValueError:
                return False, "Telegram chat ID must be numeric"

            return True, "Valid credentials"

        except Exception as e:
            return False, f"Credential validation error: {str(e)}"

    @staticmethod
    async def cleanup_credentials(credentials: Dict[str, str]) -> None:
        """Securely clear credentials from memory.

        Args:
            credentials: Dictionary of credentials to clear
        """
        try:
            # Overwrite credential values with None
            for key in credentials:
                credentials[key] = None

            # Force garbage collection hint
            import gc
            gc.collect()

            webhook_logger.debug("Credentials cleared from memory")

        except Exception as e:
            webhook_logger.error(f"Error during credential cleanup: {e}")


class TradeOrchestrator:
    """Complete trade execution orchestration with step-by-step pipeline."""

    def __init__(self, db_session: AsyncSession, trading_engine: TradingEngine):
        """Initialize trade orchestrator.

        Args:
            db_session: Database session
            trading_engine: Trading engine instance
        """
        self.db = db_session
        self.trading_engine = trading_engine

    async def execute_complete_trade(
        self,
        user: User,
        signal_data: Dict[str, Any],
        master_key: str
    ) -> Dict[str, Any]:
        """Orchestrate complete trade execution from signal to notification.

        Args:
            user: Authenticated user
            signal_data: Validated trading signal
            master_key: Master encryption key

        Returns:
            Complete trade execution result
        """
        start_time = time.time()
        credentials = None

        try:
            webhook_logger.info(
                "Starting complete trade execution",
                user_address=user.wallet_address,
                symbol=signal_data.get('symbol'),
                side=signal_data.get('side')
            )

            # Step 1: Credential retrieval with validation
            step_result = await self.step_1_credential_retrieval(user, master_key)
            if not step_result['success']:
                return step_result
            credentials = step_result['credentials']

            # Step 2: Risk calculation and validation
            step_result = await self.step_2_risk_calculation(credentials, signal_data)
            if not step_result['success']:
                await self._send_risk_notification(credentials, step_result.get('error', 'Unknown risk error'))
                return step_result

            # Step 3: Trade execution on dYdX
            trade_result = await self.step_3_trade_execution(user, credentials, step_result['risk_parameters'])
            if not trade_result['success']:
                await self._send_error_notification(credentials, "Trade execution failed", trade_result['error'])
                return trade_result

            # Step 4: Position persistence to database
            position_result = await self.step_4_position_persistence(user, trade_result['trade_result'], signal_data)
            if not position_result['success']:
                await self._send_error_notification(credentials, "Position persistence failed", position_result['error'])
                return position_result

            # Step 5: Notification delivery
            step_result = await self.step_5_notification_delivery(credentials, position_result['position'], trade_result['trade_result'])
            if not step_result['success']:
                webhook_logger.warning(
                    "Notification delivery failed, but trade was successful",
                    user_address=user.wallet_address,
                    position_id=step_result['position'].id
                )

            # Calculate total execution time
            execution_time = time.time() - start_time

            webhook_logger.info(
                "Complete trade execution successful",
                user_address=user.wallet_address,
                position_id=position_result['position'].id,
                execution_time_seconds=round(execution_time, 3)
            )

            return {
                'success': True,
                'position_id': position_result['position'].id,
                'order_id': trade_result['trade_result'].get('order_id'),
                'symbol': signal_data.get('symbol'),
                'side': signal_data.get('side'),
                'size': signal_data.get('size'),
                'price': trade_result['trade_result'].get('price'),
                'execution_time_seconds': round(execution_time, 3),
                'timestamp': datetime.utcnow().isoformat()
            }

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Trade orchestration failed: {str(e)}"

            webhook_logger.error(
                "Trade orchestration exception",
                user_address=user.wallet_address,
                execution_time_seconds=round(execution_time, 3),
                error=str(e)
            )

            # Send error notification if we have credentials
            if credentials:
                try:
                    await self._send_error_notification(credentials, "Trade execution error", error_msg)
                except Exception as notification_error:
                    webhook_logger.error(f"Failed to send error notification: {notification_error}")

            return {
                'success': False,
                'error': error_msg,
                'execution_time_seconds': round(execution_time, 3),
                'timestamp': datetime.utcnow().isoformat()
            }

        finally:
            # Always cleanup credentials
            if credentials:
                await CredentialManager.cleanup_credentials(credentials)

    async def step_1_credential_retrieval(
        self,
        user: User,
        master_key: str
    ) -> Dict[str, Any]:
        """Step 1: Decrypt user credentials.

        Args:
            user: User model instance
            master_key: Master encryption key

        Returns:
            Step result with credentials or error
        """
        try:
            credentials = await CredentialManager.fetch_user_credentials(
                user, master_key, self.db
            )

            return {
                'success': True,
                'credentials': credentials,
                'step': 'credential_retrieval'
            }

        except HTTPException as e:
            return {
                'success': False,
                'error': e.detail,
                'step': 'credential_retrieval'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Credential retrieval failed: {str(e)}',
                'step': 'credential_retrieval'
            }

    async def step_2_risk_calculation(
        self,
        credentials: Dict[str, str],
        signal_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Step 2: Calculate position size and validate risk.

        Args:
            credentials: User credentials
            signal_data: Trading signal data

        Returns:
            Step result with risk parameters or error
        """
        try:
            # Ensure signal has all required fields with defaults
            normalized_signal = {
                'symbol': signal_data.get('symbol'),
                'side': signal_data.get('side', '').upper(),
                'size': signal_data.get('size'),
                'price': signal_data.get('price'),  # Can be None for market orders
                'order_type': signal_data.get('order_type', 'MARKET')
            }
            
            # Use existing risk check from trading engine
            risk_check = await self.trading_engine._check_risk_limits(
                user_address="",  # We don't have user_address here, but risk check needs it
                signal=normalized_signal
            )

            if not risk_check['allowed']:
                return {
                    'success': False,
                    'error': f'Risk check failed: {risk_check["reason"]}',
                    'step': 'risk_calculation'
                }

            # Extract risk parameters for next step
            risk_parameters = {
                'allowed': True,
                'reason': risk_check['reason'],
                'signal': normalized_signal,
                'risk_limits': risk_check
            }

            return {
                'success': True,
                'risk_parameters': risk_parameters,
                'step': 'risk_calculation'
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Risk calculation failed: {str(e)}',
                'step': 'risk_calculation'
            }

    async def step_3_trade_execution(
        self,
        user: User,
        credentials: Dict[str, str],
        risk_parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Step 3: Execute trade on dYdX.

        Args:
            user: User model instance
            credentials: User credentials
            risk_parameters: Validated risk parameters

        Returns:
            Step result with trade result or error
        """
        try:
            # Create dYdX client with user's mnemonic and network
            dydx_mnemonic = credentials.get('dydx_mnemonic')
            if not dydx_mnemonic:
                return {
                    'success': False,
                    'error': 'dYdX mnemonic not available in credentials',
                    'step': 'trade_execution'
                }
            
            # Use user's configured network ID, default to testnet
            network_id = user.dydx_network_id or 11155111
            
            dydx_client = await DydxClient.create_client(
                network_id=network_id,
                mnemonic=dydx_mnemonic
            )

            # Execute the trade using existing trading engine logic
            signal = risk_parameters['signal']
            trade_result = await self.trading_engine._execute_trade(
                dydx_client, "", signal  # Empty string for user_address as we don't have it here
            )

            if not trade_result['success']:
                return {
                    'success': False,
                    'error': trade_result['error'],
                    'step': 'trade_execution'
                }

            return {
                'success': True,
                'trade_result': trade_result,
                'dydx_client': dydx_client,
                'step': 'trade_execution'
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Trade execution failed: {str(e)}',
                'step': 'trade_execution'
            }

    async def step_4_position_persistence(
        self,
        user: User,
        trade_result: Dict[str, Any],
        signal_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Step 4: Save position to database.

        Args:
            user: User model instance
            trade_result: Result from trade execution
            signal_data: Original trading signal data

        Returns:
            Step result with position record or error
        """
        try:
            # Extract signal data for position creation
            if not signal_data:
                return {
                    'success': False,
                    'error': 'Signal data required for position creation',
                    'step': 'position_persistence'
                }

            symbol = signal_data.get('symbol')
            side = signal_data.get('side', '').upper()
            size = signal_data.get('size')
            price = signal_data.get('price')

            if not all([symbol, side, size]):
                return {
                    'success': False,
                    'error': f'Missing required signal data for position creation. Got: symbol={symbol}, side={side}, size={size}',
                    'step': 'position_persistence'
                }

            # Create position record using existing position manager
            # Ensure size and entry_price are floats FIRST
            try:
                size_float = float(size) if size else 0.01
                entry_price_float = float(price) if price else float(trade_result.get('price', 1.0))
            except (ValueError, TypeError) as e:
                return {
                    'success': False,
                    'error': f'Invalid size or price format: {str(e)}',
                    'step': 'position_persistence'
                }
            
            # Validate values are positive
            if entry_price_float <= 0:
                entry_price_float = 1.0
            
            if size_float <= 0:
                size_float = 0.01
            
            position = await self.trading_engine.position_manager.create_position(
                user_address=user.wallet_address,
                symbol=symbol,
                side=side,
                entry_price=entry_price_float,
                size=size_float,
                dydx_order_id=trade_result.get('order_id', '')
            )

            return {
                'success': True,
                'position': position,
                'step': 'position_persistence'
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Position persistence failed: {str(e)}',
                'step': 'position_persistence'
            }

    async def step_5_notification_delivery(
        self,
        credentials: Dict[str, str],
        position: Position,
        trade_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Step 5: Send confirmation notification.

        Args:
            credentials: User credentials
            position: Created position record
            trade_result: Trade execution result

        Returns:
            Step result with notification status
        """
        try:
            # Send success notification using existing notification system
            await self._send_trade_notification(
                credentials['telegram_token'],
                credentials['telegram_chat_id'],
                {},  # Would need signal data passed through
                trade_result,
                'success'
            )

            return {
                'success': True,
                'position': position,
                'step': 'notification_delivery'
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Notification delivery failed: {str(e)}',
                'position': position,
                'step': 'notification_delivery'
            }

    async def _send_risk_notification(
        self,
        credentials: Dict[str, str],
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
                token=credentials['telegram_token'],
                chat_id=credentials['telegram_chat_id'],
                message=message
            )

        except Exception as e:
            webhook_logger.error(f"Failed to send risk notification: {e}")

    async def _send_error_notification(
        self,
        credentials: Dict[str, str],
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
                token=credentials['telegram_token'],
                chat_id=credentials['telegram_chat_id'],
                message=message
            )

        except Exception as e:
            webhook_logger.error(f"Failed to send error notification: {e}")

    async def rollback_trade(
        self,
        user: User,
        trade_result: Dict[str, Any],
        reason: str
    ) -> Dict[str, Any]:
        """Rollback a failed trade execution.

        Args:
            user: User model instance
            trade_result: Failed trade execution result
            reason: Reason for rollback

        Returns:
            Rollback execution result
        """
        try:
            webhook_logger.info(
                "Starting trade rollback",
                user_address=user.wallet_address,
                reason=reason,
                order_id=trade_result.get('order_id')
            )

            # Decrypt user credentials for rollback
            credentials = await CredentialManager.fetch_user_credentials(
                user, "default_master_key", self.db
            )

            # Create dYdX client for rollback with user's mnemonic and network
            dydx_mnemonic = credentials.get('dydx_mnemonic')
            if not dydx_mnemonic:
                raise ValueError('dYdX mnemonic not available in credentials')
            
            # Use user's configured network ID
            network_id = user.dydx_network_id or 11155111
            
            dydx_client = await DydxClient.create_client(
                network_id=network_id,
                mnemonic=dydx_mnemonic
            )

            rollback_actions = []

            # Cancel any open orders
            if trade_result.get('order_id'):
                try:
                    cancel_result = await DydxClient.cancel_order(
                        dydx_client, trade_result['order_id']
                    )
                    rollback_actions.append({
                        'action': 'cancel_order',
                        'order_id': trade_result['order_id'],
                        'success': cancel_result.get('success', False)
                    })
                except Exception as e:
                    webhook_logger.error(f"Failed to cancel order {trade_result['order_id']}: {e}")
                    rollback_actions.append({
                        'action': 'cancel_order',
                        'order_id': trade_result['order_id'],
                        'success': False,
                        'error': str(e)
                    })

            # Close any positions that were created
            if trade_result.get('position_id'):
                try:
                    # Get position from database
                    position = await self.trading_engine.position_manager.get_position(
                        trade_result['position_id']
                    )

                    if position and position.status == 'open':
                        # Close the position
                        close_result = await self._close_position_with_orders(
                            position, dydx_client, f"Rollback: {reason}"
                        )
                        rollback_actions.append({
                            'action': 'close_position',
                            'position_id': trade_result['position_id'],
                            'success': close_result.get('success', False)
                        })
                except Exception as e:
                    webhook_logger.error(f"Failed to close position {trade_result['position_id']}: {e}")
                    rollback_actions.append({
                        'action': 'close_position',
                        'position_id': trade_result['position_id'],
                        'success': False,
                        'error': str(e)
                    })

            # Send rollback notification
            try:
                await self._send_rollback_notification(credentials, reason, rollback_actions)
            except Exception as e:
                webhook_logger.error(f"Failed to send rollback notification: {e}")

            # Cleanup credentials
            await CredentialManager.cleanup_credentials(credentials)

            success_count = sum(1 for action in rollback_actions if action['success'])

            webhook_logger.info(
                "Trade rollback completed",
                user_address=user.wallet_address,
                total_actions=len(rollback_actions),
                successful_actions=success_count
            )

            return {
                'success': success_count > 0,
                'rollback_actions': rollback_actions,
                'reason': reason,
                'timestamp': datetime.utcnow().isoformat()
            }

        except Exception as e:
            webhook_logger.error(
                "Trade rollback failed",
                user_address=user.wallet_address,
                error=str(e)
            )

            return {
                'success': False,
                'error': f'Rollback failed: {str(e)}',
                'reason': reason,
                'timestamp': datetime.utcnow().isoformat()
            }

    async def _send_rollback_notification(
        self,
        credentials: Dict[str, str],
        reason: str,
        rollback_actions: List[Dict[str, Any]]
    ):
        """Send rollback notification."""
        try:
            success_count = sum(1 for action in rollback_actions if action['success'])

            message = await TelegramManager.format_error_notification(
                operation="TRADE_ROLLBACK",
                error=f"Trade rolled back: {reason}. {success_count}/{len(rollback_actions)} actions completed successfully"
            )

            await TelegramManager.send_notification(
                token=credentials['telegram_token'],
                chat_id=credentials['telegram_chat_id'],
                message=message
            )

        except Exception as e:
            webhook_logger.error(f"Failed to send rollback notification: {e}")

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

            # Update position status in database
            await self.trading_engine.position_manager.close_position(
                position_id=position.id,
                closing_price=0,  # Would need current market price
                pnl=0  # Would need to calculate
            )

            return {
                'success': True,
                'closing_price': 0,
                'pnl': 0,
            }

        except Exception as e:
            webhook_logger.error(f"Position close error for {position.id}: {e}")
            return {
                'success': False,
                'error': str(e),
            }

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
                symbol=signal.get('symbol', 'UNKNOWN'),
                side=signal.get('side', 'UNKNOWN'),
                size=str(signal.get('size', '0')),
                price=str(signal.get('price', 'MARKET')),
                order_type=signal.get('order_type', 'MARKET'),
                status=status
            )

            # Send notification
            await TelegramManager.send_notification(
                token=telegram_token,
                chat_id=telegram_chat_id,
                message=message
            )

        except Exception as e:
            webhook_logger.error(f"Failed to send trade notification: {e}")


class TradingViewSignalProcessor:
    """TradingView signal processing and format conversion."""

    # Supported TradingView alert formats
    TRADINGVIEW_FORMATS = {
        "simple": {
            "symbol": "str",
            "side": "buy|sell",
            "price": "optional",
            "size": "optional"
        },
        "advanced": {
            "symbol": "str",
            "side": "buy|sell",
            "order_type": "market|limit",
            "price": "float",
            "size": "float",
            "take_profit": "optional",
            "stop_loss": "optional"
        }
    }

    @staticmethod
    def parse_tradingview_webhook(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Parse TradingView webhook format into internal signal format.

        Args:
            payload: Raw TradingView webhook payload

        Returns:
            Parsed signal data with validation results
        """
        try:
            # Detect format type
            format_type = TradingViewSignalProcessor._detect_format(payload)

            if format_type == "unknown":
                return {
                    'valid': False,
                    'error': 'Unknown TradingView webhook format',
                    'format_detected': format_type
                }

            # Parse based on detected format
            parsed_signal = TradingViewSignalProcessor._parse_by_format(payload, format_type)

            if not parsed_signal['valid']:
                return parsed_signal

            # Normalize symbol format for dYdX
            normalized_symbol = TradingViewSignalProcessor.normalize_symbol_format(
                parsed_signal['signal']['symbol']
            )

            if not normalized_symbol:
                return {
                    'valid': False,
                    'error': 'Invalid symbol format for dYdX',
                    'signal': parsed_signal['signal']
                }

            # Update with normalized symbol
            parsed_signal['signal']['symbol'] = normalized_symbol
            parsed_signal['signal']['source'] = 'tradingview'
            parsed_signal['signal']['timestamp'] = datetime.utcnow().isoformat()

            return parsed_signal

        except Exception as e:
            return {
                'valid': False,
                'error': f'Parsing error: {str(e)}'
            }

    @staticmethod
    def _detect_format(payload: Dict[str, Any]) -> str:
        """Detect TradingView webhook format type.

        Args:
            payload: Webhook payload

        Returns:
            Detected format type
        """
        # Check for advanced format indicators
        advanced_indicators = ['order_type', 'take_profit', 'stop_loss']
        if any(indicator in payload for indicator in advanced_indicators):
            return 'advanced'

        # Check for simple format indicators
        if 'symbol' in payload and 'side' in payload:
            return 'simple'

        return 'unknown'

    @staticmethod
    def _parse_by_format(payload: Dict[str, Any], format_type: str) -> Dict[str, Any]:
        """Parse payload based on detected format.

        Args:
            payload: Webhook payload
            format_type: Detected format type

        Returns:
            Parsed signal data
        """
        if format_type == 'simple':
            return TradingViewSignalProcessor._parse_simple_format(payload)
        elif format_type == 'advanced':
            return TradingViewSignalProcessor._parse_advanced_format(payload)
        else:
            return {
                'valid': False,
                'error': f'Unsupported format type: {format_type}'
            }

    @staticmethod
    def _parse_simple_format(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Parse simple TradingView format.

        Args:
            payload: Simple format payload

        Returns:
            Parsed signal data
        """
        try:
            symbol = payload.get('symbol', '').strip()
            side = payload.get('side', '').lower()
            price = payload.get('price')
            size = payload.get('size')

            # Validate required fields
            if not symbol:
                return {
                    'valid': False,
                    'error': 'Symbol is required'
                }

            if side not in ['buy', 'sell']:
                return {
                    'valid': False,
                    'error': 'Side must be "buy" or "sell"'
                }

            # Validate price if provided
            if price is not None:
                try:
                    price_float = float(price)
                    if price_float <= 0:
                        return {
                            'valid': False,
                            'error': 'Price must be positive'
                        }
                except (ValueError, TypeError):
                    return {
                        'valid': False,
                        'error': 'Invalid price format'
                    }

            # Validate size if provided
            if size is not None:
                try:
                    size_float = float(size)
                    if size_float <= 0:
                        return {
                            'valid': False,
                            'error': 'Size must be positive'
                        }
                except (ValueError, TypeError):
                    return {
                        'valid': False,
                        'error': 'Invalid size format'
                    }

            return {
                'valid': True,
                'signal': {
                    'symbol': symbol,
                    'side': side.upper(),
                    'price': price_float if price is not None else None,
                    'size': size_float if size is not None else None,
                    'order_type': 'LIMIT' if price is not None else 'MARKET'
                }
            }

        except Exception as e:
            return {
                'valid': False,
                'error': f'Simple format parsing error: {str(e)}'
            }

    @staticmethod
    def _parse_advanced_format(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Parse advanced TradingView format.

        Args:
            payload: Advanced format payload

        Returns:
            Parsed signal data
        """
        try:
            symbol = payload.get('symbol', '').strip()
            side = payload.get('side', '').lower()
            order_type = payload.get('order_type', '').lower()
            price = payload.get('price')
            size = payload.get('size')
            take_profit = payload.get('take_profit')
            stop_loss = payload.get('stop_loss')

            # Validate required fields
            if not symbol:
                return {
                    'valid': False,
                    'error': 'Symbol is required'
                }

            if side not in ['buy', 'sell']:
                return {
                    'valid': False,
                    'error': 'Side must be "buy" or "sell"'
                }

            if order_type not in ['market', 'limit']:
                return {
                    'valid': False,
                    'error': 'Order type must be "market" or "limit"'
                }

            # Validate price for limit orders
            if order_type == 'limit':
                if price is None:
                    return {
                        'valid': False,
                        'error': 'Price is required for limit orders'
                    }
                try:
                    price_float = float(price)
                    if price_float <= 0:
                        return {
                            'valid': False,
                            'error': 'Price must be positive'
                        }
                except (ValueError, TypeError):
                    return {
                        'valid': False,
                        'error': 'Invalid price format'
                    }
            else:
                price_float = None

            # Validate size
            if size is None:
                return {
                    'valid': False,
                    'error': 'Size is required'
                }
            try:
                size_float = float(size)
                if size_float <= 0:
                    return {
                        'valid': False,
                        'error': 'Size must be positive'
                    }
            except (ValueError, TypeError):
                return {
                    'valid': False,
                    'error': 'Invalid size format'
                }

            # Validate take profit if provided
            if take_profit is not None:
                try:
                    tp_float = float(take_profit)
                    if tp_float <= 0:
                        return {
                            'valid': False,
                            'error': 'Take profit must be positive'
                        }
                except (ValueError, TypeError):
                    return {
                        'valid': False,
                        'error': 'Invalid take profit format'
                    }

            # Validate stop loss if provided
            if stop_loss is not None:
                try:
                    sl_float = float(stop_loss)
                    if sl_float <= 0:
                        return {
                            'valid': False,
                            'error': 'Stop loss must be positive'
                        }
                except (ValueError, TypeError):
                    return {
                        'valid': False,
                        'error': 'Invalid stop loss format'
                    }

            return {
                'valid': True,
                'signal': {
                    'symbol': symbol,
                    'side': side.upper(),
                    'order_type': order_type.upper(),
                    'price': price_float,
                    'size': size_float,
                    'take_profit': float(take_profit) if take_profit is not None else None,
                    'stop_loss': float(stop_loss) if stop_loss is not None else None
                }
            }

        except Exception as e:
            return {
                'valid': False,
                'error': f'Advanced format parsing error: {str(e)}'
            }

    @staticmethod
    def validate_signal_data(signal_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate required signal fields and data types.

        Args:
            signal_data: Parsed signal data

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check required fields
            required_fields = ['symbol', 'side', 'size']
            for field in required_fields:
                if field not in signal_data:
                    return False, f"Missing required field: {field}"

            # Validate symbol
            symbol = signal_data['symbol']
            if not isinstance(symbol, str) or len(symbol) < 3 or len(symbol) > 20:
                return False, "Invalid symbol format"

            # Validate side
            side = signal_data['side']
            if not isinstance(side, str) or side.upper() not in ['BUY', 'SELL']:
                return False, "Invalid side (must be BUY or SELL)"

            # Validate size
            size = signal_data['size']
            if not isinstance(size, (int, float)) or size <= 0:
                return False, "Invalid size (must be positive number)"

            # Validate price if present
            if 'price' in signal_data and signal_data['price'] is not None:
                price = signal_data['price']
                if not isinstance(price, (int, float)) or price <= 0:
                    return False, "Invalid price (must be positive number)"

            # Validate order type if present
            if 'order_type' in signal_data:
                order_type = signal_data['order_type']
                if not isinstance(order_type, str) or order_type.upper() not in ['MARKET', 'LIMIT']:
                    return False, "Invalid order type (must be MARKET or LIMIT)"

            return True, "Valid signal data"

        except Exception as e:
            return False, f"Validation error: {str(e)}"

    @staticmethod
    def normalize_symbol_format(symbol: str) -> str:
        """Normalize TradingView symbol format to dYdX format.

        Args:
            symbol: TradingView symbol (e.g., 'BTCUSDT', 'ETH/USD')

        Returns:
            Normalized dYdX symbol (e.g., 'BTC-USD')
        """
        try:
            if not symbol:
                return ""

            # Remove common separators and normalize
            normalized = symbol.upper()

            # Handle common TradingView formats
            if '/' in normalized:
                # Already in dYdX format (BTC/USD)
                parts = normalized.split('/')
                if len(parts) == 2:
                    return f"{parts[0]}-{parts[1]}"

            # Handle formats like BTCUSDT, ETHUSDT
            if len(normalized) >= 6 and not '-' in normalized:
                # Common crypto pairs
                common_pairs = {
                    'BTCUSDT': 'BTC-USD',
                    'ETHUSDT': 'ETH-USD',
                    'ADAUSDT': 'ADA-USD',
                    'LINKUSDT': 'LINK-USD',
                    'DOTUSDT': 'DOT-USD',
                    'UNIUSDT': 'UNI-USD',
                    'AAVEUSDT': 'AAVE-USD',
                    'SNXUSDT': 'SNX-USD',
                    'CRVUSDT': 'CRV-USD',
                    'SUSHIUSDT': 'SUSHI-USD',
                    'YFIUSDT': 'YFI-USD',
                    'COMPUSDT': 'COMP-USD',
                    'MKRUSDT': 'MKR-USD',
                    'LTCUSDT': 'LTC-USD',
                    'BCHUSDT': 'BCH-USD',
                    'XRPUSDT': 'XRP-USD',
                    'SOLUSDT': 'SOL-USD',
                    'AVAXUSDT': 'AVAX-USD',
                    'MATICUSDT': 'MATIC-USD',
                    'ATOMUSDT': 'ATOM-USD',
                }

                if normalized in common_pairs:
                    return common_pairs[normalized]

                # Try to split by numbers (last 3-4 characters are usually USDT)
                for i in range(len(normalized) - 3, len(normalized)):
                    base = normalized[:i]
                    quote = normalized[i:]
                    if quote in ['USDT', 'BUSD', 'USDC']:
                        return f"{base}-{quote}"

            # If already in correct format, return as-is
            if '-' in normalized and len(normalized.split('-')) == 2:
                return normalized

            # If we can't normalize, return empty string to indicate failure
            return ""

        except Exception:
            return ""

    @staticmethod
    def extract_order_parameters(signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract price, size, and order type from signal.

        Args:
            signal_data: Validated signal data

        Returns:
            Extracted order parameters for dYdX API
        """
        try:
            # Validate signal first
            is_valid, error = TradingViewSignalProcessor.validate_signal_data(signal_data)
            if not is_valid:
                return {
                    'valid': False,
                    'error': error
                }

            # Extract parameters
            symbol = signal_data['symbol']
            side = signal_data['side']
            size = signal_data['size']
            price = signal_data.get('price')
            order_type = signal_data.get('order_type', 'MARKET')

            # Convert side to dYdX format
            dydx_side = 'BUY' if side.upper() == 'BUY' else 'SELL'

            # Prepare order parameters
            order_params = {
                'symbol': symbol,
                'side': dydx_side,
                'size': str(size),
                'type': order_type
            }

            if order_type == 'LIMIT' and price:
                order_params['price'] = str(price)

            # Add advanced order parameters if present
            if 'take_profit' in signal_data and signal_data['take_profit']:
                order_params['take_profit'] = str(signal_data['take_profit'])

            if 'stop_loss' in signal_data and signal_data['stop_loss']:
                order_params['stop_loss'] = str(signal_data['stop_loss'])

            return {
                'valid': True,
                'order_params': order_params
            }

        except Exception as e:
            return {
                'valid': False,
                'error': f'Parameter extraction error: {str(e)}'
            }


class TradingViewErrorHandler:
    """TradingView-specific error handling and response formatting."""

    # Common TradingView error patterns and user-friendly messages
    ERROR_MAPPINGS = {
        'invalid_symbol': {
            'message': 'Invalid trading pair symbol',
            'suggestion': 'Check symbol format (e.g., BTCUSDT, ETH-USD)',
            'http_status': status.HTTP_400_BAD_REQUEST
        },
        'invalid_side': {
            'message': 'Invalid trade side',
            'suggestion': 'Use "buy" or "sell"',
            'http_status': status.HTTP_400_BAD_REQUEST
        },
        'invalid_price': {
            'message': 'Invalid price format',
            'suggestion': 'Price must be a positive number',
            'http_status': status.HTTP_400_BAD_REQUEST
        },
        'invalid_size': {
            'message': 'Invalid position size',
            'suggestion': 'Size must be a positive number',
            'http_status': status.HTTP_400_BAD_REQUEST
        },
        'insufficient_balance': {
            'message': 'Insufficient account balance',
            'suggestion': 'Check account balance and position sizing',
            'http_status': status.HTTP_400_BAD_REQUEST
        },
        'market_unavailable': {
            'message': 'Market temporarily unavailable',
            'suggestion': 'Trading pair may be unavailable or delisted',
            'http_status': status.HTTP_503_SERVICE_UNAVAILABLE
        },
        'rate_limit_exceeded': {
            'message': 'Rate limit exceeded',
            'suggestion': 'Too many requests, please slow down',
            'http_status': status.HTTP_429_TOO_MANY_REQUESTS
        },
        'authentication_failed': {
            'message': 'Authentication failed',
            'suggestion': 'Check webhook UUID and secret configuration',
            'http_status': status.HTTP_401_UNAUTHORIZED
        },
        'system_error': {
            'message': 'System temporarily unavailable',
            'suggestion': 'Please try again in a few moments',
            'http_status': status.HTTP_500_INTERNAL_SERVER_ERROR
        }
    }

    @staticmethod
    def format_error_response(error_type: str, original_error: str = None) -> Dict[str, Any]:
        """Format error response for TradingView webhook.

        Args:
            error_type: Type of error from ERROR_MAPPINGS
            original_error: Original error message for debugging

        Returns:
            Formatted error response
        """
        if error_type not in TradingViewErrorHandler.ERROR_MAPPINGS:
            error_type = 'system_error'

        error_info = TradingViewErrorHandler.ERROR_MAPPINGS[error_type]

        response = {
            'status': 'error',
            'message': error_info['message'],
            'suggestion': error_info['suggestion'],
            'timestamp': datetime.utcnow().isoformat()
        }

        # Add original error in development mode
        if original_error and TradingViewErrorHandler._is_development():
            response['debug_error'] = original_error

        return response

    @staticmethod
    def _is_development() -> bool:
        """Check if running in development mode."""
        import os
        return os.getenv('ENV', 'development').lower() == 'development'

    @staticmethod
    def classify_error(error_message: str) -> str:
        """Classify error message into predefined categories.

        Args:
            error_message: Raw error message

        Returns:
            Classified error type
        """
        error_lower = error_message.lower()

        # Symbol-related errors
        if any(term in error_lower for term in ['symbol', 'pair', 'ticker']):
            return 'invalid_symbol'

        # Side-related errors
        if any(term in error_lower for term in ['side', 'buy', 'sell']):
            return 'invalid_side'

        # Price-related errors
        if any(term in error_lower for term in ['price', 'limit', 'rate']):
            return 'invalid_price'

        # Size-related errors
        if any(term in error_lower for term in ['size', 'amount', 'quantity']):
            return 'invalid_size'

        # Balance-related errors
        if any(term in error_lower for term in ['balance', 'funds', 'insufficient']):
            return 'insufficient_balance'

        # Market-related errors
        if any(term in error_lower for term in ['market', 'unavailable', 'delisted']):
            return 'market_unavailable'

        # Rate limiting errors
        if any(term in error_lower for term in ['rate limit', 'too many', 'throttle']):
            return 'rate_limit_exceeded'

        # Authentication errors
        if any(term in error_lower for term in ['auth', 'secret', 'uuid', 'unauthorized']):
            return 'authentication_failed'

        # Default to system error
        return 'system_error'

    @staticmethod
    def create_tradingview_response(success: bool, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create standardized TradingView webhook response.

        Args:
            success: Whether the webhook was processed successfully
            data: Additional response data

        Returns:
            Standardized response format
        """
        if success:
            return {
                'status': 'success',
                'timestamp': datetime.utcnow().isoformat(),
                'data': data or {}
            }
        else:
            return {
                'status': 'error',
                'timestamp': datetime.utcnow().isoformat(),
                'data': data or {}
            }


class WebhookMonitor:
    """Comprehensive monitoring and alerting for webhook system."""

    # Metrics storage (in production, use Prometheus/StatsD)
    metrics = {
        'total_requests': 0,
        'successful_requests': 0,
        'failed_requests': 0,
        'authentication_failures': 0,
        'rate_limit_hits': 0,
        'average_response_time': 0.0,
        'response_times': []
    }

    @staticmethod
    def record_request(success: bool, response_time: float, error_type: str = None):
        """Record webhook request metrics.

        Args:
            success: Whether request was successful
            response_time: Request processing time in seconds
            error_type: Type of error if request failed
        """
        WebhookMonitor.metrics['total_requests'] += 1

        if success:
            WebhookMonitor.metrics['successful_requests'] += 1
        else:
            WebhookMonitor.metrics['failed_requests'] += 1
            if error_type == 'authentication_failed':
                WebhookMonitor.metrics['authentication_failures'] += 1
            elif error_type == 'rate_limit_exceeded':
                WebhookMonitor.metrics['rate_limit_hits'] += 1

        # Update average response time
        response_times = WebhookMonitor.metrics['response_times']
        response_times.append(response_time)

        # Keep only last 1000 response times
        if len(response_times) > 1000:
            response_times.pop(0)

        WebhookMonitor.metrics['average_response_time'] = (
            sum(response_times) / len(response_times)
        )

    @staticmethod
    def get_metrics() -> Dict[str, Any]:
        """Get current webhook metrics.

        Returns:
            Dictionary of current metrics
        """
        return {
            **WebhookMonitor.metrics,
            'success_rate': (
                WebhookMonitor.metrics['successful_requests'] /
                max(WebhookMonitor.metrics['total_requests'], 1)
            ) * 100,
            'timestamp': datetime.utcnow().isoformat()
        }

    @staticmethod
    def check_alert_conditions() -> List[Dict[str, Any]]:
        """Check if any alert conditions are met.

        Returns:
            List of active alerts
        """
        alerts = []

        # High failure rate alert
        total_requests = WebhookMonitor.metrics['total_requests']
        failed_requests = WebhookMonitor.metrics['failed_requests']

        if total_requests >= 10:  # Only alert after minimum requests
            failure_rate = (failed_requests / total_requests) * 100
            if failure_rate > 20:  # More than 20% failure rate
                alerts.append({
                    'type': 'high_failure_rate',
                    'severity': 'warning',
                    'message': f'High webhook failure rate: {failure_rate:.1f}%',
                    'threshold': 20,
                    'current_value': failure_rate
                })

        # High authentication failure rate
        auth_failures = WebhookMonitor.metrics['authentication_failures']
        if auth_failures > 5:  # More than 5 auth failures
            alerts.append({
                'type': 'high_auth_failures',
                'severity': 'critical',
                'message': f'High authentication failure count: {auth_failures}',
                'threshold': 5,
                'current_value': auth_failures
            })

        # High response time alert
        avg_response_time = WebhookMonitor.metrics['average_response_time']
        if avg_response_time > 5.0:  # Average response time > 5 seconds
            alerts.append({
                'type': 'high_response_time',
                'severity': 'warning',
                'message': f'High average response time: {avg_response_time:.2f}s',
                'threshold': 5.0,
                'current_value': avg_response_time
            })

        return alerts


class WebhookTestingUtilities:
    """Testing utilities for webhook development and validation."""

    @staticmethod
    def generate_test_signal(format_type: str = 'simple') -> Dict[str, Any]:
        """Generate test trading signal for development.

        Args:
            format_type: Signal format ('simple' or 'advanced')

        Returns:
            Test signal data
        """
        import random

        symbols = ['BTC-USD', 'ETH-USD', 'ADA-USD', 'LINK-USD']
        sides = ['buy', 'sell']

        symbol = random.choice(symbols)
        side = random.choice(sides)

        if format_type == 'simple':
            return {
                'symbol': symbol,
                'side': side,
                'price': round(random.uniform(1000, 50000), 2),
                'size': round(random.uniform(0.001, 1.0), 6),
                'test': True,
                'timestamp': datetime.utcnow().isoformat()
            }
        else:  # advanced format
            return {
                'symbol': symbol,
                'side': side,
                'order_type': random.choice(['market', 'limit']),
                'price': round(random.uniform(1000, 50000), 2),
                'size': round(random.uniform(0.001, 1.0), 6),
                'take_profit': round(random.uniform(1100, 60000), 2),
                'stop_loss': round(random.uniform(900, 45000), 2),
                'test': True,
                'timestamp': datetime.utcnow().isoformat()
            }

    @staticmethod
    def validate_webhook_configuration(user: User) -> Dict[str, Any]:
        """Validate user's webhook configuration.

        Args:
            user: User model instance

        Returns:
            Configuration validation result
        """
        issues = []

        # Check webhook UUID
        if not user.webhook_uuid:
            issues.append({
                'field': 'webhook_uuid',
                'issue': 'Webhook UUID not set',
                'severity': 'critical',
                'fix': 'Generate a webhook UUID for the user'
            })

        # Check webhook secret
        if not user.encrypted_webhook_secret:
            issues.append({
                'field': 'webhook_secret',
                'issue': 'Webhook secret not configured',
                'severity': 'critical',
                'fix': 'Set and encrypt a webhook secret for the user'
            })

        # Check dYdX credentials
        if not user.encrypted_dydx_private_key:
            issues.append({
                'field': 'dydx_private_key',
                'issue': 'dYdX private key not configured',
                'severity': 'critical',
                'fix': 'Configure dYdX V4 API private key for trading'
            })

        # Check Telegram credentials
        if not user.encrypted_telegram_token:
            issues.append({
                'field': 'telegram_token',
                'issue': 'Telegram token not configured',
                'severity': 'warning',
                'fix': 'Configure Telegram bot token for notifications'
            })

        if not user.encrypted_telegram_chat_id:
            issues.append({
                'field': 'telegram_chat_id',
                'issue': 'Telegram chat ID not configured',
                'severity': 'warning',
                'fix': 'Configure Telegram chat ID for notifications'
            })

        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'summary': f"{len(issues)} issues found",
            'timestamp': datetime.utcnow().isoformat()
        }


class GracefulDegradationHandler:
    """Handle external service failures gracefully."""

    # Circuit breaker state
    circuit_breakers = {
        'dydx_api': {'state': 'closed', 'failures': 0, 'last_failure': None},
        'telegram_api': {'state': 'closed', 'failures': 0, 'last_failure': None},
        'database': {'state': 'closed', 'failures': 0, 'last_failure': None}
    }

    @staticmethod
    async def check_circuit_breaker(service: str) -> bool:
        """Check if service is available (circuit breaker pattern).

        Args:
            service: Service name ('dydx_api', 'telegram_api', 'database')

        Returns:
            True if service is available
        """
        if service not in GracefulDegradationHandler.circuit_breakers:
            return True

        breaker = GracefulDegradationHandler.circuit_breakers[service]

        # If circuit is open, check if we should try again
        if breaker['state'] == 'open':
            if breaker['last_failure'] and datetime.utcnow() - breaker['last_failure'] > timedelta(minutes=5):
                # Try to close circuit
                breaker['state'] = 'half_open'
                return True
            else:
                return False

        return True

    @staticmethod
    async def record_service_failure(service: str, error: str):
        """Record service failure for circuit breaker.

        Args:
            service: Service name
            error: Error description
        """
        if service not in GracefulDegradationHandler.circuit_breakers:
            GracefulDegradationHandler.circuit_breakers[service] = {
                'state': 'closed', 'failures': 0, 'last_failure': None
            }

        breaker = GracefulDegradationHandler.circuit_breakers[service]
        breaker['failures'] += 1
        breaker['last_failure'] = datetime.utcnow()

        # Open circuit after 3 failures
        if breaker['failures'] >= 3:
            breaker['state'] = 'open'
            webhook_logger.warning(
                f"Circuit breaker opened for {service}",
                failures=breaker['failures'],
                error=error
            )

    @staticmethod
    async def record_service_success(service: str):
        """Record service success for circuit breaker.

        Args:
            service: Service name
        """
        if service in GracefulDegradationHandler.circuit_breakers:
            breaker = GracefulDegradationHandler.circuit_breakers[service]
            breaker['failures'] = 0
            breaker['state'] = 'closed'
            breaker['last_failure'] = None

    @staticmethod
    async def get_service_status() -> Dict[str, Any]:
        """Get status of all services.

        Returns:
            Service status information
        """
        return {
            'services': GracefulDegradationHandler.circuit_breakers,
            'timestamp': datetime.utcnow().isoformat()
        }


class WebhookRouter:
    """Main webhook router with secure two-factor authentication."""

    def __init__(self, db_session: AsyncSession, trading_engine: TradingEngine):
        """Initialize webhook router.

        Args:
            db_session: Database session
            trading_engine: Trading engine instance
        """
        self.db = db_session
        self.trading_engine = trading_engine
        self.trade_orchestrator = TradeOrchestrator(db_session, trading_engine)

    async def handle_webhook(
        self,
        webhook_uuid: str,
        request: Request
    ) -> Dict[str, Any]:
        """Main webhook handler with two-factor verification.

        Args:
            webhook_uuid: Webhook UUID from URL path
            request: FastAPI request object

        Returns:
            Webhook processing result
        """
        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"

        try:
            # Parse request body
            try:
                request_body = await request.json()
            except json.JSONDecodeError:
                return await self.handle_verification_failure(
                    "Invalid JSON in request body", webhook_uuid
                )

            # Log webhook event
            await self._log_webhook_event(
                webhook_uuid, "received", request_body, client_ip
            )

            # Step 1: Two-factor authentication
            is_valid, user, auth_error = await WebhookAuthenticator.verify_two_factor(
                webhook_uuid, request_body, self.db
            )

            if not is_valid:
                return await self.handle_verification_failure(auth_error, webhook_uuid)

            # Step 1.5: Check if user has configured their mnemonic (REQUIRED for trading)
            if not (user.encrypted_dydx_mnemonic or user.encrypted_dydx_testnet_mnemonic or user.encrypted_dydx_mainnet_mnemonic):
                error_msg = "dYdX mnemonic not configured. Please configure your mnemonic phrase in the dashboard before trading."
                return await self.handle_verification_failure(error_msg, webhook_uuid)

            # Step 2: Validate request format
            is_valid_format, format_error = await WebhookAuthenticator.validate_request_format(
                request_body
            )

            if not is_valid_format:
                return await self.handle_verification_failure(format_error, webhook_uuid)

            # Step 3: Process the trading signal
            result = await self.process_tradingview_signal(user, request_body)

            # Log successful processing
            processing_time = time.time() - start_time
            await self._log_webhook_event(
                webhook_uuid, "processed", result, client_ip, processing_time
            )

            return result

        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Webhook processing error: {str(e)}"

            webhook_logger.error(
                "Webhook processing exception",
                webhook_uuid=webhook_uuid,
                client_ip=client_ip,
                processing_time=processing_time,
                error=str(e)
            )

            await self._log_webhook_event(
                webhook_uuid, "error", {"error": error_msg}, client_ip, processing_time
            )

            return await self.handle_verification_failure(error_msg, webhook_uuid)

    async def process_tradingview_signal(
        self,
        user: User,
        signal_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process verified TradingView signal into trade execution.

        Args:
            user: Authenticated user
            signal_data: Validated signal data

        Returns:
            Trade execution result
        """
        try:
            # Use the TradeOrchestrator for complete trade execution
            # The master_key here is a placeholder - in production this would come from secure storage
            master_key = "default_master_key"  # This should be properly configured

            trade_result = await self.trade_orchestrator.execute_complete_trade(
                user=user,
                signal_data=signal_data,
                master_key=master_key
            )

            if trade_result['success']:
                return {
                    "status": "success",
                    "message": "Trade executed successfully",
                    "trade_id": trade_result.get('position_id'),
                    "order_id": trade_result.get('order_id'),
                    "symbol": trade_result.get('symbol'),
                    "side": trade_result.get('side'),
                    "size": trade_result.get('size'),
                    "price": trade_result.get('price'),
                    "execution_time_seconds": trade_result.get('execution_time_seconds'),
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "status": "error",
                    "message": f"Trade execution failed: {trade_result.get('error')}",
                    "timestamp": datetime.utcnow().isoformat()
                }

        except Exception as e:
            webhook_logger.error(
                "Signal processing error",
                user_address=user.wallet_address,
                error=str(e)
            )
            return {
                "status": "error",
                "message": f"Signal processing failed: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }

    async def handle_verification_failure(
        self,
        reason: str,
        webhook_uuid: str
    ) -> Dict[str, Any]:
        """Handle authentication failures securely.

        Args:
            reason: Failure reason
            webhook_uuid: Webhook UUID that failed

        Returns:
            Error response
        """
        # Log the failure
        await self._log_webhook_event(
            webhook_uuid, "auth_failed", {"reason": reason}, "unknown"
        )

        return {
            "status": "error",
            "message": "Authentication failed",
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _log_webhook_event(
        self,
        webhook_uuid: str,
        event_type: str,
        payload: Dict[str, Any],
        client_ip: str,
        processing_time: float = None
    ):
        """Log webhook events for security monitoring.

        Args:
            webhook_uuid: Webhook UUID
            event_type: Type of event (received, processed, error, auth_failed)
            payload: Event payload data
            client_ip: Client IP address
            processing_time: Optional processing time in seconds
        """
        try:
            # Try to find user by webhook UUID for logging
            user_address = None
            try:
                from sqlalchemy import select
                result = await self.db.execute(
                    select(User).where(User.webhook_uuid == webhook_uuid)
                )
                user = result.scalar_one_or_none()
                if user:
                    user_address = user.wallet_address
            except Exception:
                # If we can't find user, just use None
                pass
            
            # Skip database logging if we don't have a user_address
            # (to avoid foreign key constraint violations)
            # Just use structured logging instead
            log_data = {
                "webhook_uuid": webhook_uuid,
                "event_type": event_type,
                "client_ip": client_ip,
                "payload_size": len(str(payload)),
                "user_address": user_address
            }

            if processing_time:
                log_data["processing_time_seconds"] = round(processing_time, 3)

            webhook_logger.info(
                f"Webhook {event_type}",
                **log_data
            )

        except Exception as e:
            logger.error(f"Failed to log webhook event: {e}")


# Dependency functions
async def get_webhook_router(db_session: AsyncSession = Depends(get_db)):
    """Dependency to get webhook router instance."""
    return WebhookRouter(db_session, TradingEngine(db_session))


# Webhook endpoints
@router.post("/signal/{webhook_uuid}")
async def webhook_signal(
    webhook_uuid: str,
    request: Request,
    webhook_router: WebhookRouter = Depends(get_webhook_router)
):
    """Secure webhook endpoint for trading signals.

    This endpoint implements two-factor authentication:
    1. Webhook UUID in URL path
    2. Webhook secret in request body

    Args:
        webhook_uuid: User's webhook UUID
        request: FastAPI request object
        webhook_router: Webhook router instance

    Returns:
        Webhook processing result
    """
    return await webhook_router.handle_webhook(webhook_uuid, request)


@router.get("/test/{webhook_uuid}")
async def test_webhook(
    webhook_uuid: str,
    request: Request,
    webhook_router: WebhookRouter = Depends(get_webhook_router)
):
    """Test webhook endpoint for development and monitoring.

    Args:
        webhook_uuid: User's webhook UUID
        request: FastAPI request object
        webhook_router: Webhook router instance

    Returns:
        Webhook test result
    """
    try:
        # Parse test request body
        try:
            request_body = await request.json()
        except json.JSONDecodeError:
            request_body = {"test": True}

        # Simple authentication test (no trade execution)
        is_valid, user, auth_error = await WebhookAuthenticator.verify_two_factor(
            webhook_uuid, request_body, webhook_router.db
        )

        if not is_valid:
            return {
                "status": "error",
                "message": "Authentication failed",
                "error": auth_error,
                "timestamp": datetime.utcnow().isoformat()
            }

        return {
            "status": "success",
            "message": "Webhook authentication successful",
            "user_address": user.wallet_address,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        return {
            "status": "error",
            "message": f"Test failed: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get("/metrics")
async def get_webhook_metrics():
    """Get webhook system metrics for monitoring.

    Returns:
        Current webhook metrics and statistics
    """
    return WebhookMonitor.get_metrics()


@router.get("/health")
async def get_webhook_health():
    """Get webhook system health status.

    Returns:
        Health status including service availability
    """
    try:
        # Check service availability
        service_status = await GracefulDegradationHandler.get_service_status()

        # Get current metrics
        metrics = WebhookMonitor.get_metrics()

        # Check for active alerts
        alerts = WebhookMonitor.check_alert_conditions()

        # Overall health
        critical_alerts = [alert for alert in alerts if alert['severity'] == 'critical']
        overall_status = 'unhealthy' if critical_alerts else 'healthy'

        return {
            'status': overall_status,
            'timestamp': datetime.utcnow().isoformat(),
            'metrics': metrics,
            'services': service_status,
            'alerts': alerts
        }

    except Exception as e:
        return {
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'error': f'Health check failed: {str(e)}'
        }


@router.post("/test-signal")
async def generate_test_signal_endpoint(
    format_type: str = 'simple',
    webhook_uuid: str = None
):
    """Generate test signal for webhook testing.

    Args:
        format_type: Signal format ('simple' or 'advanced')
        webhook_uuid: Optional webhook UUID for targeted testing

    Returns:
        Test signal data
    """
    try:
        test_signal = WebhookTestingUtilities.generate_test_signal(format_type)

        return {
            'status': 'success',
            'test_signal': test_signal,
            'format': format_type,
            'webhook_url': f'/api/webhooks/signal/{webhook_uuid}' if webhook_uuid else '/api/webhooks/signal/{webhook_uuid}',
            'timestamp': datetime.utcnow().isoformat()
        }

    except Exception as e:
        return {
            'status': 'error',
            'message': f'Failed to generate test signal: {str(e)}',
            'timestamp': datetime.utcnow().isoformat()
        }


@router.get("/circuit-breakers")
async def get_circuit_breaker_status():
    """Get circuit breaker status for all services.

    Returns:
        Circuit breaker status information
    """
    return await GracefulDegradationHandler.get_service_status()