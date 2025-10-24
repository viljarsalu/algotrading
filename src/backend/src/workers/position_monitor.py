"""
Background Position Monitoring Service - Main Worker Implementation.

This module implements the core background worker that continuously monitors
all open positions and handles automated closure logic for TP/SL events.
"""

import asyncio
import logging
import signal
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import json

from fastapi import FastAPI
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload

from ..db.models import User, Position
from ..db.database import get_database_manager
from ..core.security import get_encryption_manager
from ..core.config import get_settings
from .dydx_order_monitor import DydxOrderMonitor
from .position_state_manager import PositionStateManager
from .position_closure_orchestrator import PositionClosureOrchestrator
from .notification_manager import PositionNotificationManager
from .monitoring_manager import MonitoringManager

logger = logging.getLogger(__name__)


@dataclass
class WorkerMetrics:
    """Metrics for monitoring worker performance."""
    cycles_completed: int = 0
    positions_processed: int = 0
    positions_closed: int = 0
    errors_total: int = 0
    last_cycle_time: float = 0.0
    last_cycle_timestamp: Optional[datetime] = None
    average_cycle_time: float = 0.0
    start_time: datetime = field(default_factory=datetime.utcnow)


@dataclass
class WorkerConfig:
    """Configuration for the position monitor worker."""
    monitoring_interval: int = 30  # seconds
    max_workers: int = 5
    batch_size: int = 10
    max_retries: int = 3
    retry_backoff: int = 60  # seconds
    health_check_interval: int = 300  # 5 minutes
    max_concurrent_positions: int = 20
    enable_notifications: bool = True
    enable_monitoring: bool = True


