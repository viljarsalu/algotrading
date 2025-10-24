"""
Position Notification Manager Module - Telegram Notifications for Positions.

This module handles all position-related notifications including closures,
monitoring alerts, and system status updates.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from decimal import Decimal

from ..db.models import Position
from ..bot.telegram_manager import TelegramManager

logger = logging.getLogger(__name__)


class PositionNotificationManager:
    """Manages position-related notifications via Telegram."""

    @staticmethod
    async def send_position_closure_notification(
        credentials: Dict[str, str],
        position: Position,
        closing_data: Dict[str, Any]
    ) -> bool:
        """Send detailed position closure notification.

        Args:
            credentials: User credentials including Telegram token and chat ID
            position: Position that was closed
            closing_data: Position closure data

        Returns:
            True if notification was sent successfully
        """
        try:
            # Check if user has Telegram credentials
            telegram_token = credentials.get('telegram_token')
            telegram_chat_id = credentials.get('telegram_chat_id')

            if not telegram_token or not telegram_chat_id:
                logger.warning(f"No Telegram credentials found for user {credentials.get('wallet_address')}")
                return False

            # Format the closure message
            message = await PositionNotificationManager.format_closure_message(
                position=position,
                closing_reason=closing_data.get('closing_reason', 'Unknown'),
                pnl=closing_data.get('pnl', 0),
                closing_price=closing_data.get('closing_price', 0)
            )

            # Send the notification
            success = await TelegramManager.send_notification(
                token=telegram_token,
                chat_id=telegram_chat_id,
                message=message
            )

            if success:
                logger.info(f"Position closure notification sent for position {position.id}")
            else:
                logger.error(f"Failed to send position closure notification for position {position.id}")

            return success

        except Exception as e:
            logger.error(f"Error sending position closure notification for {position.id}: {e}")
            return False

    @staticmethod
    async def format_closure_message(
        position: Position,
        closing_reason: str,
        pnl: float,
        closing_price: float
    ) -> str:
        """Format position closure message with all relevant details.

        Args:
            position: Position that was closed
            closing_reason: Reason for closure
            pnl: Profit and loss amount
            closing_price: Price at closure

        Returns:
            Formatted message string
        """
        try:
            # Position status emoji
            status_emoji = "✅"  # Closed successfully

            # P&L emoji and color
            if pnl >= 0:
                pnl_emoji = "💰"
                pnl_text = f"<b>+${pnl:.4f}</b>"
            else:
                pnl_emoji = "💸"
                pnl_text = f"<b style='color: red'>${pnl:.4f}</b>"

            # Reason emoji
            reason_emoji = PositionNotificationManager._get_reason_emoji(closing_reason)

            # Calculate duration if possible
            duration_text = ""
            if position.opened_at:
                duration = datetime.utcnow() - position.opened_at
                hours = duration.total_seconds() / 3600
                duration_text = f"\n<b>Duration:</b> {hours:.1f} hours"

            # Format comprehensive message
            message = f"""
{status_emoji} <b>Position Closed</b>

{reason_emoji} <b>Reason:</b> {closing_reason}

<b>Symbol:</b> {position.symbol}
<b>Size:</b> {float(position.size)}
<b>Entry Price:</b> ${float(position.entry_price)}
<b>Closing Price:</b> ${closing_price}

{pnl_emoji} <b>P&L:</b> {pnl_text}{duration_text}

<i>Automated position closure</i>
            """.strip()

            return message

        except Exception as e:
            logger.error(f"Error formatting closure message for position {position.id}: {e}")
            return f"Position {position.symbol} closed: {closing_reason} (P&L: ${pnl:.4f})"

    @staticmethod
    def _get_reason_emoji(reason: str) -> str:
        """Get emoji for closure reason."""
        reason_lower = reason.lower()

        if 'take_profit' in reason_lower:
            return "🎯"
        elif 'stop_loss' in reason_lower:
            return "🛑"
        elif 'emergency' in reason_lower:
            return "🚨"
        elif 'market' in reason_lower:
            return "📊"
        elif 'entry' in reason_lower:
            return "🚪"
        else:
            return "📋"

    @staticmethod
    async def send_monitoring_alert(
        alert_type: str,
        message: str,
        admin_credentials: Dict[str, str]
    ) -> bool:
        """Send system monitoring alerts to administrators.

        Args:
            alert_type: Type of alert (ERROR, WARNING, INFO)
            message: Alert message
            admin_credentials: Admin Telegram credentials

        Returns:
            True if alert was sent successfully
        """
        try:
            telegram_token = admin_credentials.get('telegram_token')
            telegram_chat_id = admin_credentials.get('telegram_chat_id')

            if not telegram_token or not telegram_chat_id:
                logger.warning("No admin Telegram credentials found for monitoring alert")
                return False

            # Format alert message with type emoji
            alert_emoji = PositionNotificationManager._get_alert_emoji(alert_type)

            formatted_message = f"""
{alert_emoji} <b>System Alert</b>

