"""Resilience Module - Error Handling, Rate Limiting, and Circuit Breaker.

This module provides comprehensive error handling, rate limiting detection,
circuit breaker pattern, and graceful degradation for production resilience.
"""

import logging
import asyncio
from typing import Dict, Any, Optional, Callable, TypeVar, Awaitable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import time

logger = logging.getLogger(__name__)

T = TypeVar("T")


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
    RATE_LIMIT = "rate_limit"
    VALIDATION = "validation"
    PROCESSING = "processing"
    SYSTEM = "system"
    UNKNOWN = "unknown"


class CircuitBreakerState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class ErrorRecord:
    """Record of an error occurrence."""
    error_id: str
    message: str
    category: ErrorCategory
    severity: ErrorSeverity
    exception_type: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    count: int = 1
    last_seen: datetime = field(default_factory=datetime.utcnow)
    http_status: Optional[int] = None
    user_message: Optional[str] = None


class RateLimitDetector:
    """Detect and handle rate limiting."""

    def __init__(self, window_seconds: int = 60, max_requests: int = 100):
        """Initialize rate limit detector.

        Args:
            window_seconds: Time window in seconds
            max_requests: Maximum requests in window
        """
        self.window_seconds = window_seconds
        self.max_requests = max_requests
        self.request_times: Dict[str, list] = {}
        self.rate_limited_until: Dict[str, datetime] = {}

    def is_rate_limited(self, key: str) -> bool:
        """Check if key is rate limited.

        Args:
            key: Rate limit key (e.g., user_id, endpoint)

        Returns:
            True if rate limited, False otherwise
        """
        # Check if in rate limited period
        if key in self.rate_limited_until:
            if datetime.utcnow() < self.rate_limited_until[key]:
                return True
            else:
                del self.rate_limited_until[key]

        return False

    def record_request(self, key: str) -> bool:
        """Record a request and check rate limit.

        Args:
            key: Rate limit key

        Returns:
            True if request allowed, False if rate limited
        """
        now = datetime.utcnow()
        cutoff = now - timedelta(seconds=self.window_seconds)

        # Initialize or clean request times
        if key not in self.request_times:
            self.request_times[key] = []

        # Remove old requests outside window
        self.request_times[key] = [
            t for t in self.request_times[key] if t > cutoff
        ]

        # Check if rate limited
        if len(self.request_times[key]) >= self.max_requests:
            # Set rate limited until next window
            self.rate_limited_until[key] = now + timedelta(
                seconds=self.window_seconds
            )
            logger.warning(f"Rate limit exceeded for {key}")
            return False

        # Record request
        self.request_times[key].append(now)
        return True

    def get_retry_after(self, key: str) -> Optional[int]:
        """Get seconds to wait before retry.

        Args:
            key: Rate limit key

        Returns:
            Seconds to wait, or None if not rate limited
        """
        if key not in self.rate_limited_until:
            return None

        wait_until = self.rate_limited_until[key]
        wait_seconds = (wait_until - datetime.utcnow()).total_seconds()
        return max(0, int(wait_seconds))