class PositionMonitorWorker:
    """Main background worker for position monitoring and automated closure."""

    def __init__(
        self,
        db_session: Session,
        config: Optional[WorkerConfig] = None
    ):
        """Initialize the position monitor worker.

        Args:
            db_session: Database session for queries
            config: Worker configuration (uses defaults if None)
        """
        self.db = db_session
        self.config = config or WorkerConfig()
        self.is_running = False
        self._shutdown_event = asyncio.Event()
        self._monitoring_task: Optional[asyncio.Task] = None
        self._health_check_task: Optional[asyncio.Task] = None

        # Initialize components
        self.order_monitor = DydxOrderMonitor()
        self.state_manager = PositionStateManager()
        self.closure_orchestrator = PositionClosureOrchestrator(db_session)
        self.notification_manager = PositionNotificationManager()
        self.monitoring_manager = MonitoringManager()

        # Worker state
        self.metrics = WorkerMetrics()
        self._last_error: Optional[str] = None
        self._consecutive_errors = 0

        # Signal handlers for graceful shutdown
        self._setup_signal_handlers()

        logger.info(f"PositionMonitorWorker initialized with interval: {self.config.monitoring_interval}s")

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        try:
            loop = asyncio.get_event_loop()

            def signal_handler():
                logger.info("Received shutdown signal, stopping worker...")
                self._shutdown_event.set()

            # Add signal handlers for common termination signals
            for sig in (signal.SIGTERM, signal.SIGINT):
                loop.add_signal_handler(sig, signal_handler)
        except (RuntimeError, ValueError):
            # No event loop or signal handler already set
            pass

    async def start_monitoring(self) -> None:
        """Start the background monitoring process."""
        if self.is_running:
            logger.warning("Worker is already running")
            return

        logger.info("Starting position monitoring worker...")
        self.is_running = True
        self._shutdown_event.clear()
        self.metrics = WorkerMetrics()  # Reset metrics

        try:
            # Start main monitoring loop
            self._monitoring_task = asyncio.create_task(self.monitoring_loop())

            # Start health check task if enabled
            if self.config.enable_monitoring:
                self._health_check_task = asyncio.create_task(self.health_check_loop())

            logger.info("Position monitoring worker started successfully")

        except Exception as e:
            logger.error(f"Failed to start monitoring worker: {e}")
            self.is_running = False
            raise

    async def stop_monitoring(self) -> None:
        """Gracefully stop the monitoring process."""
        if not self.is_running:
            logger.warning("Worker is not running")
            return

        logger.info("Stopping position monitoring worker...")
        self.is_running = False
        self._shutdown_event.set()

        # Cancel running tasks
        if self._monitoring_task and not self._monitoring_task.done():
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

        if self._health_check_task and not self._health_check_task.done():
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        logger.info("Position monitoring worker stopped")

    async def monitoring_loop(self) -> None:
        """Main monitoring loop with error handling and recovery."""
        logger.info("Starting monitoring loop...")

        while self.is_running and not self._shutdown_event.is_set():
            try:
                cycle_start_time = time.time()

                # Process one monitoring cycle
                await self._process_monitoring_cycle()

                # Update metrics
                cycle_time = time.time() - cycle_start_time
                self.metrics.last_cycle_time = cycle_time
                self.metrics.last_cycle_timestamp = datetime.utcnow()
                self.metrics.cycles_completed += 1

                # Update average cycle time
                total_cycles = self.metrics.cycles_completed
                self.metrics.average_cycle_time = (
                    (self.metrics.average_cycle_time * (total_cycles - 1)) + cycle_time
                ) / total_cycles

                # Reset error counters on successful cycle
                self._consecutive_errors = 0
                self._last_error = None

                # Wait for next cycle or shutdown
                if self.is_running and not self._shutdown_event.is_set():
                    logger.debug(f"Monitoring cycle completed in {cycle_time:.2f}s, waiting {self.config.monitoring_interval}s")
                    await asyncio.wait_for(
                        self._shutdown_event.wait(),
                        timeout=self.config.monitoring_interval
                    )

            except asyncio.TimeoutError:
                # Normal timeout, continue to next cycle
                continue
            except asyncio.CancelledError:
                logger.info("Monitoring loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in monitoring cycle: {e}")
                self._handle_monitoring_error(e)

                # Continue running even after errors
                if self.is_running and not self._shutdown_event.is_set():
                    logger.info(f"Continuing monitoring after error, waiting {self.config.monitoring_interval}s")
                    await asyncio.wait_for(
                        self._shutdown_event.wait(),
                        timeout=self.config.monitoring_interval
                    )

        logger.info("Monitoring loop stopped")

    async def _process_monitoring_cycle(self) -> None:
        """Process one complete monitoring cycle."""
        try:
            # Step 1: Get all open positions
            positions = await self._get_open_positions()
            logger.debug(f"Found {len(positions)} open positions to monitor")

            if not positions:
                return

            # Step 2: Group positions by user for efficient processing
            positions_by_user = self._group_positions_by_user(positions)

            # Step 3: Process positions in batches
            for user_address, user_positions in positions_by_user.items():
                try:
                    await self._process_user_positions(user_address, user_positions)
                except Exception as e:
                    logger.error(f"Error processing positions for user {user_address}: {e}")
                    self.metrics.errors_total += 1

        except Exception as e:
            logger.error(f"Failed to process monitoring cycle: {e}")
            raise

    async def _get_open_positions(self) -> List[Position]:
        """Query database for all open positions across users."""
        try:
            # Query for open positions with user data loaded
            statement = (
                select(Position)
                .where(Position.status == "open")
                .options(selectinload(Position.user))
            )

            result = self.db.exec(statement)
            positions = result.all()

            logger.debug(f"Retrieved {len(positions)} open positions from database")
            return positions

        except Exception as e:
            logger.error(f"Failed to query open positions: {e}")
            raise

    def _group_positions_by_user(self, positions: List[Position]) -> Dict[str, List[Position]]:
        """Group positions by user address for efficient processing."""
        positions_by_user = {}

        for position in positions:
            user_address = position.user_address
            if user_address not in positions_by_user:
                positions_by_user[user_address] = []
            positions_by_user[user_address].append(position)

        logger.debug(f"Grouped positions into {len(positions_by_user)} user batches")
        return positions_by_user

    async def _process_user_positions(self, user_address: str, positions: List[Position]) -> None:
        """Process all positions for a specific user."""
        try:
            # Get user credentials
            user = await self._get_user_with_credentials(user_address)
            if not user:
                logger.warning(f"User {user_address} not found or missing credentials")
                return

            # Decrypt credentials
            credentials = await self._decrypt_user_credentials(user)
            if not credentials:
                logger.warning(f"Failed to decrypt credentials for user {user_address}")
                return

            # Process positions in batches
            for i in range(0, len(positions), self.config.batch_size):
                batch = positions[i:i + self.config.batch_size]

                try:
                    await self._process_position_batch(batch, credentials)
                except Exception as e:
                    logger.error(f"Error processing position batch for user {user_address}: {e}")
                    self.metrics.errors_total += 1

        except Exception as e:
            logger.error(f"Failed to process user positions for {user_address}: {e}")
            raise

    async def _get_user_with_credentials(self, user_address: str) -> Optional[User]:
        """Get user with credentials from database."""
        try:
            statement = select(User).where(User.wallet_address == user_address)
            user = self.db.exec(statement).first()
            return user
        except Exception as e:
            logger.error(f"Failed to get user {user_address}: {e}")
            return None

    async def _decrypt_user_credentials(self, user: User) -> Optional[Dict[str, str]]:
        """Decrypt user credentials for dYdX and Telegram access."""
        try:
            encryption_manager = get_encryption_manager()

            # Decrypt dYdX mnemonic
            dydx_mnemonic = None
            if user.encrypted_dydx_mnemonic:
                dydx_mnemonic = encryption_manager.decrypt(user.encrypted_dydx_mnemonic)

            # Decrypt Telegram credentials
            telegram_token = None
            telegram_chat_id = None
            if user.encrypted_telegram_token and user.encrypted_telegram_chat_id:
                telegram_token = encryption_manager.decrypt(user.encrypted_telegram_token)
                telegram_chat_id = encryption_manager.decrypt(user.encrypted_telegram_chat_id)

            if not dydx_mnemonic:
                logger.warning(f"No dYdX credentials found for user {user.wallet_address}")
                return None

            return {
                'dydx_mnemonic': dydx_mnemonic,
                'telegram_token': telegram_token,
                'telegram_chat_id': telegram_chat_id,
                'wallet_address': user.wallet_address,
            }

        except Exception as e:
            logger.error(f"Failed to decrypt credentials for user {user.wallet_address}: {e}")
            return None

    async def _process_position_batch(self, positions: List[Position], credentials: Dict[str, str]) -> None:
        """Process a batch of positions for closure evaluation."""
        try:
            # Step 1: Check dYdX order status for all positions
            order_checks = await self.order_monitor.check_order_status_batch(
                positions=positions,
                credentials=credentials
            )

            # Step 2: Evaluate position states
            positions_to_close = []
            for position in positions:
                position_key = f"{position.id}"

                if position_key in order_checks:
                    order_data = order_checks[position_key]

                    # Evaluate if position should be closed
                    should_close, reason = await self.state_manager.evaluate_position_state(
                        position=position,
                        dydx_orders=order_data
                    )

                    if should_close:
                        positions_to_close.append({
                            'position': position,
                            'reason': reason,
                            'order_data': order_data
                        })

            # Step 3: Close positions that need closing
            for close_data in positions_to_close:
                try:
                    await self._close_position_automatically(close_data, credentials)
                except Exception as e:
                    logger.error(f"Failed to close position {close_data['position'].id}: {e}")
                    self.metrics.errors_total += 1

        except Exception as e:
            logger.error(f"Failed to process position batch: {e}")
            raise

    async def _close_position_automatically(self, close_data: Dict[str, Any], credentials: Dict[str, str]) -> None:
        """Close a position automatically with notifications."""
        position = close_data['position']
        reason = close_data['reason']
        order_data = close_data['order_data']

        try:
            logger.info(f"Automatically closing position {position.id} for reason: {reason}")

            # Close the position
            close_result = await self.closure_orchestrator.close_position_automatically(
                position=position,
                credentials=credentials,
                closing_reason=reason,
                closing_data=order_data
            )

            if close_result['success']:
                # Update metrics
                self.metrics.positions_closed += 1

                # Send notification if enabled
                if self.config.enable_notifications and credentials.get('telegram_token'):
                    await self._send_closure_notification(position, credentials, close_result)

                logger.info(f"Position {position.id} closed successfully: {reason}")
            else:
                logger.error(f"Failed to close position {position.id}: {close_result.get('error')}")
                self.metrics.errors_total += 1

        except Exception as e:
            logger.error(f"Error in automatic position closure for {position.id}: {e}")
            self.metrics.errors_total += 1
            raise

    async def _send_closure_notification(self, position: Position, credentials: Dict[str, str], close_result: Dict[str, Any]) -> None:
        """Send position closure notification to user."""
        try:
            await self.notification_manager.send_position_closure_notification(
                credentials=credentials,
                position=position,
                closing_data=close_result
            )
        except Exception as e:
            logger.error(f"Failed to send closure notification for position {position.id}: {e}")

    def _handle_monitoring_error(self, error: Exception) -> None:
        """Handle errors in the monitoring process."""
        self._last_error = str(error)
        self._consecutive_errors += 1
        self.metrics.errors_total += 1

        logger.error(f"Monitoring error #{self._consecutive_errors}: {error}")

        # Log critical errors
        if self._consecutive_errors >= 5:
            logger.critical(f"Multiple consecutive monitoring errors ({self._consecutive_errors}). Last error: {error}")

    async def health_check_loop(self) -> None:
        """Periodic health check and metrics reporting."""
        while self.is_running and not self._shutdown_event.is_set():
            try:
                # Wait for health check interval
                await asyncio.sleep(self.config.health_check_interval)

                # Perform health checks
                await self._perform_health_checks()

            except asyncio.CancelledError:
                logger.info("Health check loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")

    async def _perform_health_checks(self) -> None:
        """Perform comprehensive health checks."""
        try:
            # Check if monitoring is responsive
            time_since_last_cycle = 0.0
            if self.metrics.last_cycle_timestamp:
                time_since_last_cycle = (datetime.utcnow() - self.metrics.last_cycle_timestamp).total_seconds()

            # Log health status
            health_data = {
                'is_running': self.is_running,
                'cycles_completed': self.metrics.cycles_completed,
                'positions_processed': self.metrics.positions_processed,
                'positions_closed': self.metrics.positions_closed,
                'errors_total': self.metrics.errors_total,
                'last_cycle_seconds_ago': time_since_last_cycle,
                'average_cycle_time': self.metrics.average_cycle_time,
                'uptime_seconds': (datetime.utcnow() - self.metrics.start_time).total_seconds(),
            }

            logger.info(f"Worker health check: {json.dumps(health_data, indent=2)}")

            # Check for concerning patterns
            if time_since_last_cycle > self.config.monitoring_interval * 3:
                logger.warning(f"Worker may be unresponsive - last cycle was {time_since_last_cycle:.0f}s ago")

            if self._consecutive_errors > 0:
                logger.warning(f"Worker has {self._consecutive_errors} consecutive errors")

        except Exception as e:
            logger.error(f"Health check failed: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get current worker status and metrics."""
        return {
            'is_running': self.is_running,
            'metrics': {
                'cycles_completed': self.metrics.cycles_completed,
                'positions_processed': self.metrics.positions_processed,
                'positions_closed': self.metrics.positions_closed,
                'errors_total': self.metrics.errors_total,
                'last_cycle_time': self.metrics.last_cycle_time,
                'last_cycle_timestamp': self.metrics.last_cycle_timestamp.isoformat() if self.metrics.last_cycle_timestamp else None,
                'average_cycle_time': self.metrics.average_cycle_time,
                'uptime_seconds': (datetime.utcnow() - self.metrics.start_time).total_seconds(),
            },
            'config': {
                'monitoring_interval': self.config.monitoring_interval,
                'max_workers': self.config.max_workers,
                'batch_size': self.config.batch_size,
                'max_retries': self.config.max_retries,
            },
            'last_error': self._last_error,
            'consecutive_errors': self._consecutive_errors,
        }


# Global worker instance
_worker_instance: Optional[PositionMonitorWorker] = None


async def get_position_monitor_worker() -> PositionMonitorWorker:
    """Get or create the global worker instance."""
    global _worker_instance

    if _worker_instance is None:
        # Get database session
        db_manager = get_database_manager()
        db_session = next(db_manager.get_session())

        # Create worker instance
        _worker_instance = PositionMonitorWorker(db_session)

    return _worker_instance


async def initialize_worker(app: FastAPI, config: Optional[Dict[str, Any]] = None) -> PositionMonitorWorker:
    """Initialize and start worker with application."""
    worker = await get_position_monitor_worker()

    # Apply configuration if provided
    if config:
        worker_config = WorkerConfig(**{k: v for k, v in config.items() if hasattr(WorkerConfig, k)})
        worker.config = worker_config

    # Start the worker
    await worker.start_monitoring()

    return worker


async def graceful_shutdown(app: FastAPI) -> None:
    """Handle graceful shutdown of worker processes."""
    global _worker_instance

    if _worker_instance:
        await _worker_instance.stop_monitoring()
        logger.info("Worker shutdown completed")


async def health_check() -> Dict[str, Any]:
    """Monitor worker health and performance metrics."""
    global _worker_instance

    if _worker_instance:
        return _worker_instance.get_status()
    else:
        return {
            'is_running': False,
            'error': 'Worker not initialized'
        }