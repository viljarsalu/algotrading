"""
dYdX Trading Service - Main FastAPI Application.

This module creates and configures the FastAPI application with all
necessary middleware, routes, and lifecycle event handlers.
"""

import asyncio
import logging
import os
import re
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import uvicorn

from .core.config import get_settings, get_cors_middleware_config, validate_configuration
from .core.network_validator import NetworkValidator
from .core.resilience import get_error_handler
from .db.database import init_db, check_db_health, get_database_manager
from .core.security import get_encryption_manager
from .core.logging_config import setup_logging, get_logger
from .api import auth, trading, user, webhooks, websockets, health, equity_curve
# from .api import pnl, errors  # TODO: Need proper authentication setup
from .api import websockets_enhanced
from .workers.position_monitor import initialize_worker, graceful_shutdown, health_check as worker_health_check

# Setup comprehensive logging
setup_logging(get_settings().log_level)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    print("Starting dYdX Trading Service...")
    logger.info("Starting dYdX Trading Service...")

    try:
        print("Starting lifespan event handler...")
        
        # Validate network configuration
        print("Validating network configuration...")
        settings = get_settings()
        try:
            validator = NetworkValidator(environment=settings.env)
            config, is_safe = validator.get_network_config()
            logger.info(f"Network validation passed: {config.network_type.value} ({config.chain_id})")
            validator.print_network_info(config)
        except ValueError as e:
            logger.error(f"Network validation failed: {e}")
            raise
        
        # Validate configuration
        print("Validating application configuration...")
        validation_messages = validate_configuration()
        print(f"Configuration validation messages: {validation_messages}")
        if validation_messages:
            for message in validation_messages:
                if message.startswith("ERROR"):
                    logger.error(f"Configuration error: {message}")
                    raise ValueError(f"Configuration error: {message}")
                else:
                    logger.warning(f"Configuration warning: {message}")

        # Initialize encryption manager
        encryption_manager = get_encryption_manager()
        logger.info("Encryption manager initialized")

        # Initialize database
        await init_db()
        logger.info("Database initialized successfully")

        # Test database health
        db_health = await check_db_health()
        if db_health['status'] != 'healthy':
            raise RuntimeError(f"Database health check failed: {db_health.get('error')}")

        logger.info(f"Database health check passed in {db_health['response_time_ms']}ms")

        # Create sample data in development mode
        if get_settings().is_development():
            from .db.database import create_sample_data
            await create_sample_data()
            logger.info("Sample data created for development")

        # Initialize error handler and circuit breakers
        print("Initializing error handler and circuit breakers...")
        error_handler = get_error_handler()
        error_handler.register_circuit_breaker("dydx_api", failure_threshold=5, recovery_timeout=60)
        error_handler.register_circuit_breaker("websocket", failure_threshold=3, recovery_timeout=30)
        error_handler.register_circuit_breaker("database", failure_threshold=3, recovery_timeout=30)
        logger.info("Error handler and circuit breakers initialized")
        app.state.error_handler = error_handler

        # Initialize and start position monitoring worker
        try:
            # Get worker configuration from settings
            worker_config = {
                'monitoring_interval': get_settings().worker.monitoring_interval,
                'max_workers': get_settings().worker.max_workers,
                'batch_size': get_settings().worker.batch_size,
                'max_retries': get_settings().worker.max_retries,
                'retry_backoff': get_settings().worker.retry_backoff,
                'health_check_interval': get_settings().worker.health_check_interval,
                'max_concurrent_positions': get_settings().worker.max_concurrent_positions,
                'enable_notifications': get_settings().worker.enable_notifications,
                'enable_monitoring': get_settings().worker.enable_monitoring,
                'rate_limit_delay': get_settings().worker.rate_limit_delay,
            }

            # Initialize worker
            worker = await initialize_worker(app, worker_config)
            logger.info("Position monitoring worker initialized and started")

            # Store worker instance in app state for health checks
            app.state.position_monitor_worker = worker

        except Exception as e:
            logger.error(f"Failed to initialize position monitoring worker: {e}")
            # Don't fail the entire application if worker fails to start
            logger.warning("Application will continue without position monitoring worker")

        logger.info("dYdX Trading Service startup completed successfully")

    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down dYdX Trading Service...")

    try:
        # Stop position monitoring worker
        if hasattr(app.state, 'position_monitor_worker'):
            await graceful_shutdown(app)
            logger.info("Position monitoring worker stopped")

        # Close database connections
        db_manager = get_database_manager()
        await db_manager.close()
        logger.info("Database connections closed")

    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

    logger.info("dYdX Trading Service shutdown completed")


