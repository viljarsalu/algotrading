"""Network Configuration Validator - Prevent Accidental Mainnet Trades.

This module provides validation and safety checks for dYdX network configuration
to ensure the application reliably connects to the correct network (testnet/mainnet)
and prevents accidental trades on mainnet during development.
"""

import logging
from enum import Enum
from typing import Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


class NetworkType(Enum):
    """Supported dYdX networks."""
    TESTNET = "testnet"
    MAINNET = "mainnet"


class NetworkID(Enum):
    """dYdX network IDs."""
    TESTNET = 11155111  # Sepolia testnet
    MAINNET = 1  # Mainnet


@dataclass
class NetworkConfig:
    """Network configuration details."""
    network_type: NetworkType
    network_id: int
    indexer_rest_url: str
    indexer_ws_url: str
    chain_id: str
    is_production: bool


class NetworkValidator:
    """Validates and manages dYdX network configuration."""

    # Network configurations
    NETWORKS: Dict[int, NetworkConfig] = {
        NetworkID.TESTNET.value: NetworkConfig(
            network_type=NetworkType.TESTNET,
            network_id=NetworkID.TESTNET.value,
            indexer_rest_url="https://indexer.v4testnet.dydx.exchange",
            indexer_ws_url="wss://indexer.v4testnet.dydx.exchange/v4/ws",
            chain_id="dydx-testnet-1",
            is_production=False,
        ),
        NetworkID.MAINNET.value: NetworkConfig(
            network_type=NetworkType.MAINNET,
            network_id=NetworkID.MAINNET.value,
            indexer_rest_url="https://indexer.dydx.trade/v4",
            indexer_ws_url="wss://indexer.dydx.trade/v4/ws",
            chain_id="dydx-mainnet-1",
            is_production=True,
        ),
    }

    def __init__(self, environment: str, network_id: Optional[int] = None):
        """Initialize network validator.

        Args:
            environment: Application environment (development, testing, staging, production)
            network_id: Optional explicit network ID (overrides environment-based selection)
        """
        self.environment = environment.lower()
        self.explicit_network_id = network_id
        self.validation_timestamp = datetime.utcnow()

    def get_network_config(self) -> Tuple[NetworkConfig, bool]:
        """Get network configuration with validation.

        Returns:
            Tuple of (NetworkConfig, is_safe) where is_safe indicates if configuration is safe

        Raises:
            ValueError: If network configuration is invalid or unsafe
        """
        # Determine network ID
        network_id = self._determine_network_id()

        # Validate network exists
        if network_id not in self.NETWORKS:
            raise ValueError(f"Unsupported network ID: {network_id}")

        config = self.NETWORKS[network_id]

        # Validate environment/network combination
        is_safe = self._validate_environment_network_combination(config)

        if not is_safe:
            raise ValueError(
                f"Unsafe configuration: {self.environment} environment with "
                f"{config.network_type.value} network. "
                f"Production environment requires mainnet."
            )

        return config, is_safe

    def _determine_network_id(self) -> int:
        """Determine which network to use based on environment and explicit settings.

        Returns:
            Network ID to use
        """
        # Explicit network ID takes precedence
        if self.explicit_network_id is not None:
            logger.warning(
                f"Using explicit network ID {self.explicit_network_id}. "
                f"Ensure this is intentional for {self.environment} environment."
            )
            return self.explicit_network_id

        # Environment-based selection
        if self.environment == "production":
            logger.info("Production environment detected. Using mainnet.")
            return NetworkID.MAINNET.value
        else:
            logger.info(f"{self.environment} environment detected. Using testnet.")
            return NetworkID.TESTNET.value

    def _validate_environment_network_combination(self, config: NetworkConfig) -> bool:
        """Validate that environment and network combination is safe.

        Args:
            config: Network configuration to validate

        Returns:
            True if combination is safe, False otherwise
        """
        # Production environment must use mainnet
        if self.environment == "production" and config.network_type == NetworkType.TESTNET:
            logger.error(
                "SECURITY: Production environment cannot use testnet. "
                "This would cause real trades on testnet instead of mainnet."
            )
            return False

        # Staging can use either, but should prefer mainnet
        if self.environment == "staging" and config.network_type == NetworkType.TESTNET:
            logger.warning(
                "Staging environment using testnet. "
                "Consider using mainnet for staging to match production behavior."
            )

        # Development and testing should use testnet
        if self.environment in ["development", "testing"] and config.network_type == NetworkType.MAINNET:
            logger.warning(
                f"{self.environment} environment using mainnet. "
                "This will execute real trades. Ensure this is intentional."
            )

        return True

    def validate_connection_urls(self, config: NetworkConfig) -> Tuple[bool, str]:
        """Validate that network URLs are correctly configured.

        Args:
            config: Network configuration to validate

        Returns:
            Tuple of (is_valid, message)
        """
        try:
            # Check REST URL format
            if not config.indexer_rest_url.startswith(("http://", "https://")):
                return False, f"Invalid REST URL format: {config.indexer_rest_url}"

            # Check WebSocket URL format
            if not config.indexer_ws_url.startswith(("ws://", "wss://")):
                return False, f"Invalid WebSocket URL format: {config.indexer_ws_url}"

            # Check for testnet/mainnet consistency
            if config.network_type == NetworkType.TESTNET:
                if "testnet" not in config.indexer_rest_url.lower():
                    return False, "Testnet REST URL doesn't contain 'testnet'"
                if "testnet" not in config.indexer_ws_url.lower():
                    return False, "Testnet WebSocket URL doesn't contain 'testnet'"
            else:
                if "testnet" in config.indexer_rest_url.lower():
                    return False, "Mainnet REST URL contains 'testnet'"
                if "testnet" in config.indexer_ws_url.lower():
                    return False, "Mainnet WebSocket URL contains 'testnet'"

            return True, "URLs are valid"

        except Exception as e:
            return False, f"URL validation error: {str(e)}"

    def get_safety_warnings(self, config: NetworkConfig) -> list:
        """Get list of safety warnings for current configuration.

        Args:
            config: Network configuration to check

        Returns:
            List of warning messages
        """
        warnings = []

        # Warn if using mainnet in non-production
        if config.network_type == NetworkType.MAINNET and self.environment != "production":
            warnings.append(
                f"⚠️  MAINNET in {self.environment}: Real trades will execute. "
                f"Ensure this is intentional."
            )

        # Warn if using testnet in production
        if config.network_type == NetworkType.TESTNET and self.environment == "production":
            warnings.append(
                "⚠️  TESTNET in production: Trades will execute on testnet, not mainnet."
            )

        return warnings

    def print_network_info(self, config: NetworkConfig) -> None:
        """Print network configuration information.

        Args:
            config: Network configuration to display
        """
        print("\n" + "=" * 60)
        print("dYdX Network Configuration")
        print("=" * 60)
        print(f"Environment: {self.environment}")
        print(f"Network Type: {config.network_type.value.upper()}")
        print(f"Network ID: {config.network_id}")
        print(f"Chain ID: {config.chain_id}")
        print(f"REST URL: {config.indexer_rest_url}")
        print(f"WebSocket URL: {config.indexer_ws_url}")
        print(f"Is Production: {config.is_production}")
        print("=" * 60)

        # Print warnings
        warnings = self.get_safety_warnings(config)
        if warnings:
            print("\n⚠️  WARNINGS:")
            for warning in warnings:
                print(f"  {warning}")
        else:
            print("\n✅ Configuration is safe.")
        print()

    @staticmethod
    def get_network_info_dict(config: NetworkConfig) -> Dict[str, any]:
        """Get network configuration as dictionary.

        Args:
            config: Network configuration

        Returns:
            Dictionary with network information
        """
        return {
            "network_type": config.network_type.value,
            "network_id": config.network_id,
            "chain_id": config.chain_id,
            "indexer_rest_url": config.indexer_rest_url,
            "indexer_ws_url": config.indexer_ws_url,
            "is_production": config.is_production,
        }
