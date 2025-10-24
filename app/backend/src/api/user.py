"""
User management API endpoints for credential management and dashboard data.

This module provides endpoints for managing user credentials, webhook information,
and dashboard data for authenticated users.
"""

import secrets
import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from eth_account import Account

from ..core.security import (
    get_credential_validator,
    get_aesgcm_manager,
    encrypt_sensitive_data,
    decrypt_sensitive_data
)
from ..db.database import get_database_manager
from ..db.models import User
from .auth import get_current_user
from ..bot.dydx_client import DydxClient

# Create router
router = APIRouter(prefix="/api/user", tags=["user-management"])

# Pydantic models for request/response
class CredentialsRequest(BaseModel):
    """Request model for saving/updating credentials."""
    dydx_mnemonic: Optional[str] = Field(None, description="dYdX wallet mnemonic phrase")
    telegram_token: Optional[str] = Field(None, description="Telegram bot token")
    telegram_chat_id: Optional[str] = Field(None, description="Telegram chat ID")

class CredentialsResponse(BaseModel):
    """Response model for credential operations."""
    message: str = Field(..., description="Operation result message")
    updated_fields: list[str] = Field(..., description="Fields that were updated")

class CredentialsStatusResponse(BaseModel):
    """Response model for credential status check."""
    dydx_configured: bool = Field(..., description="Whether dYdX credentials are set")
    telegram_configured: bool = Field(..., description="Whether Telegram credentials are set")
    webhook_configured: bool = Field(..., description="Whether webhook secret is set")

class DashboardResponse(BaseModel):
    """Response model for dashboard data."""
    user_profile: Dict[str, Any] = Field(..., description="User profile information")
    webhook_info: Dict[str, Any] = Field(..., description="Webhook configuration info")
    credentials_status: CredentialsStatusResponse = Field(..., description="Credentials status")

class WebhookInfoResponse(BaseModel):
    """Response model for webhook information."""
    webhook_url: str = Field(..., description="Webhook URL for API access")
    webhook_secret: str = Field(..., description="Webhook secret (display only)")
    instructions: str = Field(..., description="Setup instructions")

class WebhookSecretResponse(BaseModel):
    """Response model for webhook secret regeneration."""
    new_secret: str = Field(..., description="New webhook secret")

class AccountBalanceResponse(BaseModel):
    """Response model for account balance information."""
    success: bool = Field(..., description="Whether balance fetch was successful")
    equity: Optional[str] = Field(None, description="Total account equity (USD)")
    free_collateral: Optional[str] = Field(None, description="Free collateral available (USD)")
    margin_used: Optional[str] = Field(None, description="Margin currently used (USD)")
    open_positions_value: Optional[str] = Field(None, description="Total value of open positions (USD)")
    error: Optional[str] = Field(None, description="Error message if failed")

class UpdateCredentialsRequest(BaseModel):
    """Request model for partial credential updates."""
    dydx_mnemonic: Optional[str] = Field(None, description="dYdX wallet mnemonic phrase")
    telegram_token: Optional[str] = Field(None, description="Telegram bot token")
    telegram_chat_id: Optional[str] = Field(None, description="Telegram chat ID")

# API Endpoints

@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(current_user: str = Depends(get_current_user)) -> DashboardResponse:
    """Get user dashboard data including profile and webhook information.

    Args:
        current_user: Authenticated user's wallet address

    Returns:
        Dashboard data with user profile and webhook info
    """
    try:
        # Get database manager
        db_manager = get_database_manager()

        # Get user data
        user = await db_manager.get_user_by_wallet(current_user)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Prepare user profile
        user_profile = {
            "wallet_address": user.wallet_address,
            "webhook_uuid": user.webhook_uuid,
            "created_at": user.created_at.isoformat(),
            "account_age_days": (datetime.utcnow() - user.created_at).days
        }

        # Prepare webhook info
        webhook_info = {
            "webhook_uuid": user.webhook_uuid,
            "webhook_url": f"https://your-domain.com/api/webhook/{user.webhook_uuid}",  # TODO: Use actual domain
            "has_secret": user.encrypted_webhook_secret is not None,
            "secret_last_updated": None  # TODO: Add timestamp tracking
        }

        # Check credentials status
        credentials_status = CredentialsStatusResponse(
            dydx_configured=user.encrypted_dydx_mnemonic is not None,
            telegram_configured=user.encrypted_telegram_token is not None,
            webhook_configured=user.encrypted_webhook_secret is not None
        )

        return DashboardResponse(
            user_profile=user_profile,
            webhook_info=webhook_info,
            credentials_status=credentials_status
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load dashboard: {str(e)}"
        )