def create_application() -> FastAPI:
    """Create and configure FastAPI application.

    Returns:
        Configured FastAPI application instance
    """
    # Create FastAPI app with lifespan manager
    app = FastAPI(
        title="dYdX Trading Service",
        description="Multi-tenant trading platform for dYdX protocol",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )

    # Include API routers
    print("Including API routers...")
    app.include_router(auth.router)
    print("Auth router included")
    app.include_router(user.router)
    print("User router included")
    app.include_router(trading.router)
    print("Trading router included")
    app.include_router(webhooks.router)
    print("Webhooks router included")
    app.include_router(websockets.router)
    print("WebSocket router included")
    app.include_router(websockets_enhanced.router)
    print("Enhanced WebSocket router included")
    app.include_router(health.router)
    print("Health check router included")
    # app.include_router(pnl.router)
    # print("PNL router included")
    # app.include_router(errors.router)
    # print("Error router included")
    # TODO: These routers need proper authentication setup
    app.include_router(equity_curve.router)
    print("Equity curve router included")

    # Add CORS middleware
    cors_config = get_cors_middleware_config()
    app.add_middleware(
        CORSMiddleware,
        **cors_config
    )
    logger.info(f"CORS configured for origins: {cors_config['allow_origins']}")

    # Configure rate limiting
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"]
    )

    # Add rate limiting to specific routes
    app.state.limiter = limiter

    # Add SlowAPI middleware for rate limiting
    print("Adding SlowAPI middleware...")
    app.add_middleware(SlowAPIMiddleware)
    print("SlowAPI middleware added")

    # Add rate limit exceeded handler
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    print("Rate limit exception handler added")

    # Mount static files directory
    app.mount("/static", StaticFiles(directory="src/static"), name="static")

    # Add security headers middleware
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        """Add security headers to all responses."""
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content Security Policy - allow necessary external resources for different pages
        if request.url.path in ["/docs", "/redoc", "/openapi.json"]:
            # Swagger UI - allow CDN resources and inline scripts
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "img-src 'self' data: https://cdn.jsdelivr.net https://fastapi.tiangolo.com; "
                "font-src 'self' https://cdn.jsdelivr.net; "
                "connect-src 'self'"
            )
        elif request.url.path in ["/login", "/dashboard"]:
            # Login/Dashboard pages - allow Tailwind CDN and inline scripts
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://cdn.jsdelivr.net/npm/chart.js; "
                "style-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com; "
                "img-src 'self' data:; "
                "font-src 'self'; "
                "connect-src 'self'"
            )
        else:
            # Default restrictive policy for other pages
            response.headers["Content-Security-Policy"] = "default-src 'self'"

        return response

    # Add request validation middleware
    @app.middleware("http")
    async def validate_request(request: Request, call_next):
        """Validate incoming requests for security and format."""
        # Skip validation for health check endpoints
        if request.url.path in ["/", "/health/detailed", "/ready", "/live", "/health/network", "/health/config", "/health/"]:
            return await call_next(request)

        # Validate Content-Type for POST/PUT requests
        if request.method in ["POST", "PUT"]:
            content_type = request.headers.get("content-type", "")
            if not content_type.startswith("application/json"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Content-Type must be application/json"
                )

        # Validate request size (prevent large payload attacks)
        content_length = request.headers.get("content-length")
        if content_length:
            max_size = 1024 * 1024  # 1MB limit
            if int(content_length) > max_size:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail="Request payload too large"
                )

        # For auth endpoints, we need to validate the body but also cache it for reuse
        if "auth" in request.url.path and request.method == "POST":
            if request.url.path in ["/api/auth/login", "/api/auth/create-user"]:
                try:
                    # Read and cache the body
                    body_bytes = await request.body()
                    
                    # Parse the JSON
                    import json
                    body = json.loads(body_bytes.decode('utf-8'))
                    
                    wallet_address = body.get("wallet_address", "")

                    # Basic Ethereum address validation
                    if wallet_address:
                        if not wallet_address.startswith("0x") or len(wallet_address) != 42:
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Invalid wallet address format"
                            )

                        # Check for valid hex characters
                        try:
                            int(wallet_address[2:], 16)
                        except ValueError:
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Invalid wallet address format"
                            )
                    
                    # Validate signature format for login endpoint
                    if request.url.path == "/api/auth/login":
                        signature = body.get("signature", "")
                        if signature:
                            # Basic signature format validation
                            if not signature.startswith("0x"):
                                signature = "0x" + signature
                            
                            # Check if it's a valid hex string
                            try:
                                int(signature[2:], 16)
                            except ValueError:
                                raise HTTPException(
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="Invalid signature format"
                                )
                    
                    # Create a new request with cached body
                    async def receive():
                        return {"type": "http.request", "body": body_bytes}
                    
                    # Replace the request's receive method
                    request._receive = receive

                except json.JSONDecodeError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Invalid JSON format"
                    )
                except Exception as e:
                    logger.error(f"Request validation error: {e}")
                    # Let the endpoint handle other errors
                    pass

        return await call_next(request)

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Handle unhandled exceptions globally."""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "message": "An unexpected error occurred",
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    return app


# Create the main application instance
app = create_application()


@app.get("/")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint.

    Returns:
        Health status information including database connectivity
    """
    try:
        # Get database health
        db_health = await check_db_health()

        # Overall health status
        overall_status = "healthy" if db_health['status'] == 'healthy' else "unhealthy"

        health_info = {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "environment": get_settings().env,
            "database": db_health,
            "uptime_seconds": getattr(app.state, 'uptime_seconds', 0)
        }

        # Return appropriate status code
        status_code = status.HTTP_200_OK if overall_status == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE

        return JSONResponse(
            status_code=status_code,
            content=health_info
        )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": "Health check failed",
                "message": str(e)
            }
        )


