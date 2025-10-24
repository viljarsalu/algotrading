#!/usr/bin/env python3
"""Network Configuration Validation Script.

This script validates the dYdX network configuration before deployment.
Run this script to catch configuration issues early.

Usage:
    python validate_network_config.py
    python validate_network_config.py --verbose
    python validate_network_config.py --environment production
"""

import sys
import os
import argparse
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.network_validator import NetworkValidator
from src.core.config import get_settings, validate_configuration


def print_header(text: str) -> None:
    """Print formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_section(text: str) -> None:
    """Print formatted section."""
    print(f"\n▶ {text}")
    print("-" * 70)


def print_success(text: str) -> None:
    """Print success message."""
    print(f"  ✅ {text}")


def print_warning(text: str) -> None:
    """Print warning message."""
    print(f"  ⚠️  {text}")


def print_error(text: str) -> None:
    """Print error message."""
    print(f"  ❌ {text}")


def validate_environment_variables() -> bool:
    """Validate required environment variables.

    Returns:
        True if all required variables are set, False otherwise
    """
    print_section("Environment Variables")

    required_vars = {
        "DYDX_V4_PRIVATE_KEY": "dYdX v4 private key",
        "DYDX_V4_API_WALLET_ADDRESS": "dYdX v4 wallet address",
        "MASTER_ENCRYPTION_KEY": "Master encryption key",
    }

    all_valid = True

    for var_name, description in required_vars.items():
        if os.getenv(var_name):
            # Show masked value for security
            value = os.getenv(var_name)
            if len(value) > 10:
                masked = value[:4] + "*" * (len(value) - 8) + value[-4:]
            else:
                masked = "*" * len(value)
            print_success(f"{var_name}: {masked}")
        else:
            print_error(f"{var_name}: NOT SET ({description})")
            all_valid = False

    return all_valid


def validate_network_configuration(environment: str) -> bool:
    """Validate network configuration.

    Args:
        environment: Application environment

    Returns:
        True if configuration is valid, False otherwise
    """
    print_section("Network Configuration")

    try:
        # Create validator
        validator = NetworkValidator(environment=environment)

        # Get network config
        config, is_safe = validator.get_network_config()

        # Print network info
        print_success(f"Environment: {environment}")
        print_success(f"Network Type: {config.network_type.value.upper()}")
        print_success(f"Network ID: {config.network_id}")
        print_success(f"Chain ID: {config.chain_id}")
        print_success(f"REST URL: {config.indexer_rest_url}")
        print_success(f"WebSocket URL: {config.indexer_ws_url}")

        # Validate URLs
        urls_valid, url_message = validator.validate_connection_urls(config)
        if urls_valid:
            print_success("URLs are valid and consistent")
        else:
            print_error(f"URL validation failed: {url_message}")
            return False

        # Check safety
        if is_safe:
            print_success("Configuration is safe")
        else:
            print_error("Configuration is NOT safe")
            return False

        # Show warnings
        warnings = validator.get_safety_warnings(config)
        if warnings:
            for warning in warnings:
                print_warning(warning)

        return True

    except ValueError as e:
        print_error(f"Configuration error: {e}")
        return False
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return False


def validate_application_configuration() -> bool:
    """Validate application configuration.

    Returns:
        True if configuration is valid, False otherwise
    """
    print_section("Application Configuration")

    try:
        settings = get_settings()

        # Check environment
        print_success(f"Environment: {settings.env}")
        print_success(f"Debug Mode: {settings.debug}")
        print_success(f"Log Level: {settings.log_level}")

        # Check database
        if settings.database.url:
            print_success(f"Database: Configured")
        else:
            print_error("Database: NOT configured")
            return False

        # Check security
        if settings.security.master_key:
            print_success("Master Encryption Key: Configured")
        else:
            print_error("Master Encryption Key: NOT configured")
            return False

        # Check dYdX
        if settings.dydx_v4.private_key:
            print_success("dYdX v4 Credentials: Configured")
        else:
            print_error("dYdX v4 Credentials: NOT configured")
            return False

        return True

    except Exception as e:
        print_error(f"Configuration validation failed: {e}")
        return False


def validate_configuration_issues() -> bool:
    """Check for configuration issues.

    Returns:
        True if no issues, False if issues found
    """
    print_section("Configuration Issues")

    issues = validate_configuration()

    if not issues:
        print_success("No configuration issues found")
        return True
    else:
        for issue in issues:
            if issue.startswith("ERROR"):
                print_error(issue)
            else:
                print_warning(issue)
        return len([i for i in issues if i.startswith("ERROR")]) == 0


def main() -> int:
    """Main validation function.

    Returns:
        0 if all validations pass, 1 otherwise
    """
    parser = argparse.ArgumentParser(
        description="Validate dYdX network configuration"
    )
    parser.add_argument(
        "--environment",
        default="development",
        help="Application environment (development, testing, staging, production)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print verbose output",
    )

    args = parser.parse_args()

    print_header("dYdX Network Configuration Validator")

    # Run validations
    results = {
        "Environment Variables": validate_environment_variables(),
        "Network Configuration": validate_network_configuration(args.environment),
        "Application Configuration": validate_application_configuration(),
        "Configuration Issues": validate_configuration_issues(),
    }

    # Print summary
    print_section("Summary")

    all_passed = True
    for check_name, passed in results.items():
        if passed:
            print_success(f"{check_name}: PASSED")
        else:
            print_error(f"{check_name}: FAILED")
            all_passed = False

    # Print final status
    print_header("Validation Result")
    if all_passed:
        print_success("✅ All validations passed! Configuration is ready.")
        print()
        return 0
    else:
        print_error("❌ Some validations failed. Please fix the issues above.")
        print()
        return 1


if __name__ == "__main__":
    sys.exit(main())
