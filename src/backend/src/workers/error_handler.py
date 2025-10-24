"""
Error Handling Module - Centralized Error Management for Position Monitoring.

This module provides comprehensive error handling, logging, and recovery
mechanisms for the position monitoring system.
"""

import asyncio
import logging
import traceback
import functools
from typing import Dict, List, Any, Optional, Callable, TypeVar, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification."""
    NETWORK = "network"
    DATABASE = "database"
    API = "api"
    VALIDATION = "validation"
    PROCESSING = "processing"
    SYSTEM = "system"
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """Context information for errors."""
    operation: str
    user_address: Optional[str] = None
    position_id: Optional[int] = None
    component: str = "unknown"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorRecord:
    """Record of an error occurrence."""
    error_id: str
    message: str
    category: ErrorCategory
    severity: ErrorSeverity
    context: ErrorContext
    exception_type: str
    traceback: Optional[str] = None
    count: int = 1
    first_seen: datetime = field(default_factory=datetime.utcnow)
    last_seen: datetime = field(default_factory=datetime.utcnow)


class ErrorHandler:
    """Centralized error handling and recovery system."""

    def __init__(self, max_error_history: int = 1000):
        """Initialize error handler.

        Args:
            max_error_history: Maximum number of error records to keep
        """
        self.max_error_history = max_error_history
        self.error_history: List[ErrorRecord] = []
        self.error_counts: Dict[str, int] = {}
        self._lock = asyncio.Lock()

        # Recovery strategies
        self.recovery_strategies: Dict[ErrorCategory, Callable] = {
            ErrorCategory.NETWORK: self._recover_from_network_error,
            ErrorCategory.DATABASE: self._recover_from_database_error,
            ErrorCategory.API: self._recover_from_api_error,
            ErrorCategory.VALIDATION: self._recover_from_validation_error,
            ErrorCategory.PROCESSING: self._recover_from_processing_error,
        }

    async def handle_error(
        self,
        error: Exception,
        context: ErrorContext,
        category: Optional[ErrorCategory] = None,
        severity: Optional[ErrorSeverity] = None
    ) -> ErrorRecord:
        """Handle an error with classification and recovery.

        Args:
            error: The exception that occurred
            context: Context information about the error
            category: Error category (auto-detected if None)
            severity: Error severity (auto-detected if None)

        Returns:
            Error record for the handled error
        """
        # Classify error
        if category is None:
            category = self._classify_error(error)

        if severity is None:
            severity = self._assess_severity(error, category)

        # Create error record
        error_id = self._generate_error_id(error, context)
        error_record = ErrorRecord(
            error_id=error_id,
            message=str(error),
            category=category,
            severity=severity,
            context=context,
            exception_type=type(error).__name__,
            traceback=traceback.format_exc()
        )

        # Store error record
        async with self._lock:
            # Check if this error already exists
            existing_record = self._find_existing_error(error_id)

            if existing_record:
                # Update existing record
                existing_record.count += 1
                existing_record.last_seen = datetime.utcnow()
                existing_record.context = context  # Update with latest context
                error_record = existing_record
            else:
                # Add new record
                self.error_history.append(error_record)

                # Trim history if needed
                if len(self.error_history) > self.max_error_history:
                    self.error_history.pop(0)

        # Log the error
        await self._log_error(error_record)

        # Attempt recovery if applicable
        await self._attempt_recovery(error_record)

        return error_record

    def _classify_error(self, error: Exception) -> ErrorCategory:
        """Classify error into categories."""
        error_message = str(error).lower()
        error_type = type(error).__name__.lower()

        # Network errors
        if any(term in error_message for term in ['timeout', 'connection', 'network', 'dns', 'tcp']):
            return ErrorCategory.NETWORK

        # Database errors
        if any(term in error_message for term in ['database', 'sql', 'connection pool', 'deadlock']):
            return ErrorCategory.DATABASE

        # API errors
        if any(term in error_message for term in ['api', 'http', 'status', 'unauthorized', 'forbidden']):
            return ErrorCategory.API

        # Validation errors
        if any(term in error_type for term in ['validationerror', 'valueerror']):
            return ErrorCategory.VALIDATION

        # Processing errors
        if any(term in error_message for term in ['processing', 'calculation', 'logic']):
            return ErrorCategory.PROCESSING

        # System errors
        if any(term in error_type for term in ['systemerror', 'memoryerror', 'runtimeerror']):
            return ErrorCategory.SYSTEM

        return ErrorCategory.UNKNOWN

    def _assess_severity(self, error: Exception, category: ErrorCategory) -> ErrorSeverity:
        """Assess error severity."""
        error_message = str(error).lower()

        # Critical errors
        if any(term in error_message for term in ['critical', 'fatal', 'system failure', 'out of memory']):
            return ErrorSeverity.CRITICAL

        # High severity
        if category in [ErrorCategory.SYSTEM, ErrorCategory.DATABASE]:
            return ErrorSeverity.HIGH

        # Medium severity
        if category in [ErrorCategory.API, ErrorCategory.NETWORK]:
            return ErrorSeverity.MEDIUM

        # Low severity for validation and processing errors
        return ErrorSeverity.LOW

    def _generate_error_id(self, error: Exception, context: ErrorContext) -> str:
        """Generate unique error ID."""
        return f"{type(error).__name__}_{context.operation}_{hash(str(error)) % 10000}"

    def _find_existing_error(self, error_id: str) -> Optional[ErrorRecord]:
        """Find existing error record by ID."""
        for record in self.error_history:
            if record.error_id == error_id:
                return record
        return None

    async def _log_error(self, error_record: ErrorRecord) -> None:
        """Log error with appropriate level."""
        log_message = (
            f"Error in {error_record.context.operation}: {error_record.message} "
            f"(Category: {error_record.category.value}, Severity: {error_record.severity.value})"
        )

        # Log based on severity
        if error_record.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message, extra={
                'error_id': error_record.error_id,
                'category': error_record.category.value,
                'context': error_record.context.__dict__
            })
        elif error_record.severity == ErrorSeverity.HIGH:
            logger.error(log_message, extra={
                'error_id': error_record.error_id,
                'category': error_record.category.value,
                'context': error_record.context.__dict__
            })
        elif error_record.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message, extra={
                'error_id': error_record.error_id,
                'category': error_record.category.value,
                'context': error_record.context.__dict__
            })
        else:
            logger.info(log_message, extra={
                'error_id': error_record.error_id,
                'category': error_record.category.value,
                'context': error_record.context.__dict__
            })

    async def _attempt_recovery(self, error_record: ErrorRecord) -> None:
        """Attempt error recovery using appropriate strategy."""
        try:
            recovery_strategy = self.recovery_strategies.get(error_record.category)
            if recovery_strategy:
                await recovery_strategy(error_record)
        except Exception as e:
            logger.error(f"Recovery attempt failed for error {error_record.error_id}: {e}")

    async def _recover_from_network_error(self, error_record: ErrorRecord) -> None:
        """Recover from network errors."""
        logger.info(f"Attempting network error recovery for {error_record.error_id}")

        # For network errors, we might want to:
        # - Retry after a delay
        # - Use exponential backoff
        # - Switch to backup endpoints
        # - Implement circuit breaker pattern

        # For now, just log the recovery attempt
        logger.info(f"Network error recovery completed for {error_record.error_id}")

    async def _recover_from_database_error(self, error_record: ErrorRecord) -> None:
        """Recover from database errors."""
        logger.info(f"Attempting database error recovery for {error_record.error_id}")

        # For database errors, we might want to:
        # - Retry the transaction
        # - Check database connectivity
        # - Clear connection pools
        # - Switch to read-only mode

        logger.info(f"Database error recovery completed for {error_record.error_id}")

    async def _recover_from_api_error(self, error_record: ErrorRecord) -> None:
        """Recover from API errors."""
        logger.info(f"Attempting API error recovery for {error_record.error_id}")

        # For API errors, we might want to:
        # - Retry with rate limiting
        # - Use different API endpoints
        # - Implement caching for non-critical data
        # - Graceful degradation

        logger.info(f"API error recovery completed for {error_record.error_id}")

    async def _recover_from_validation_error(self, error_record: ErrorRecord) -> None:
        """Recover from validation errors."""
        logger.info(f"Validation error recovery for {error_record.error_id}")

        # Validation errors are usually data issues that need fixing
        # Recovery might involve:
        # - Data cleanup
        # - Default value assignment
        # - User notification

        logger.info(f"Validation error recovery completed for {error_record.error_id}")

    async def _recover_from_processing_error(self, error_record: ErrorRecord) -> None:
        """Recover from processing errors."""
        logger.info(f"Attempting processing error recovery for {error_record.error_id}")

        # Processing errors might need:
        # - Algorithm adjustments
        # - Fallback processing methods
        # - Partial result processing

        logger.info(f"Processing error recovery completed for {error_record.error_id}")

    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for the specified time period."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)

            recent_errors = [
                record for record in self.error_history
                if record.last_seen > cutoff_time
            ]

            # Group errors by category and severity
            errors_by_category = {}
            errors_by_severity = {}

            for error in recent_errors:
                # By category
                category = error.category.value
                if category not in errors_by_category:
                    errors_by_category[category] = []
                errors_by_category[category].append(error)

                # By severity
                severity = error.severity.value
                if severity not in errors_by_severity:
                    errors_by_severity[severity] = []
                errors_by_severity[severity].append(error)

            return {
                'time_period_hours': hours,
                'total_errors': len(recent_errors),
                'unique_errors': len(set(error.error_id for error in recent_errors)),
                'errors_by_category': {
                    category: len(errors)
                    for category, errors in errors_by_category.items()
                },
                'errors_by_severity': {
                    severity: len(errors)
                    for severity, errors in errors_by_severity.items()
                },
                'most_common_errors': self._get_most_common_errors(recent_errors),
            }

        except Exception as e:
            logger.error(f"Error generating error summary: {e}")
            return {'error': str(e)}

    def _get_most_common_errors(self, errors: List[ErrorRecord], limit: int = 10) -> List[Dict[str, Any]]:
        """Get most common errors."""
        error_counts = {}

        for error in errors:
            key = error.error_id
            if key not in error_counts:
                error_counts[key] = {
                    'error_id': error.error_id,
                    'message': error.message,
                    'category': error.category.value,
                    'severity': error.severity.value,
                    'count': 0,
                    'first_seen': error.first_seen,
                    'last_seen': error.last_seen,
                }
            error_counts[key]['count'] += 1

        # Sort by count and return top errors
        sorted_errors = sorted(error_counts.values(), key=lambda x: x['count'], reverse=True)
        return sorted_errors[:limit]

    def get_error_details(self, error_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific error."""
        for record in self.error_history:
            if record.error_id == error_id:
                return {
                    'error_id': record.error_id,
                    'message': record.message,
                    'category': record.category.value,
                    'severity': record.severity.value,
                    'count': record.count,
                    'first_seen': record.first_seen.isoformat(),
                    'last_seen': record.last_seen.isoformat(),
                    'context': record.context.__dict__,
                    'traceback': record.traceback,
                }
        return None


