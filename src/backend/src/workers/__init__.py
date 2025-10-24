"""
Position Monitoring Workers Package - Background Position Monitoring System.

This package provides a comprehensive background monitoring system for dYdX
trading positions with automated closure capabilities and real-time notifications.
"""

from .position_monitor import (
    PositionMonitorWorker,
    WorkerConfig,
    WorkerMetrics,
    get_position_monitor_worker,
    initialize_worker,
    graceful_shutdown,
    health_check
)

from .dydx_order_monitor import DydxOrderMonitor
from .position_state_manager import PositionStateManager
from .position_closure_orchestrator import PositionClosureOrchestrator
from .batch_processor import BatchProcessor
from .notification_manager import PositionNotificationManager
from .monitoring_manager import MonitoringManager, SystemMetrics, AlertRule, MetricsCollector
from .error_handler import (
    ErrorHandler,
    ErrorRecoveryManager,
    ErrorContext,
    ErrorRecord,
    ErrorSeverity,
    ErrorCategory,
    handle_async_error,
    handle_sync_error,
    create_error_context,
    error_handler,
    recovery_manager
)

__version__ = "1.0.0"
__all__ = [
    # Main worker
    "PositionMonitorWorker",
    "WorkerConfig",
    "WorkerMetrics",

    # Worker management
    "get_position_monitor_worker",
    "initialize_worker",
    "graceful_shutdown",
    "health_check",

    # Components
    "DydxOrderMonitor",
    "PositionStateManager",
    "PositionClosureOrchestrator",
    "BatchProcessor",
    "PositionNotificationManager",
    "MonitoringManager",

    # Monitoring types
    "SystemMetrics",
    "AlertRule",
    "MetricsCollector",

    # Error handling
    "ErrorHandler",
    "ErrorRecoveryManager",
    "ErrorContext",
    "ErrorRecord",
    "ErrorSeverity",
    "ErrorCategory",
    "handle_async_error",
    "handle_sync_error",
    "create_error_context",
    "error_handler",
    "recovery_manager",
]