<b>Type:</b> {alert_type}
<b>Time:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

{message}

<i>Automated monitoring alert</i>
            """.strip()

            success = await TelegramManager.send_notification(
                token=telegram_token,
                chat_id=telegram_chat_id,
                message=formatted_message
            )

            if success:
                logger.info(f"Monitoring alert sent: {alert_type}")
            else:
                logger.error(f"Failed to send monitoring alert: {alert_type}")

            return success

        except Exception as e:
            logger.error(f"Error sending monitoring alert: {e}")
            return False

    @staticmethod
    def _get_alert_emoji(alert_type: str) -> str:
        """Get emoji for alert type."""
        alert_lower = alert_type.lower()

        if alert_lower in ['error', 'critical', 'fatal']:
            return "🚨"
        elif alert_lower in ['warning', 'warn']:
            return "⚠️"
        elif alert_lower in ['info', 'information']:
            return "ℹ️"
        else:
            return "📢"

    @staticmethod
    async def send_batch_closure_notification(
        credentials: Dict[str, str],
        closed_positions: List[Dict[str, Any]]
    ) -> bool:
        """Send notification for multiple position closures.

        Args:
            credentials: User credentials
            closed_positions: List of closed position data

        Returns:
            True if notification was sent successfully
        """
        try:
            if not closed_positions:
                return False

            telegram_token = credentials.get('telegram_token')
            telegram_chat_id = credentials.get('telegram_chat_id')

            if not telegram_token or not telegram_chat_id:
                logger.warning(f"No Telegram credentials found for user {credentials.get('wallet_address')}")
                return False

            # Format batch closure message
            total_pnl = sum(float(pos.get('pnl', 0)) for pos in closed_positions)
            total_positions = len(closed_positions)

            # P&L summary
            if total_pnl >= 0:
                pnl_summary = f"💰 <b>+${total_pnl:.4f}</b>"
            else:
                pnl_summary = f"💸 <b style='color: red'>${total_pnl:.4f}</b>"

            # Create position details
            position_details = []
            for pos in closed_positions:
                pnl = float(pos.get('pnl', 0))
                pnl_text = f"+${pnl:.4f}" if pnl >= 0 else f"${pnl:.4f}"
                position_details.append(
                    f"• {pos.get('symbol', 'N/A')}: {pnl_text}"
                )

            message = f"""
📊 <b>Batch Position Closure</b>

<b>Positions Closed:</b> {total_positions}
{pnl_summary}

<b>Details:</b>
{chr(10).join(position_details)}

<i>Automated batch closure</i>
            """.strip()

            success = await TelegramManager.send_notification(
                token=telegram_token,
                chat_id=telegram_chat_id,
                message=message
            )

            if success:
                logger.info(f"Batch closure notification sent for {total_positions} positions")
            else:
                logger.error(f"Failed to send batch closure notification")

            return success

        except Exception as e:
            logger.error(f"Error sending batch closure notification: {e}")
            return False

    @staticmethod
    async def send_position_monitoring_summary(
        credentials: Dict[str, str],
        summary_data: Dict[str, Any]
    ) -> bool:
        """Send position monitoring summary notification.

        Args:
            credentials: User credentials
            summary_data: Monitoring summary data

        Returns:
            True if notification was sent successfully
        """
        try:
            telegram_token = credentials.get('telegram_token')
            telegram_chat_id = credentials.get('telegram_chat_id')

            if not telegram_token or not telegram_chat_id:
                logger.warning(f"No Telegram credentials found for user {credentials.get('wallet_address')}")
                return False

            # Extract summary data
            total_positions = summary_data.get('total_positions', 0)
            open_positions = summary_data.get('open_positions', 0)
            closed_positions = summary_data.get('closed_positions', 0)
            total_pnl = summary_data.get('total_pnl', 0)
            period_hours = summary_data.get('period_hours', 24)

            # Format summary message
            if total_pnl >= 0:
                pnl_text = f"💰 <b>+${total_pnl:.4f}</b>"
            else:
                pnl_text = f"💸 <b style='color: red'>${total_pnl:.4f}</b>"

            message = f"""
📈 <b>Position Monitoring Summary</b>

<b>Period:</b> Last {period_hours} hours
<b>Total Positions:</b> {total_positions}
<b>Open:</b> {open_positions}
<b>Closed:</b> {closed_positions}

{pnl_text}