@app.get("/login", response_class=HTMLResponse)
async def login_page():
    """Serve the login page."""
    try:
        with open("src/templates/index.html", "r") as f:
            content = f.read()
        return HTMLResponse(content)
    except FileNotFoundError:
        return HTMLResponse("<h1>Login page not found</h1>", status_code=404)
    except Exception as e:
        return HTMLResponse(f"<h1>Error loading login page: {str(e)}</h1>", status_code=500)


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page():
    """Serve the dashboard page."""
    try:
        with open("src/templates/dashboard.html", "r") as f:
            content = f.read()
        return HTMLResponse(content)
    except FileNotFoundError:
        return HTMLResponse("<h1>Dashboard page not found</h1>", status_code=404)
    except Exception as e:
        return HTMLResponse(f"<h1>Error loading dashboard: {str(e)}</h1>", status_code=500)


@app.get("/health/detailed")
async def detailed_health_check() -> Dict[str, Any]:
    """Detailed health check with comprehensive system information.

    Returns:
        Detailed health information including system metrics
    """
    try:
        # Database health
        db_health = await check_db_health()

        # System information
        import psutil
        import platform

        system_info = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": os.cpu_count(),
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "percent_used": psutil.virtual_memory().percent
            }
        }

        # Application metrics
        app_metrics = {
            "environment": get_settings().env,
            "debug_mode": get_settings().debug,
            "host": get_settings().host,
            "port": get_settings().port,
            "log_level": get_settings().log_level
        }

        # Overall status
        overall_status = "healthy" if db_health['status'] == 'healthy' else "unhealthy"

        health_info = {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "system": system_info,
            "application": app_metrics,
            "database": db_health
        }

        status_code = status.HTTP_200_OK if overall_status == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE

        return JSONResponse(
            status_code=status_code,
            content=health_info
        )

    except ImportError:
        # psutil not available
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": "System monitoring unavailable",
                "message": "psutil package not installed"
            }
        )
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": "Detailed health check failed",
                "message": str(e)
            }
        )


