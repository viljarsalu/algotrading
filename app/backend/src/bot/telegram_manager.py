"""
Telegram Manager Module - User-specific Telegram Notifications.

This module provides stateless Telegram notification functionality,
accepting user credentials as parameters for each operation.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
import httpx

logger = logging.getLogger(__name__)


class TelegramManager:
    """Stateless Telegram manager for user-specific notifications."""

    # Telegram API configuration
    API_BASE_URL = "https://api.telegram.org/bot"

    @staticmethod
    async def send_notification(
        token: str,
        chat_id: str,
        message: str,
        parse_mode: str = "HTML"
    ) -> bool:
        """Send notification to user's Telegram.

        Args:
            token: Telegram bot token
            chat_id: Telegram chat ID
            message: Message to send
            parse_mode: Message parse mode ('HTML' or 'Markdown')

        Returns:
            True if message was sent successfully

        Raises:
            ValueError: If parameters are invalid
        """
        try:
            # Validate parameters
            if not token or not token.startswith('bot'):
                raise ValueError("Invalid Telegram bot token")

            if not chat_id:
                raise ValueError("Chat ID is required")

            if not message or len(message) > 4096:  # Telegram message limit
                raise ValueError("Message must be between 1 and 4096 characters")

            if parse_mode not in ['HTML', 'Markdown']:
                raise ValueError("Parse mode must be 'HTML' or 'Markdown'")

            # Prepare API request
            url = f"{TelegramManager.API_BASE_URL}{token}/sendMessage"

            payload = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': parse_mode,
                'disable_web_page_preview': True,
            }

            # Send message with timeout
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)

            # Check response
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    logger.info(f"Telegram message sent to {chat_id}")
                    return True
                else:
                    logger.error(f"Telegram API error: {result.get('description')}")
                    return False
            else:
                logger.error(f"Telegram HTTP error: {response.status_code}")
                return False

        except httpx.TimeoutException:
            logger.error("Telegram request timeout")
            return False
        except httpx.RequestError as e:
            logger.error(f"Telegram request error: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False

    @staticmethod
    async def format_trade_notification(
        symbol: str,
        side: str,
        size: str,
        price: str,
        order_type: str,
        status: str
    ) -> str:
        """Format trade notification message.

        Args:
            symbol: Trading pair symbol
            side: Trade side ('BUY' or 'SELL')
            size: Position size
            price: Execution price
            order_type: Order type ('MARKET' or 'LIMIT')
            status: Order status

        Returns:
            Formatted notification message
        """
        try:
            # Create emoji based on side
            emoji = "🚀" if side.upper() == "BUY" else "🔻"

            # Format message with HTML
            message = f"""
{emoji} <b>Trade Executed</b>

<b>Symbol:</b> {symbol}
<b>Side:</b> {side.upper()}
<b>Size:</b> {size}
<b>Price:</b> ${price}
<b>Type:</b> {order_type}
<b>Status:</b> {status}

<i>Automated trading notification</i>
            """.strip()

            return message

        except Exception as e:
            logger.error(f"Failed to format trade notification: {e}")
            return f"Trade: {symbol} {side} {size} @ {price} ({status})"

    @staticmethod
    async def format_position_notification(
        position: Dict[str, Any],
        action: str,
        reason: str = ""
    ) -> str:
        """Format position update notification.

        Args:
            position: Position data dictionary
            action: Action performed ('OPENED', 'CLOSED', 'MODIFIED')
            reason: Optional reason for the action

        Returns:
            Formatted position notification message
        """
        try:
            # Position status emoji
            status_emoji = {
                'OPENED': "📈",
                'CLOSED': "✅",
                'MODIFIED': "🔄",
                'CANCELLED': "❌"
            }.get(action.upper(), "📊")

            # Calculate P&L if position is closed
            pnl_info = ""
            if action.upper() == 'CLOSED' and 'pnl' in position:
                pnl = float(position['pnl'])
                pnl_emoji = "💰" if pnl > 0 else "💸"
                pnl_info = f"\n<b>P&L:</b> {pnl_emoji} ${pnl:.4f}"

            # Format message with HTML
            message = f"""{status_emoji} <b>Position {action.title()}</b>

<b>Symbol:</b> {position.get('symbol', 'N/A')}
<b>Size:</b> {position.get('size', 'N/A')}
<b>Entry Price:</b> ${position.get('entry_price', 'N/A')}{pnl_info}

<i>Automated position update</i>""".strip()

            # Add reason if provided
            if reason:
                message += f"\n<b>Reason:</b> {reason}"

            return message

        except Exception as e:
            logger.error(f"Failed to format position notification: {e}")
            return f"Position {action}: {position.get('symbol', 'N/A')}"

    @staticmethod
    async def format_error_notification(
        operation: str,
        error: str,
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        """Format error notification message.

        Args:
            operation: Operation that failed
            error: Error message
            details: Optional additional error details

        Returns:
            Formatted error notification message
        """
        try:
            # Format error message with HTML
            message = f"""
⚠️ <b>Trading Error</b>

<b>Operation:</b> {operation}
<b>Error:</b> {error}
            """.strip()

            # Add details if provided
            if details:
                for key, value in details.items():
                    message += f"\n<b>{key.title()}:</b> {value}"

            message += "\n\n<i>Please check your trading configuration</i>"

            return message

        except Exception as e:
            logger.error(f"Failed to format error notification: {e}")
            return f"Error in {operation}: {error}"

    @staticmethod
    async def format_risk_warning_notification(
        warning_type: str,
        symbol: str,
        current_value: float,
        limit_value: float,
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        """Format risk management warning notification.

        Args:
            warning_type: Type of warning ('POSITION_SIZE', 'EXPOSURE', 'MARGIN')
            symbol: Trading pair symbol
            current_value: Current risk metric value
            limit_value: Risk limit value
            details: Optional additional warning details

        Returns:
            Formatted risk warning message
        """
        try:
            # Warning type emoji
            warning_emoji = {
                'POSITION_SIZE': "📏",
                'EXPOSURE': "⚖️",
                'MARGIN': "💳",
                'LEVERAGE': "🔆"
            }.get(warning_type.upper(), "⚠️")

            # Format message with HTML
            message = f"""
{warning_emoji} <b>Risk Warning</b>

<b>Type:</b> {warning_type.replace('_', ' ').title()}
<b>Symbol:</b> {symbol}
<b>Current:</b> {current_value}
<b>Limit:</b> {limit_value}
            """.strip()

            # Add details if provided
            if details:
                for key, value in details.items():
                    message += f"\n<b>{key.title()}:</b> {value}"

            message += "\n\n<i>Risk management alert</i>"

            return message

        except Exception as e:
            logger.error(f"Failed to format risk warning notification: {e}")
            return f"Risk Warning: {warning_type} for {symbol}"

    @staticmethod
    async def test_connection(token: str, chat_id: str) -> Dict[str, Any]:
        """Test Telegram connection and permissions.

        Args:
            token: Telegram bot token
            chat_id: Telegram chat ID to test

        Returns:
            Connection test result with details
        """
        try:
            # Send a test message
            test_message = "🤖 <b>Connection Test</b>\n\n<i>Trading bot is ready!</i>"

            success = await TelegramManager.send_notification(
                token=token,
                chat_id=chat_id,
                message=test_message
            )

            if success:
                return {
                    'success': True,
                    'message': 'Connection test successful',
                    'bot_info': 'Connected and ready to send notifications'
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to send test message',
                    'message': 'Check bot token and chat ID'
                }

        except Exception as e:
            logger.error(f"Telegram connection test failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Connection test failed'
            }