@router.post("/credentials", response_model=CredentialsResponse)
async def save_credentials(
    credentials: CredentialsRequest,
    current_user: str = Depends(get_current_user)
) -> CredentialsResponse:
    """Save user credentials with encryption.

    Args:
        credentials: User credentials to save
        current_user: Authenticated user's wallet address

    Returns:
        Confirmation of saved credentials
    """
    try:
        # Get credential validator
        validator = get_credential_validator()

        # Validate credentials if provided
        updated_fields = []

        if credentials.dydx_mnemonic:
            dydx_validation = validator.validate_dydx_credentials(
                current_user, credentials.dydx_mnemonic
            )
            if not dydx_validation['valid']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"dYdX credential validation failed: {'; '.join(dydx_validation['errors'])}"
                )
            updated_fields.append('dydx_mnemonic')

        if credentials.telegram_token and credentials.telegram_chat_id:
            telegram_validation = validator.validate_telegram_credentials(
                credentials.telegram_token, credentials.telegram_chat_id
            )
            if not telegram_validation['valid']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Telegram credential validation failed: {'; '.join(telegram_validation['errors'])}"
                )
            updated_fields.extend(['telegram_token', 'telegram_chat_id'])

        if not updated_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid credentials provided"
            )

        # Get database manager
        db_manager = get_database_manager()

        # Get existing user
        user = await db_manager.get_user_by_wallet(current_user)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Update user with encrypted credentials
        if credentials.dydx_mnemonic:
            user.encrypted_dydx_mnemonic = encrypt_sensitive_data(credentials.dydx_mnemonic)

        if credentials.telegram_token:
            user.encrypted_telegram_token = encrypt_sensitive_data(credentials.telegram_token)

        if credentials.telegram_chat_id:
            user.encrypted_telegram_chat_id = encrypt_sensitive_data(credentials.telegram_chat_id)

        # Save to database
        await db_manager.update_user(user)

        return CredentialsResponse(
            message=f"Successfully saved {len(updated_fields)} credential field(s)",
            updated_fields=updated_fields
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save credentials: {str(e)}"
        )

@router.put("/credentials", response_model=CredentialsResponse)
async def update_credentials(
    credentials: UpdateCredentialsRequest,
    current_user: str = Depends(get_current_user)
) -> CredentialsResponse:
    """Update specific user credentials.

    Args:
        credentials: Partial credential updates
        current_user: Authenticated user's wallet address

    Returns:
        Confirmation of updated credentials
    """
    # This is similar to save_credentials but for partial updates
    # We'll reuse the same logic but only update provided fields
    try:
        # Get credential validator
        validator = get_credential_validator()

        # Validate credentials if provided
        updated_fields = []

        if credentials.dydx_mnemonic:
            dydx_validation = validator.validate_dydx_credentials(
                current_user, credentials.dydx_mnemonic
            )
            if not dydx_validation['valid']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"dYdX credential validation failed: {'; '.join(dydx_validation['errors'])}"
                )
            updated_fields.append('dydx_mnemonic')

        if credentials.telegram_token and credentials.telegram_chat_id:
            telegram_validation = validator.validate_telegram_credentials(
                credentials.telegram_token, credentials.telegram_chat_id
            )
            if not telegram_validation['valid']:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Telegram credential validation failed: {'; '.join(telegram_validation['errors'])}"
                )
            updated_fields.extend(['telegram_token', 'telegram_chat_id'])

        if not updated_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid credentials provided for update"
            )

        # Get database manager
        db_manager = get_database_manager()

        # Get existing user
        user = await db_manager.get_user_by_wallet(current_user)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Update only provided fields
        if credentials.dydx_mnemonic:
            user.encrypted_dydx_mnemonic = encrypt_sensitive_data(credentials.dydx_mnemonic)

        if credentials.telegram_token:
            user.encrypted_telegram_token = encrypt_sensitive_data(credentials.telegram_token)

        if credentials.telegram_chat_id:
            user.encrypted_telegram_chat_id = encrypt_sensitive_data(credentials.telegram_chat_id)

        # Save to database
        await db_manager.update_user(user)

        return CredentialsResponse(
            message=f"Successfully updated {len(updated_fields)} credential field(s)",
            updated_fields=updated_fields
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update credentials: {str(e)}"
        )

@router.get("/credentials/status", response_model=CredentialsStatusResponse)
async def get_credentials_status(current_user: str = Depends(get_current_user)) -> CredentialsStatusResponse:
    """Get status of configured credentials.

    Args:
        current_user: Authenticated user's wallet address

    Returns:
        Status of all credential types
    """
    try:
        # Get database manager
        db_manager = get_database_manager()

        # Get user data
        user = await db_manager.get_user_by_wallet(current_user)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        return CredentialsStatusResponse(
            dydx_configured=user.encrypted_dydx_mnemonic is not None,
            telegram_configured=user.encrypted_telegram_token is not None and user.encrypted_telegram_chat_id is not None,
            webhook_configured=user.encrypted_webhook_secret is not None
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get credentials status: {str(e)}"
        )