class CircuitBreaker:
    """Circuit breaker pattern for failing endpoints."""

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception,
    ):
        """Initialize circuit breaker.

        Args:
            name: Circuit breaker name
            failure_threshold: Failures before opening
            recovery_timeout: Seconds before attempting recovery
            expected_exception: Exception type to catch
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.success_count = 0

    def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute function with circuit breaker protection.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            Exception: If circuit is open or function fails
        """
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
                logger.info(f"Circuit breaker {self.name} entering HALF_OPEN")
            else:
                raise Exception(
                    f"Circuit breaker {self.name} is OPEN. "
                    f"Service unavailable."
                )

        try:
            result = func(*args, **kwargs)

            if self.state == CircuitBreakerState.HALF_OPEN:
                self._on_success()

            return result

        except self.expected_exception as e:
            self._on_failure()
            raise

    async def call_async(
        self, func: Callable[..., Awaitable[T]], *args, **kwargs
    ) -> T:
        """Execute async function with circuit breaker protection.

        Args:
            func: Async function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            Exception: If circuit is open or function fails
        """
        if self.state == CircuitBreakerState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitBreakerState.HALF_OPEN
                logger.info(f"Circuit breaker {self.name} entering HALF_OPEN")
            else:
                raise Exception(
                    f"Circuit breaker {self.name} is OPEN. "
                    f"Service unavailable."
                )

        try:
            result = await func(*args, **kwargs)

            if self.state == CircuitBreakerState.HALF_OPEN:
                self._on_success()

            return result

        except self.expected_exception as e:
            self._on_failure()
            raise

    def _on_success(self) -> None:
        """Handle successful call."""
        self.failure_count = 0
        self.success_count += 1

        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.CLOSED
            self.success_count = 0
            logger.info(f"Circuit breaker {self.name} CLOSED (recovered)")

    def _on_failure(self) -> None:
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.utcnow()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            logger.error(
                f"Circuit breaker {self.name} OPEN "
                f"({self.failure_count} failures)"
            )

    def _should_attempt_reset(self) -> bool:
        """Check if should attempt recovery.

        Returns:
            True if recovery timeout has passed
        """
        if not self.last_failure_time:
            return True

        elapsed = (datetime.utcnow() - self.last_failure_time).total_seconds()
        return elapsed >= self.recovery_timeout

    def get_status(self) -> Dict[str, Any]:
        """Get circuit breaker status.

        Returns:
            Status dictionary
        """
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "last_failure_time": (
                self.last_failure_time.isoformat()
                if self.last_failure_time
                else None
            ),
        }


