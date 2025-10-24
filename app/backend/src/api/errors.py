"""Error API Endpoints - User-Facing Error Handling and Notifications.

This module provides API endpoints for error handling, notifications,
and system status reporting.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..core.security import get_current_user, verify_jwt_token
from ..core.resilience import get_error_handler, ErrorSeverity
from ..db.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/errors", tags=["errors"])


@router.get("/summary")
async def get_error_summary(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get error summary for current user.

    Returns:
        Error summary with recent errors and statistics
    """
    try:
        error_handler = get_error_handler()
        summary = error_handler.get_error_summary()

        return {
            "status": "success",
            "data": summary,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get error summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve error summary"
        )


@router.get("/rate-limit-status")
async def get_rate_limit_status(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get rate limit status for current user.

    Returns:
        Rate limit information
    """
    try:
        error_handler = get_error_handler()
        rate_limiter = error_handler.rate_limiter

        user_key = f"user_{current_user.id}"
        is_limited = rate_limiter.is_rate_limited(user_key)
        retry_after = rate_limiter.get_retry_after(user_key)

        return {
            "status": "success",
            "is_rate_limited": is_limited,
            "retry_after_seconds": retry_after,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get rate limit status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve rate limit status"
        )


@router.get("/circuit-breakers")
async def get_circuit_breaker_status(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get status of all circuit breakers.

    Returns:
        Circuit breaker status information
    """
    try:
        error_handler = get_error_handler()
        status_info = error_handler.get_all_circuit_breakers_status()

        return {
            "status": "success",
            "circuit_breakers": status_info,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get circuit breaker status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve circuit breaker status"
        )


@router.get("/system-health")
async def get_system_health(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get overall system health status.

    Returns:
        System health information
    """
    try:
        error_handler = get_error_handler()
        summary = error_handler.get_error_summary()
        circuit_breakers = error_handler.get_all_circuit_breakers_status()

        # Determine overall health
        total_errors = summary.get("total_errors", 0)
        critical_errors = sum(
            1 for e in summary.get("recent_errors", [])
            if e.get("severity") == "critical"
        )
        open_circuits = sum(
            1 for cb in circuit_breakers.values()
            if cb.get("state") == "open"
        )

        if critical_errors > 0 or open_circuits > 2:
            health_status = "degraded"
        elif open_circuits > 0:
            health_status = "warning"
        else:
            health_status = "healthy"

        return {
            "status": "success",
            "health": health_status,
            "metrics": {
                "total_errors": total_errors,
                "critical_errors": critical_errors,
                "open_circuits": open_circuits,
                "circuit_breakers_total": len(circuit_breakers),
            },
            "circuit_breakers": circuit_breakers,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get system health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system health"
        )


@router.post("/report")
async def report_error(
    error_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Report an error from the client.

    Args:
        error_data: Error information from client
        current_user: Current authenticated user

    Returns:
        Error report confirmation
    """
    try:
        error_handler = get_error_handler()

        # Extract error information
        operation = error_data.get("operation", "unknown")
        message = error_data.get("message", "Unknown error")
        error_type = error_data.get("error_type", "unknown")

        # Create error for logging
        class ClientError(Exception):
            pass

        error = ClientError(message)

        # Handle error
        record = await error_handler.handle_error(
            error=error,
            operation=f"client_{operation}",
            user_id=str(current_user.id),
        )

        logger.info(
            f"Client error reported by {current_user.id}: "
            f"{operation} - {message}"
        )

        return {
            "status": "success",
            "error_id": record.error_id,
            "message": "Error reported successfully",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to report error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to report error"
        )


@router.get("/notifications")
async def get_error_notifications(
    severity: Optional[str] = None,
    limit: int = 10,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get error notifications for current user.

    Args:
        severity: Optional severity filter (low, medium, high, critical)
        limit: Maximum number of notifications
        current_user: Current authenticated user

    Returns:
        List of error notifications
    """
    try:
        error_handler = get_error_handler()
        summary = error_handler.get_error_summary()

        notifications = summary.get("recent_errors", [])

        # Filter by severity if specified
        if severity:
            notifications = [
                n for n in notifications
                if n.get("severity") == severity
            ]

        # Limit results
        notifications = notifications[-limit:]

        # Convert to notification format
        formatted_notifications = [
            {
                "id": n.get("error_id"),
                "title": f"{n.get('category').upper()} Error",
                "message": n.get("message"),
                "severity": n.get("severity"),
                "timestamp": n.get("timestamp"),
                "action": _get_notification_action(n.get("category")),
            }
            for n in notifications
        ]

        return {
            "status": "success",
            "notifications": formatted_notifications,
            "total": len(formatted_notifications),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get error notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve error notifications"
        )


@router.post("/acknowledge/{error_id}")
async def acknowledge_error(
    error_id: str,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Acknowledge an error notification.

    Args:
        error_id: Error ID to acknowledge
        current_user: Current authenticated user

    Returns:
        Acknowledgment confirmation
    """
    try:
        logger.info(f"Error {error_id} acknowledged by {current_user.id}")

        return {
            "status": "success",
            "message": "Error acknowledged",
            "error_id": error_id,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to acknowledge error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to acknowledge error"
        )


def _get_notification_action(category: str) -> Dict[str, str]:
    """Get recommended action for error category.

    Args:
        category: Error category

    Returns:
        Action dictionary with type and message
    """
    actions = {
        "rate_limit": {
            "type": "wait",
            "message": "Please wait before retrying",
        },
        "network": {
            "type": "retry",
            "message": "Check your connection and retry",
        },
        "database": {
            "type": "contact_support",
            "message": "Contact support if problem persists",
        },
        "api": {
            "type": "retry",
            "message": "Service temporarily unavailable, retrying...",
        },
        "validation": {
            "type": "fix_input",
            "message": "Please check your input and try again",
        },
    }

    return actions.get(category, {
        "type": "retry",
        "message": "Please try again",
    })


@router.get("/degradation-mode")
async def check_degradation_mode(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Check if system is in degradation mode.

    Returns:
        Degradation mode status and affected features
    """
    try:
        error_handler = get_error_handler()
        circuit_breakers = error_handler.get_all_circuit_breakers_status()

        open_circuits = [
            name for name, cb in circuit_breakers.items()
            if cb.get("state") == "open"
        ]

        is_degraded = len(open_circuits) > 0

        affected_features = _get_affected_features(open_circuits)

        return {
            "status": "success",
            "is_degraded": is_degraded,
            "open_circuits": open_circuits,
            "affected_features": affected_features,
            "fallback_available": len(affected_features) > 0,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to check degradation mode: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check degradation mode"
        )


def _get_affected_features(open_circuits: list) -> list:
    """Get list of affected features based on open circuits.

    Args:
        open_circuits: List of open circuit breaker names

    Returns:
        List of affected features
    """
    feature_map = {
        "websocket": "Real-time updates (using polling fallback)",
        "dydx_api": "Trading operations (limited functionality)",
        "database": "Data persistence (read-only mode)",
        "notifications": "User notifications (delayed)",
    }

    affected = []
    for circuit in open_circuits:
        if circuit in feature_map:
            affected.append({
                "feature": circuit,
                "status": "degraded",
                "message": feature_map[circuit],
            })

    return affected