@router.get("/webhook-info", response_model=WebhookInfoResponse)
async def get_webhook_info(current_user: str = Depends(get_current_user)) -> WebhookInfoResponse:
    """Get webhook information and setup instructions.

    Args:
        current_user: Authenticated user's wallet address

    Returns:
        Webhook URL, secret, and setup instructions
    """
    try:
        # Get database manager
        db_manager = get_database_manager()

        # Get user data
        user = await db_manager.get_user_by_wallet(current_user)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Decrypt webhook secret for display (one-time only)
        webhook_secret = "Not configured"
        if user.encrypted_webhook_secret:
            try:
                webhook_secret = decrypt_sensitive_data(user.encrypted_webhook_secret)
            except Exception:
                webhook_secret = "Error decrypting secret"

        # Generate webhook URL (TODO: Use actual domain)
        webhook_url = f"https://your-domain.com/api/webhook/{user.webhook_uuid}"

        # Setup instructions
        instructions = f"""
        To set up webhook notifications:

        1. Use this webhook URL: {webhook_url}
        2. Include the 'X-Webhook-Secret' header with value: {webhook_secret}
        3. Send POST requests with JSON payload for trading events
        4. The webhook UUID in the URL serves as additional authentication

        Note: Keep the webhook secret secure and do not expose it in client-side code.
        """

        return WebhookInfoResponse(
            webhook_url=webhook_url,
            webhook_secret=webhook_secret,
            instructions=instructions.strip()
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get webhook info: {str(e)}"
        )

@router.put("/webhook-secret", response_model=WebhookSecretResponse)
async def regenerate_webhook_secret(current_user: str = Depends(get_current_user)) -> WebhookSecretResponse:
    """Regenerate webhook secret (requires re-authentication).

    Args:
        current_user: Authenticated user's wallet address

    Returns:
        New webhook secret
    """
    try:
        # Generate new webhook secret
        new_secret = get_aesgcm_manager().generate_webhook_secret()

        # Encrypt the new secret
        encrypted_secret = encrypt_sensitive_data(new_secret)

        # Get database manager
        db_manager = get_database_manager()

        # Get existing user
        user = await db_manager.get_user_by_wallet(current_user)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Update webhook secret
        user.encrypted_webhook_secret = encrypted_secret

        # Save to database
        await db_manager.update_user(user)

        return WebhookSecretResponse(new_secret=new_secret)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to regenerate webhook secret: {str(e)}"
        )

@router.get("/account-balance", response_model=AccountBalanceResponse)
async def get_account_balance(current_user: str = Depends(get_current_user)) -> AccountBalanceResponse:
    """Get user's dYdX account balance and equity information.

    Args:
        current_user: Authenticated user's wallet address

    Returns:
        Account balance information including equity and free collateral
    """
    try:
        db_manager = get_database_manager()
        user = await db_manager.get_user_by_wallet(current_user)

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if not user.encrypted_dydx_mnemonic:
            return AccountBalanceResponse(
                success=False,
                error="dYdX credentials not configured. Please configure them first."
            )

        try:
            # Decrypt mnemonic and create private key
            decrypted_mnemonic = decrypt_sensitive_data(user.encrypted_dydx_mnemonic)
            account = Account.from_mnemonic(decrypted_mnemonic)
            private_key = account.key.hex()

            # Initialize dYdX client with user-specific private key
            dydx_client = await DydxClient.create_client(eth_private_key=private_key)
            
            # Fetch account info
            account_info = await DydxClient.get_account_info(dydx_client)

            if not account_info.get("success"):
                error_message = account_info.get("error", "Failed to fetch account info from dYdX")
                logger.error(f"dYdX API error for user {current_user}: {error_message}")
                return AccountBalanceResponse(success=False, error=error_message)

            # Extract balance data
            account_details = account_info.get("account", {})
            subaccount_details = account_info.get("subaccount", {})

            return AccountBalanceResponse(
                success=True,
                equity=account_details.get("equity"),
                free_collateral=account_details.get("freeCollateral"),
                margin_used=subaccount_details.get("marginUsed"),
                open_positions_value=account_details.get("openNotional"),
            )

        except Exception as e:
            logger.error(f"Failed to initialize dYdX client or fetch balance for user {current_user}: {e}")
            return AccountBalanceResponse(
                success=False,
                error=f"An unexpected error occurred while fetching balance: {str(e)}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Account balance endpoint error for user {current_user}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get account balance: {str(e)}"
        )