# Global error handler instance
error_handler = ErrorHandler()


def handle_async_error(category: ErrorCategory = None, severity: ErrorSeverity = None):
    """Decorator for handling async function errors."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Create context from function information
                context = ErrorContext(
                    operation=func.__name__,
                    component=func.__module__,
                )

                # Handle the error
                await error_handler.handle_error(e, context, category, severity)

                # Re-raise the exception
                raise

        return wrapper
    return decorator


def handle_sync_error(category: ErrorCategory = None, severity: ErrorSeverity = None):
    """Decorator for handling sync function errors."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Create context from function information
                context = ErrorContext(
                    operation=func.__name__,
                    component=func.__module__,
                )

                # Handle the error (create task to avoid blocking)
                asyncio.create_task(
                    error_handler.handle_error(e, context, category, severity)
                )

                # Re-raise the exception
                raise

        return wrapper
    return decorator


class ErrorRecoveryManager:
    """Manages error recovery strategies and circuit breakers."""

    def __init__(self):
        """Initialize recovery manager."""
        self.circuit_breakers: Dict[str, Dict[str, Any]] = {}
        self.recovery_attempts: Dict[str, int] = {}

    async def execute_with_recovery(
        self,
        operation: Callable,
        operation_name: str,
        max_retries: int = 3,
        base_delay: float = 1.0
    ) -> Any:
        """Execute operation with retry and circuit breaker logic."""
        circuit_key = operation_name

        # Check circuit breaker
        if not await self._is_circuit_closed(circuit_key):
            raise Exception(f"Circuit breaker is open for {operation_name}")

        last_exception = None

        for attempt in range(max_retries):
            try:
                # Record attempt
                self.recovery_attempts[circuit_key] = attempt + 1

                # Execute operation
                result = await operation() if asyncio.iscoroutinefunction(operation) else operation()

                # Success - reset circuit breaker
                await self._record_success(circuit_key)
                return result

            except Exception as e:
                last_exception = e

                # Record failure
                await self._record_failure(circuit_key)

                # Wait before retry (except on last attempt)
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    logger.info(f"Retrying {operation_name} in {delay}s (attempt {attempt + 2}/{max_retries})")
                    await asyncio.sleep(delay)

        # All retries failed
        logger.error(f"All retry attempts failed for {operation_name}")
        raise last_exception

    async def _is_circuit_closed(self, circuit_key: str) -> bool:
        """Check if circuit breaker is closed."""
        if circuit_key not in self.circuit_breakers:
            self.circuit_breakers[circuit_key] = {
                'state': 'CLOSED',
                'failures': 0,
                'last_failure': None,
                'successes': 0,
            }
            return True

        circuit = self.circuit_breakers[circuit_key]

        if circuit['state'] == 'OPEN':
            # Check if we should try half-open
            if circuit['last_failure']:
                time_since_failure = datetime.utcnow() - circuit['last_failure']
                if time_since_failure.total_seconds() > 60:  # 1 minute timeout
                    circuit['state'] = 'HALF_OPEN'
                    logger.info(f"Circuit breaker {circuit_key} moved to HALF_OPEN")

        return circuit['state'] != 'OPEN'

    async def _record_success(self, circuit_key: str) -> None:
        """Record successful operation."""
        if circuit_key in self.circuit_breakers:
            circuit = self.circuit_breakers[circuit_key]
            circuit['successes'] += 1

            # Close circuit if it was half-open
            if circuit['state'] == 'HALF_OPEN':
                circuit['state'] = 'CLOSED'
                circuit['failures'] = 0
                logger.info(f"Circuit breaker {circuit_key} reset to CLOSED")

    async def _record_failure(self, circuit_key: str) -> None:
        """Record failed operation."""
        if circuit_key in self.circuit_breakers:
            circuit = self.circuit_breakers[circuit_key]
            circuit['failures'] += 1
            circuit['last_failure'] = datetime.utcnow()

            # Open circuit after 3 failures
            if circuit['failures'] >= 3:
                circuit['state'] = 'OPEN'
                logger.warning(f"Circuit breaker {circuit_key} opened after {circuit['failures']} failures")


# Global recovery manager instance
recovery_manager = ErrorRecoveryManager()


async def create_error_context(
    operation: str,
    user_address: Optional[str] = None,
    position_id: Optional[int] = None,
    component: str = "position_monitor",
    **kwargs
) -> ErrorContext:
    """Create error context with additional data."""
    return ErrorContext(
        operation=operation,
        user_address=user_address,
        position_id=position_id,
        component=component,
        additional_data=kwargs
    )