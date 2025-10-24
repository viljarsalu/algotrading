"""
Application configuration management for dYdX Trading Service.

This module provides centralized configuration management with environment
variable validation and type conversion for different deployment environments.
"""

import os
import secrets
from typing import List, Optional, Union
from functools import lru_cache
from pydantic import validator, Field
from pydantic_settings import BaseSettings
import logging

logger = logging.getLogger(__name__)


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    url: str = Field(default="sqlite+aiosqlite:///./dydx_trading.db")
    pool_size: int = Field(default=10, ge=1, le=50)
    max_overflow: int = Field(default=20, ge=0, le=100)
    pool_recycle: int = Field(default=3600, ge=60)  # 1 hour minimum
    echo: bool = Field(default=False)

    @validator('url')
    def validate_database_url(cls, v):
        """Validate database URL format."""
        if not v:
            raise ValueError("Database URL cannot be empty")
        return v

    class Config:
        env_prefix = "DATABASE_"


class SecuritySettings(BaseSettings):
    """Security configuration settings."""

    master_key: str = Field(..., min_length=64, max_length=64, alias="MASTER_ENCRYPTION_KEY")
    secret_key: str = Field(default_factory=lambda: secrets.token_urlsafe(32))
    cors_origins: List[str] = Field(default=["http://localhost:3000"])

    @validator('master_key')
    def validate_master_key(cls, v):
        """Validate master encryption key format."""
        if not v:
            raise ValueError("Master encryption key is required")
        if len(v) != 64:
            raise ValueError("Master key must be 64 hex characters (32 bytes)")
        try:
            int(v, 16)
        except ValueError:
            raise ValueError("Master key must be valid hex string")
        return v

    @validator('cors_origins', pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from environment variable."""
        if isinstance(v, str):
            # Handle comma-separated string or JSON-like string
            if v.startswith('[') and v.endswith(']'):
                # Remove brackets and split by comma
                return [origin.strip().strip('"\'') for origin in v[1:-1].split(',') if origin.strip()]
            else:
                # Single origin
                return [v.strip()]
        return v or ["http://localhost:3000"]

    class Config:
        env_prefix = ""  # No prefix for these settings
        populate_by_name = True  # Allow both field name and alias


class DydxV4Settings(BaseSettings):
    """dYdX v4 API configuration settings."""
    
    api_wallet_address: Optional[str] = Field(default=None, alias="DYDX_V4_API_WALLET_ADDRESS")
    private_key: Optional[str] = Field(default=None, alias="DYDX_V4_PRIVATE_KEY")
    network_id: int = Field(default=11155111, alias="DYDX_V4_NETWORK_ID")

    @validator('private_key')
    def validate_private_key(cls, v):
        """Validate private key format."""
        if v and not v.startswith('0x'):
            raise ValueError("Private key must start with 0x")
        return v
    
    class Config:
        env_prefix = "" # No prefix, using alias
        populate_by_name = True


class WorkerSettings(BaseSettings):
    """Position monitoring worker configuration settings."""

    # Monitoring behavior
    monitoring_interval: int = Field(default=30, ge=10, le=300)  # seconds
    max_workers: int = Field(default=5, ge=1, le=20)
    batch_size: int = Field(default=10, ge=1, le=50)

    # Retry and error handling
    max_retries: int = Field(default=3, ge=1, le=10)
    retry_backoff: int = Field(default=60, ge=10, le=300)  # seconds

    # Health monitoring
    health_check_interval: int = Field(default=300, ge=60, le=3600)  # 5 minutes default
    max_concurrent_positions: int = Field(default=20, ge=1, le=100)

    # Feature flags
    enable_notifications: bool = Field(default=True)
    enable_monitoring: bool = Field(default=True)

    # Performance tuning
    rate_limit_delay: float = Field(default=0.1, ge=0.0, le=1.0)  # seconds between API calls

    @validator('monitoring_interval')
    def validate_monitoring_interval(cls, v):
        """Validate monitoring interval is reasonable."""
        if v < 10:
            raise ValueError("Monitoring interval must be at least 10 seconds")
        return v

    class Config:
        env_prefix = "WORKER_"


class ApplicationSettings(BaseSettings):
    """Main application configuration settings."""

    # Environment
    env: str = Field(default="development")
    debug: bool = Field(default=False)

    # Server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000, ge=1, le=65535)

    # Logging
    log_level: str = Field(default="INFO")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Database settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)

    # Security settings
    security: SecuritySettings = Field(default_factory=SecuritySettings)

    # Worker settings
    worker: WorkerSettings = Field(default_factory=WorkerSettings)

    # dYdX v4 settings
    dydx_v4: DydxV4Settings = Field(default_factory=DydxV4Settings)
 
    @validator('env')
    def validate_environment(cls, v):
        """Validate environment setting."""
        valid_envs = {"development", "testing", "staging", "production"}
        if v.lower() not in valid_envs:
            raise ValueError(f"Environment must be one of: {valid_envs}")
        return v.lower()

    @validator('log_level')
    def validate_log_level(cls, v):
        """Validate log level setting."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()

    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.env == "development"

    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.env == "production"

    def is_testing(self) -> bool:
        """Check if running in testing mode."""
        return self.env == "testing"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


class Settings:
    """Main settings container with lazy loading."""

    def __init__(self):
        self._settings: Optional[ApplicationSettings] = None

    def __getattr__(self, name: str) -> any:
        """Lazy load settings on first access."""
        if self._settings is None:
            self._settings = ApplicationSettings()
        return getattr(self._settings, name)

    def reload(self) -> None:
        """Reload settings from environment (for testing)."""
        self._settings = ApplicationSettings()


# Global settings instance
settings = Settings()


@lru_cache()
def get_settings() -> ApplicationSettings:
    """Get cached application settings.

    Returns:
        ApplicationSettings instance
    """
    return ApplicationSettings()


def get_database_url() -> str:
    """Get database URL from settings.

    Returns:
        Database connection URL
    """
    return get_settings().database.url


def get_cors_origins() -> List[str]:
    """Get CORS origins from settings.

    Returns:
        List of allowed CORS origins
    """
    return get_settings().security.cors_origins


def is_development() -> bool:
    """Check if running in development mode.

    Returns:
        True if in development mode
    """
    return get_settings().is_development()


def is_production() -> bool:
    """Check if running in production mode.

    Returns:
        True if in production mode
    """
    return get_settings().is_production()


def is_testing() -> bool:
    """Check if running in testing mode.

    Returns:
        True if in testing mode
    """
    return get_settings().is_testing()


# Environment-specific configurations

def get_logging_config() -> dict:
    """Get logging configuration based on environment.

    Returns:
        Dictionary with logging configuration
    """
    app_settings = get_settings()

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": app_settings.log_format,
            },
            "access": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "": {  # Root logger
                "handlers": ["console"],
                "level": app_settings.log_level,
            },
            "uvicorn.access": {
                "handlers": ["console"],
                "level": "WARNING",
                "propagate": False,
            },
        },
    }

    # Add file handler for production
    if app_settings.is_production():
        config["handlers"]["file"] = {
            "class": "logging.FileHandler",
            "formatter": "default",
            "filename": "logs/dydx_trading.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
        }
        config["loggers"][""]["handlers"].append("file")

    return config


