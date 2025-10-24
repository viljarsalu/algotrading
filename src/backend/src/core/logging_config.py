"""
Logging Configuration Module - Centralized Logging Setup.

This module provides comprehensive logging configuration for the
dYdX trading service with structured logging and proper formatting.
"""

import logging
import logging.config
from typing import Dict, Any
import json
import sys
from pathlib import Path

# Create logs directory if it doesn't exist
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# Structured logging formatter
class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": self.formatTime(record, self.default_time_format),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        for key, value in record.__dict__.items():
            if key not in {
                'name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                'thread', 'threadName', 'processName', 'process', 'getMessage',
                'formatTime', 'formatException', 'format'
            }:
                log_entry[key] = value

        return json.dumps(log_entry, default=str)


def get_logging_config(log_level: str = "INFO") -> Dict[str, Any]:
    """Get comprehensive logging configuration.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Logging configuration dictionary
    """
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
            "json": {
                "()": JSONFormatter,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": log_level,
                "formatter": "detailed",
                "stream": sys.stdout,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "DEBUG",
                "formatter": "json",
                "filename": LOGS_DIR / "dydx_trading_service.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8",
            },
            "error_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "ERROR",
                "formatter": "json",
                "filename": LOGS_DIR / "dydx_trading_service_errors.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "encoding": "utf8",
            },
            "trading_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": LOGS_DIR / "trading_operations.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 10,
                "encoding": "utf8",
            },
        },
        "loggers": {
            "": {  # Root logger
                "level": "DEBUG",
                "handlers": ["console", "file", "error_file"],
                "propagate": False,
            },
            "dydx_trading_service": {
                "level": "DEBUG",
                "handlers": ["console", "file", "error_file"],
                "propagate": False,
            },
            "bot": {
                "level": "DEBUG",
                "handlers": ["console", "file", "error_file", "trading_file"],
                "propagate": False,
            },
            "api": {
                "level": "INFO",
                "handlers": ["console", "file", "error_file"],
                "propagate": False,
            },
            "database": {
                "level": "INFO",
                "handlers": ["console", "file", "error_file"],
                "propagate": False,
            },
            "security": {
                "level": "WARNING",
                "handlers": ["console", "file", "error_file"],
                "propagate": False,
            },
        },
    }


def setup_logging(log_level: str = "INFO") -> None:
    """Setup logging configuration.

    Args:
        log_level: Logging level for console output
    """
    config = get_logging_config(log_level)
    logging.config.dictConfig(config)

    # Set specific levels for noisy libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("alembic").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info("Logging configuration initialized")


def get_logger(name: str) -> logging.Logger:
    """Get logger instance with the specified name.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Trading-specific logging helpers

def log_trade_signal(
    logger: logging.Logger,
    user_address: str,
    signal_data: Dict[str, Any],
    **kwargs
) -> None:
    """Log trading signal with structured data.

    Args:
        logger: Logger instance
        user_address: User's wallet address
        signal_data: Trading signal data
        **kwargs: Additional context
    """
    logger.info(
        "Trading signal received",
        extra={
            "user_address": user_address,
            "signal": signal_data,
            "event_type": "trade_signal",
            **kwargs
        }
    )


def log_trade_execution(
    logger: logging.Logger,
    user_address: str,
    result: Dict[str, Any],
    **kwargs
) -> None:
    """Log trade execution result.

    Args:
        logger: Logger instance
        user_address: User's wallet address
        result: Trade execution result
        **kwargs: Additional context
    """
    log_level = logging.ERROR if not result.get('success') else logging.INFO

    logger.log(
        log_level,
        f"Trade execution {'successful' if result.get('success') else 'failed'}",
        extra={
            "user_address": user_address,
            "trade_result": result,
            "event_type": "trade_execution",
            **kwargs
        }
    )


def log_position_update(
    logger: logging.Logger,
    position_id: int,
    action: str,
    details: Dict[str, Any],
    **kwargs
) -> None:
    """Log position update.

    Args:
        logger: Logger instance
        position_id: Position ID
        action: Action performed (created, updated, closed)
        details: Position details
        **kwargs: Additional context
    """
    logger.info(
        f"Position {action}",
        extra={
            "position_id": position_id,
            "action": action,
            "position_details": details,
            "event_type": "position_update",
            **kwargs
        }
    )


def log_risk_check(
    logger: logging.Logger,
    user_address: str,
    check_result: Dict[str, Any],
    **kwargs
) -> None:
    """Log risk management check.

    Args:
        logger: Logger instance
        user_address: User's wallet address
        check_result: Risk check result
        **kwargs: Additional context
    """
    log_level = logging.WARNING if not check_result.get('allowed') else logging.DEBUG

    logger.log(
        log_level,
        f"Risk check {'passed' if check_result.get('allowed') else 'failed'}",
        extra={
            "user_address": user_address,
            "risk_check": check_result,
            "event_type": "risk_check",
            **kwargs
        }
    )


def log_error_with_context(
    logger: logging.Logger,
    error: Exception,
    context: Dict[str, Any],
    **kwargs
) -> None:
    """Log error with additional context.

    Args:
        logger: Logger instance
        error: Exception that occurred
        context: Additional context information
        **kwargs: Additional context
    """
    logger.error(
        f"Error occurred: {str(error)}",
        extra={
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "event_type": "error",
            **kwargs
        },
        exc_info=True
    )