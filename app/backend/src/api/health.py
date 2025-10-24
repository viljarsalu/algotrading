"""Health Check Endpoints - Network and System Status.

This module provides health check endpoints for monitoring network connectivity,
configuration status, and system health.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, status
from datetime import datetime

from src.core.network_validator import NetworkValidator
from src.core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/network", status_code=status.HTTP_200_OK)
async def health_network() -> Dict[str, Any]:
    """
    Check dYdX network connectivity and configuration.

    Returns:
        {
            "status": "healthy",
            "network_type": "testnet",
            "network_id": 11155111,
            "chain_id": "dydx-testnet-1",
            "timestamp": "2024-01-01T00:00:00Z",
            "environment": "development"
        }
    """
    try:
        settings = get_settings()

        # Validate network configuration
        validator = NetworkValidator(
            environment=settings.env,
            network_id=None,
        )

        config, is_safe = validator.get_network_config()

        # Validate URLs
        urls_valid, url_message = validator.validate_connection_urls(config)

        if not urls_valid:
            logger.error(f"Network URL validation failed: {url_message}")
            return {
                "status": "unhealthy",
                "error": url_message,
                "timestamp": datetime.utcnow().isoformat(),
            }, status.HTTP_503_SERVICE_UNAVAILABLE

        # Get warnings
        warnings = validator.get_safety_warnings(config)

        return {
            "status": "healthy",
            "network_type": config.network_type.value,
            "network_id": config.network_id,
            "chain_id": config.chain_id,
            "indexer_rest_url": config.indexer_rest_url,
            "indexer_ws_url": config.indexer_ws_url,
            "is_production": config.is_production,
            "environment": settings.env,
            "is_safe": is_safe,
            "warnings": warnings,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except ValueError as e:
        logger.error(f"Network configuration error: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }, status.HTTP_400_BAD_REQUEST

    except Exception as e:
        logger.error(f"Network health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": "Internal server error",
            "timestamp": datetime.utcnow().isoformat(),
        }, status.HTTP_503_SERVICE_UNAVAILABLE


@router.get("/config", status_code=status.HTTP_200_OK)
async def health_config() -> Dict[str, Any]:
    """
    Check application configuration status.

    Returns:
        {
            "status": "healthy",
            "environment": "development",
            "debug": false,
            "database_configured": true,
            "security_configured": true,
            "dydx_configured": true,
            "issues": []
        }
    """
    try:
        from src.core.config import validate_configuration

        settings = get_settings()
        issues = validate_configuration()

        status_value = "healthy" if not issues else "degraded"

        return {
            "status": status_value,
            "environment": settings.env,
            "debug": settings.debug,
            "database_configured": bool(settings.database.url),
            "security_configured": bool(settings.security.master_key),
            "dydx_configured": bool(settings.dydx_v4.private_key),
            "issues": issues,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Configuration health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": "Internal server error",
            "timestamp": datetime.utcnow().isoformat(),
        }, status.HTTP_503_SERVICE_UNAVAILABLE


@router.get("/", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, Any]:
    """
    General health check endpoint.

    Returns:
        {
            "status": "healthy",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check for Kubernetes/orchestration.

    Returns:
        {
            "ready": true,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    """
    try:
        settings = get_settings()

        # Check critical configurations
        if not settings.dydx_v4.private_key:
            return {
                "ready": False,
                "reason": "dYdX credentials not configured",
                "timestamp": datetime.utcnow().isoformat(),
            }, status.HTTP_503_SERVICE_UNAVAILABLE

        if not settings.security.master_key:
            return {
                "ready": False,
                "reason": "Encryption key not configured",
                "timestamp": datetime.utcnow().isoformat(),
            }, status.HTTP_503_SERVICE_UNAVAILABLE

        return {
            "ready": True,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {
            "ready": False,
            "reason": "Internal server error",
            "timestamp": datetime.utcnow().isoformat(),
        }, status.HTTP_503_SERVICE_UNAVAILABLE


@router.get("/live", status_code=status.HTTP_200_OK)
async def liveness_check() -> Dict[str, Any]:
    """
    Liveness check for Kubernetes/orchestration.

    Returns:
        {
            "alive": true,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    """
    return {
        "alive": True,
        "timestamp": datetime.utcnow().isoformat(),
    }