def get_cors_middleware_config() -> dict:
    """Get CORS middleware configuration.

    Returns:
        Dictionary with CORS settings
    """
    return {
        "allow_origins": get_cors_origins(),
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["*"],
    }


def validate_configuration() -> List[str]:
    """Validate current configuration and return any warnings or errors.

    Returns:
        List of validation messages
    """
    messages = []
    app_settings = get_settings()

    # Check for development defaults in production
    if app_settings.is_production():
        if app_settings.debug:
            messages.append("WARNING: Debug mode enabled in production")

        if app_settings.security.secret_key == "your-secret-key-here-replace-with-secure-random-string":
            messages.append("ERROR: Default secret key used in production")

        if not app_settings.database.url.startswith(("postgresql://", "mysql://")):
            messages.append("WARNING: Using non-production database in production")

    # Check for missing encryption key
    if not app_settings.security.master_key or app_settings.security.master_key == "YOUR_MASTER_ENCRYPTION_KEY_HERE_REPLACE_WITH_SECURE_32_BYTE_HEX":
        messages.append("ERROR: Master encryption key not properly configured")

    # Check CORS configuration
    if "http://localhost:3000" in app_settings.security.cors_origins and not app_settings.is_development():
        messages.append("WARNING: Localhost CORS origin configured for non-development environment")

    # Check dYdX v4 configuration
    if not app_settings.dydx_v4.api_wallet_address or not app_settings.dydx_v4.private_key:
        messages.append("ERROR: dYdX v4 API wallet address or private key is not configured")
 
    return messages
 
 