<i>Automated monitoring summary</i>
            """.strip()

            success = await TelegramManager.send_notification(
                token=telegram_token,
                chat_id=telegram_chat_id,
                message=message
            )

            if success:
                logger.info(f"Monitoring summary sent for {total_positions} positions")
            else:
                logger.error("Failed to send monitoring summary")

            return success

        except Exception as e:
            logger.error(f"Error sending monitoring summary: {e}")
            return False

    @staticmethod
    async def send_error_notification(
        credentials: Dict[str, str],
        operation: str,
        error: str,
        position_id: Optional[int] = None
    ) -> bool:
        """Send error notification for position operations.

        Args:
            credentials: User credentials
            operation: Operation that failed
            error: Error message
            position_id: Optional position ID

        Returns:
            True if notification was sent successfully
        """
        try:
            telegram_token = credentials.get('telegram_token')
            telegram_chat_id = credentials.get('telegram_chat_id')

            if not telegram_token or not telegram_chat_id:
                logger.warning(f"No Telegram credentials found for user {credentials.get('wallet_address')}")
                return False

            # Format error message
            position_text = f" (Position ID: {position_id})" if position_id else ""

            message = f"""
⚠️ <b>Position Error</b>

<b>Operation:</b> {operation}{position_text}
<b>Error:</b> {error}
<b>Time:</b> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}

<i>Please check your position configuration</i>
            """.strip()

            success = await TelegramManager.send_notification(
                token=telegram_token,
                chat_id=telegram_chat_id,
                message=message
            )

            if success:
                logger.info(f"Error notification sent for operation: {operation}")
            else:
                logger.error(f"Failed to send error notification for operation: {operation}")

            return success

        except Exception as e:
            logger.error(f"Error sending error notification: {e}")
            return False

    @staticmethod
    async def send_system_status_notification(
        admin_credentials: Dict[str, str],
        status_data: Dict[str, Any]
    ) -> bool:
        """Send system status notification to administrators.

        Args:
            admin_credentials: Admin Telegram credentials
            status_data: System status information

        Returns:
            True if notification was sent successfully
        """
        try:
            telegram_token = admin_credentials.get('telegram_token')
            telegram_chat_id = admin_credentials.get('telegram_chat_id')

            if not telegram_token or not telegram_chat_id:
                logger.warning("No admin Telegram credentials found for system status")
                return False

            # Extract status data
            uptime = status_data.get('uptime_seconds', 0)
            positions_processed = status_data.get('positions_processed', 0)
            positions_closed = status_data.get('positions_closed', 0)
            errors_total = status_data.get('errors_total', 0)
            average_cycle_time = status_data.get('average_cycle_time', 0)

            # Format status message
            uptime_text = f"{uptime/3600:.1f}h" if uptime > 3600 else f"{uptime:.1f}s"

            message = f"""
🔧 <b>System Status Report</b>

<b>Uptime:</b> {uptime_text}
<b>Positions Processed:</b> {positions_processed}
<b>Positions Closed:</b> {positions_closed}
<b>Total Errors:</b> {errors_total}
<b>Avg Cycle Time:</b> {average_cycle_time:.2f}s

<i>Automated system status</i>
            """.strip()

            success = await TelegramManager.send_notification(
                token=telegram_token,
                chat_id=telegram_chat_id,
                message=message
            )

            if success:
                logger.info("System status notification sent")
            else:
                logger.error("Failed to send system status notification")

            return success

        except Exception as e:
            logger.error(f"Error sending system status notification: {e}")
            return False

    @staticmethod
    async def test_notification_system(credentials: Dict[str, str]) -> Dict[str, Any]:
        """Test the notification system for a user.

        Args:
            credentials: User credentials

        Returns:
            Test result with details
        """
        try:
            telegram_token = credentials.get('telegram_token')
            telegram_chat_id = credentials.get('telegram_chat_id')

            if not telegram_token or not telegram_chat_id:
                return {
                    'success': False,
                    'error': 'No Telegram credentials found',
                    'message': 'Please configure Telegram token and chat ID'
                }

            # Send test message
            test_message = """
🤖 <b>Notification Test</b>

Your position monitoring system is working correctly!

<i>Test message - you can disable these in settings</i>
            """.strip()

            success = await TelegramManager.send_notification(
                token=telegram_token,
                chat_id=telegram_chat_id,
                message=test_message
            )

            if success:
                return {
                    'success': True,
                    'message': 'Test notification sent successfully',
                    'timestamp': datetime.utcnow().isoformat()
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to send test notification',
                    'message': 'Check your Telegram credentials and bot permissions'
                }

        except Exception as e:
            logger.error(f"Error testing notification system: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Notification test failed'
            }