@app.get("/ready")
async def readiness_check() -> Dict[str, Any]:
    """Kubernetes readiness probe endpoint.

    Returns:
        Readiness status for load balancer health checks
    """
    try:
        db_health = await check_db_health()

        if db_health['status'] == 'healthy':
            return {
                "status": "ready",
                "timestamp": datetime.utcnow().isoformat(),
                "database": "connected"
            }
        else:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "status": "not_ready",
                    "timestamp": datetime.utcnow().isoformat(),
                    "database": "disconnected",
                    "error": db_health.get('error')
                }
            )

    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
        )


@app.get("/live")
async def liveness_check() -> Dict[str, Any]:
    """Kubernetes liveness probe endpoint.

    Returns:
        Liveness status for container health checks
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": getattr(app.state, 'uptime_seconds', 0)
    }


@app.get("/health/worker")
async def worker_health_check() -> Dict[str, Any]:
    """Position monitoring worker health check endpoint.

    Returns:
        Worker health status and metrics
    """
    try:
        # Get worker health status
        worker_status = await worker_health_check()

        # Overall health status
        if worker_status.get('is_running', False):
            overall_status = "healthy"
            status_code = status.HTTP_200_OK
        else:
            overall_status = "stopped"
            status_code = status.HTTP_503_SERVICE_UNAVAILABLE

        health_info = {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "worker": worker_status
        }

        return JSONResponse(
            status_code=status_code,
            content=health_info
        )

    except Exception as e:
        logger.error(f"Worker health check failed: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": "Worker health check failed",
                "message": str(e)
            }
        )


@app.get("/api/worker/status")
async def get_worker_status() -> Dict[str, Any]:
    """Get detailed worker status and metrics.

    Returns:
        Detailed worker status information
    """
    try:
        worker_status = await worker_health_check()

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "worker": worker_status
        }

    except Exception as e:
        logger.error(f"Failed to get worker status: {e}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }


@app.post("/api/worker/start")
async def start_worker() -> Dict[str, Any]:
    """Start the position monitoring worker.

    Returns:
        Worker start result
    """
    try:
        if hasattr(app.state, 'position_monitor_worker'):
            await app.state.position_monitor_worker.start_monitoring()
            return {
                "success": True,
                "message": "Worker started successfully",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {
                "success": False,
                "error": "Worker not initialized",
                "timestamp": datetime.utcnow().isoformat()
            }

    except Exception as e:
        logger.error(f"Failed to start worker: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@app.post("/api/worker/stop")
async def stop_worker() -> Dict[str, Any]:
    """Stop the position monitoring worker.

    Returns:
        Worker stop result
    """
    try:
        if hasattr(app.state, 'position_monitor_worker'):
            await app.state.position_monitor_worker.stop_monitoring()
            return {
                "success": True,
                "message": "Worker stopped successfully",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {
                "success": False,
                "error": "Worker not initialized",
                "timestamp": datetime.utcnow().isoformat()
            }

    except Exception as e:
        logger.error(f"Failed to stop worker: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


def main() -> None:
    """Main entry point for running the application."""
    settings = get_settings()

    logger.info(f"Starting dYdX Trading Service in {settings.env} mode")
    logger.info(f"Server will run on {settings.host}:{settings.port}")

    # Configure uvicorn
    config = uvicorn.Config(
        app=app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        access_log=True,
        reload=settings.is_development(),
        reload_dirs=["./src"] if settings.is_development() else None
    )

    server = uvicorn.Server(config)

    # Store server instance for graceful shutdown
    app.state.server = server

    try:
        server.run()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
    finally:
        logger.info("Server shutdown complete")


if __name__ == "__main__":
    main()