def print_configuration_info() -> None:
    """Print current configuration information (for debugging)."""
    app_settings = get_settings()

    print("=== dYdX Trading Service Configuration ===")
    print(f"Environment: {app_settings.env}")
    print(f"Debug: {app_settings.debug}")
    print(f"Host: {app_settings.host}")
    print(f"Port: {app_settings.port}")
    print(f"Log Level: {app_settings.log_level}")
    print(f"Database URL: {app_settings.database.url.replace(app_settings.database.url.split('@')[-1], '***') if '@' in app_settings.database.url else app_settings.database.url}")
    print(f"CORS Origins: {app_settings.security.cors_origins}")
    print(f"Master Key Configured: {'Yes' if app_settings.security.master_key != 'YOUR_MASTER_ENCRYPTION_KEY_HERE_REPLACE_WITH_SECURE_32_BYTE_HEX' else 'No'}")
    print(f"dYdX v4 Wallet Address: {app_settings.dydx_v4.api_wallet_address}")
    print(f"dYdX v4 Private Key Configured: {'Yes' if app_settings.dydx_v4.private_key else 'No'}")
 
    # Print validation messages
    validation_messages = validate_configuration()
    if validation_messages:
        print("\n=== Configuration Issues ===")
        for message in validation_messages:
            print(f"  - {message}")
    else:
        print("\n=== Configuration Valid ===")


# Development helpers

def generate_sample_env_file() -> str:
    """Generate sample .env file content for development.

    Returns:
        String with sample environment configuration
    """
    return '''# dYdX Trading Service - Sample Environment Configuration
# Copy this file to .env and update the values

# dYdX V4 API Configuration
DYDX_V4_PRIVATE_KEY=YOUR_DYDX_V4_PRIVATE_KEY_HERE
DYDX_V4_API_WALLET_ADDRESS=YOUR_DYDX_V4_WALLET_ADDRESS_HERE

# Master Encryption Key (Generate with: python3 -c "import secrets; print(secrets.token_hex(32))")
MASTER_ENCRYPTION_KEY=YOUR_MASTER_ENCRYPTION_KEY_HERE
 
# Database Configuration
DATABASE_URL=postgresql+asyncpg://dydx_user:dydx_password@localhost:5432/dydx_trading
POSTGRES_DB=dydx_trading
POSTGRES_USER=dydx_user
POSTGRES_PASSWORD=dydx_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Application Configuration
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=true

# Security Configuration
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8000"]
SECRET_KEY=your-secret-key-here-replace-with-secure-random-string

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s

# Worker Configuration (Position Monitoring)
WORKER_MONITORING_INTERVAL=30
WORKER_MAX_WORKERS=5
WORKER_BATCH_SIZE=10
WORKER_MAX_RETRIES=3
WORKER_RETRY_BACKOFF=60
WORKER_HEALTH_CHECK_INTERVAL=300
WORKER_MAX_CONCURRENT_POSITIONS=20
WORKER_ENABLE_NOTIFICATIONS=true
WORKER_ENABLE_MONITORING=true
WORKER_RATE_LIMIT_DELAY=0.1
'''


if __name__ == "__main__":
    """Main entry point for configuration testing."""
    print_configuration_info()