class ErrorHandler:
    """Centralized error handling and recovery."""

    def __init__(self, max_error_history: int = 1000):
        """Initialize error handler.

        Args:
            max_error_history: Maximum error records to keep
        """
        self.max_error_history = max_error_history
        self.error_history: list = []
        self.error_counts: Dict[str, int] = {}
        self.rate_limiter = RateLimitDetector()
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._lock = asyncio.Lock()

    def classify_error(self, error: Exception) -> ErrorCategory:
        """Classify error by type.

        Args:
            error: Exception to classify

        Returns:
            Error category
        """
        error_str = str(error).lower()
        error_type = type(error).__name__.lower()

        # Rate limit detection
        if "429" in error_str or "rate limit" in error_str:
            return ErrorCategory.RATE_LIMIT

        # Network errors
        if any(
            x in error_type
            for x in ["connection", "timeout", "network", "socket"]
        ):
            return ErrorCategory.NETWORK

        # Database errors
        if any(x in error_type for x in ["database", "sql", "db"]):
            return ErrorCategory.DATABASE

        # API errors
        if any(x in error_type for x in ["http", "request", "api"]):
            return ErrorCategory.API

        # Validation errors
        if "validation" in error_type or "value" in error_type:
            return ErrorCategory.VALIDATION

        # Processing errors
        if "processing" in error_type or "runtime" in error_type:
            return ErrorCategory.PROCESSING

        return ErrorCategory.UNKNOWN

    def assess_severity(
        self, error: Exception, category: ErrorCategory
    ) -> ErrorSeverity:
        """Assess error severity.

        Args:
            error: Exception to assess
            category: Error category

        Returns:
            Error severity
        """
        error_str = str(error).lower()

        # Critical errors
        if category in [ErrorCategory.DATABASE, ErrorCategory.SYSTEM]:
            return ErrorSeverity.CRITICAL

        # High severity
        if category == ErrorCategory.NETWORK:
            return ErrorSeverity.HIGH

        # Medium severity
        if category in [ErrorCategory.API, ErrorCategory.RATE_LIMIT]:
            return ErrorSeverity.MEDIUM

        # Low severity
        return ErrorSeverity.LOW

    async def handle_error(
        self,
        error: Exception,
        operation: str,
        user_id: Optional[str] = None,
    ) -> ErrorRecord:
        """Handle an error with classification and logging.

        Args:
            error: Exception to handle
            operation: Operation that failed
            user_id: Optional user ID

        Returns:
            Error record
        """
        category = self.classify_error(error)
        severity = self.assess_severity(error, category)

        error_id = f"{operation}_{int(time.time() * 1000)}"

        record = ErrorRecord(
            error_id=error_id,
            message=str(error),
            category=category,
            severity=severity,
            exception_type=type(error).__name__,
            http_status=self._extract_http_status(error),
            user_message=self._get_user_message(category, severity),
        )

        async with self._lock:
            self.error_history.append(record)

            # Trim history
            if len(self.error_history) > self.max_error_history:
                self.error_history.pop(0)

            # Update counts
            key = f"{category.value}_{severity.value}"
            self.error_counts[key] = self.error_counts.get(key, 0) + 1

        # Log based on severity
        if severity == ErrorSeverity.CRITICAL:
            logger.critical(
                f"[{error_id}] {operation}: {error}", exc_info=True
            )
        elif severity == ErrorSeverity.HIGH:
            logger.error(f"[{error_id}] {operation}: {error}")
        elif severity == ErrorSeverity.MEDIUM:
            logger.warning(f"[{error_id}] {operation}: {error}")
        else:
            logger.info(f"[{error_id}] {operation}: {error}")

        return record

    def _extract_http_status(self, error: Exception) -> Optional[int]:
        """Extract HTTP status code from error.

        Args:
            error: Exception to extract from

        Returns:
            HTTP status code or None
        """
        error_str = str(error)

        # Try to find status code
        for status in [429, 500, 503, 400, 401, 403, 404]:
            if str(status) in error_str:
                return status

        return None

    def _get_user_message(
        self, category: ErrorCategory, severity: ErrorSeverity
    ) -> str:
        """Get user-friendly error message.

        Args:
            category: Error category
            severity: Error severity

        Returns:
            User message
        """
        if category == ErrorCategory.RATE_LIMIT:
            return "Too many requests. Please try again later."

        if category == ErrorCategory.NETWORK:
            return "Network error. Please check your connection."

        if category == ErrorCategory.DATABASE:
            return "Database error. Please try again later."

        if category == ErrorCategory.API:
            return "Service error. Please try again later."

        if severity == ErrorSeverity.CRITICAL:
            return "A critical error occurred. Please contact support."

        return "An error occurred. Please try again."

    def get_error_summary(self) -> Dict[str, Any]:
        """Get error summary statistics.

        Returns:
            Summary dictionary
        """
        return {
            "total_errors": len(self.error_history),
            "error_counts": self.error_counts,
            "recent_errors": [
                {
                    "error_id": e.error_id,
                    "message": e.message,
                    "category": e.category.value,
                    "severity": e.severity.value,
                    "timestamp": e.timestamp.isoformat(),
                }
                for e in self.error_history[-10:]
            ],
        }

    def register_circuit_breaker(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
    ) -> CircuitBreaker:
        """Register a circuit breaker.

        Args:
            name: Circuit breaker name
            failure_threshold: Failures before opening
            recovery_timeout: Seconds before recovery attempt

        Returns:
            Circuit breaker instance
        """
        cb = CircuitBreaker(
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
        )
        self.circuit_breakers[name] = cb
        return cb

    def get_circuit_breaker(self, name: str) -> Optional[CircuitBreaker]:
        """Get circuit breaker by name.

        Args:
            name: Circuit breaker name

        Returns:
            Circuit breaker or None
        """
        return self.circuit_breakers.get(name)

    def get_all_circuit_breakers_status(self) -> Dict[str, Any]:
        """Get status of all circuit breakers.

        Returns:
            Status dictionary
        """
        return {
            name: cb.get_status()
            for name, cb in self.circuit_breakers.items()
        }


# Global error handler instance
_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """Get global error handler instance.

    Returns:
        Error handler instance
    """
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler
