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
    dydx_address: Optional[str] = Field(None, description="dYdX wallet address (deprecated, use testnet/mainnet specific)")
    dydx_testnet_address: Optional[str] = Field(None, description="dYdX testnet wallet address")
    dydx_mainnet_address: Optional[str] = Field(None, description="dYdX mainnet wallet address")
    dydx_mnemonic: Optional[str] = Field(None, description="dYdX V4 mnemonic phrase (12-24 words)")
    dydx_testnet_mnemonic: Optional[str] = Field(None, description="dYdX V4 testnet mnemonic phrase (12-24 words)")
    dydx_mainnet_mnemonic: Optional[str] = Field(None, description="dYdX V4 mainnet mnemonic phrase (12-24 words)")
    dydx_network_id: Optional[int] = Field(None, description="dYdX network ID (1 for mainnet, 11155111 for testnet)")
    telegram_token: Optional[str] = Field(None, description="Telegram bot token")
    telegram_chat_id: Optional[str] = Field(None, description="Telegram chat ID")

class CredentialsResponse(BaseModel):
    """Response model for credential operations."""
    message: str = Field(..., description="Operation result message")
    updated_fields: list[str] = Field(..., description="Fields that were updated")

class CredentialsStatusResponse(BaseModel):
    """Response model for credential status check."""
    dydx_configured: bool = Field(..., description="Whether dYdX mnemonic is configured")
    dydx_testnet_configured: bool = Field(..., description="Whether dYdX testnet mnemonic is configured")
    dydx_mainnet_configured: bool = Field(..., description="Whether dYdX mainnet mnemonic is configured")
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

class WebhookSecretResponse(BaseModel):
    """Response model for webhook secret regeneration."""
    new_secret: str = Field(..., description="New webhook secret")

class AccountBalanceResponse(BaseModel):
    """Response model for account balance."""
    success: bool = Field(..., description="Whether the request was successful")
    equity: Optional[str] = Field(None, description="Total account equity (USD)")
    free_collateral: Optional[str] = Field(None, description="Free collateral available (USD)")
    margin_used: Optional[str] = Field(None, description="Margin currently used (USD)")
    open_positions_value: Optional[str] = Field(None, description="Total value of open positions (USD)")
    error: Optional[str] = Field(None, description="Error message if failed")

class PositionData(BaseModel):
    """Model for a single position."""
    id: int = Field(..., description="Position ID")
    symbol: str = Field(..., description="Trading pair symbol")
    side: str = Field(..., description="Position side (BUY or SELL)")
    entry_price: str = Field(..., description="Entry price")
    size: str = Field(..., description="Position size")
    status: str = Field(..., description="Position status (open, closed, etc)")
    opened_at: str = Field(..., description="When position was opened")
    dydx_order_id: Optional[str] = Field(None, description="dYdX order ID")

class OpenPositionsResponse(BaseModel):
    """Response model for open positions."""
    success: bool = Field(..., description="Whether the request was successful")
    positions: list[PositionData] = Field(default_factory=list, description="List of open positions")
    error: Optional[str] = Field(None, description="Error message if failed")

# API Endpoints

@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(current_user: str = Depends(get_current_user)) -> DashboardResponse:
    """Get user dashboard data including profile and webhook information."""
    try:
        db_manager = get_database_manager()
        user = await db_manager.get_user_by_wallet(current_user)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        user_profile = {
            "wallet_address": user.wallet_address,
            "webhook_uuid": user.webhook_uuid,
            "created_at": user.created_at.isoformat(),
            "account_age_days": (datetime.utcnow() - user.created_at).days,
            "dydx_testnet_address": user.dydx_testnet_address,
            "dydx_mainnet_address": user.dydx_mainnet_address
        }

        webhook_info = {
            "webhook_uuid": user.webhook_uuid,
            "webhook_url": f"/api/webhooks/signal/{user.webhook_uuid}",  # Relative URL
            "has_secret": user.encrypted_webhook_secret is not None,
        }

        credentials_status = CredentialsStatusResponse(
            dydx_configured=(user.encrypted_dydx_mnemonic is not None or user.encrypted_dydx_testnet_mnemonic is not None or user.encrypted_dydx_mainnet_mnemonic is not None),
            dydx_testnet_configured=user.encrypted_dydx_testnet_mnemonic is not None,
            dydx_mainnet_configured=user.encrypted_dydx_mainnet_mnemonic is not None,
            telegram_configured=(user.encrypted_telegram_token is not None and user.encrypted_telegram_chat_id is not None),
            webhook_configured=user.encrypted_webhook_secret is not None
        )

        return DashboardResponse(
            user_profile=user_profile,
            webhook_info=webhook_info,
            credentials_status=credentials_status
        )
    except Exception as e:
        logger.error(f"Failed to load dashboard for user {current_user}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to load dashboard data.")

@router.post("/credentials", response_model=CredentialsResponse)
async def save_credentials(
    credentials: CredentialsRequest,
    current_user: str = Depends(get_current_user)
) -> CredentialsResponse:
    """Save or update user credentials with encryption."""
    try:
        validator = get_credential_validator()
        updated_fields = []

        # Handle dYdX testnet credentials
        if credentials.dydx_testnet_address or credentials.dydx_testnet_mnemonic:
            if not (credentials.dydx_testnet_address and credentials.dydx_testnet_mnemonic):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Both testnet address and mnemonic are required")
            dydx_validation = validator.validate_dydx_mnemonic(credentials.dydx_testnet_mnemonic)
            if not dydx_validation['valid']:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"dYdX testnet mnemonic validation failed: {'; '.join(dydx_validation['errors'])}")
            updated_fields.extend(['dydx_testnet_address', 'dydx_testnet_mnemonic'])

        # Handle dYdX mainnet credentials
        if credentials.dydx_mainnet_address or credentials.dydx_mainnet_mnemonic:
            if not (credentials.dydx_mainnet_address and credentials.dydx_mainnet_mnemonic):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Both mainnet address and mnemonic are required")
            dydx_validation = validator.validate_dydx_mnemonic(credentials.dydx_mainnet_mnemonic)
            if not dydx_validation['valid']:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"dYdX mainnet mnemonic validation failed: {'; '.join(dydx_validation['errors'])}")
            updated_fields.extend(['dydx_mainnet_address', 'dydx_mainnet_mnemonic'])

        if credentials.dydx_network_id:
            # Validate network ID
            valid_networks = [1, 11155111]  # mainnet, testnet
            if credentials.dydx_network_id not in valid_networks:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid network ID. Must be 1 (mainnet) or 11155111 (testnet)")
            updated_fields.append('dydx_network_id')

        if credentials.telegram_token and credentials.telegram_chat_id:
            telegram_validation = validator.validate_telegram_credentials(credentials.telegram_token, credentials.telegram_chat_id)
            if not telegram_validation['valid']:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Telegram credential validation failed: {'; '.join(telegram_validation['errors'])}")
            updated_fields.extend(['telegram_token', 'telegram_chat_id'])

        if not updated_fields:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No valid credentials provided")

        db_manager = get_database_manager()
        user = await db_manager.get_user_by_wallet(current_user)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if 'dydx_testnet_address' in updated_fields:
            user.dydx_testnet_address = credentials.dydx_testnet_address
        if 'dydx_mainnet_address' in updated_fields:
            user.dydx_mainnet_address = credentials.dydx_mainnet_address
        if 'dydx_testnet_mnemonic' in updated_fields:
            user.encrypted_dydx_testnet_mnemonic = encrypt_sensitive_data(credentials.dydx_testnet_mnemonic)
        if 'dydx_mainnet_mnemonic' in updated_fields:
            user.encrypted_dydx_mainnet_mnemonic = encrypt_sensitive_data(credentials.dydx_mainnet_mnemonic)
        if 'dydx_network_id' in updated_fields:
            user.dydx_network_id = credentials.dydx_network_id
        if 'telegram_token' in updated_fields:
            user.encrypted_telegram_token = encrypt_sensitive_data(credentials.telegram_token)
        if 'telegram_chat_id' in updated_fields:
            user.encrypted_telegram_chat_id = encrypt_sensitive_data(credentials.telegram_chat_id)

        await db_manager.update_user(user)

        return CredentialsResponse(
            message=f"Successfully saved {len(updated_fields)} credential field(s)",
            updated_fields=updated_fields
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save credentials for user {current_user}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to save credentials: {str(e)}")

@router.get("/credentials/status", response_model=CredentialsStatusResponse)
async def get_credentials_status(current_user: str = Depends(get_current_user)) -> CredentialsStatusResponse:
    """Get status of configured credentials."""
    try:
        db_manager = get_database_manager()
        user = await db_manager.get_user_by_wallet(current_user)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        return CredentialsStatusResponse(
            dydx_configured=(user.encrypted_dydx_mnemonic is not None or user.encrypted_dydx_testnet_mnemonic is not None or user.encrypted_dydx_mainnet_mnemonic is not None),
            dydx_testnet_configured=user.encrypted_dydx_testnet_mnemonic is not None,
            dydx_mainnet_configured=user.encrypted_dydx_mainnet_mnemonic is not None,
            telegram_configured=user.encrypted_telegram_token is not None and user.encrypted_telegram_chat_id is not None,
            webhook_configured=user.encrypted_webhook_secret is not None
        )
    except Exception as e:
        logger.error(f"Failed to get credentials status for user {current_user}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get credentials status.")

@router.get("/webhook-info", response_model=WebhookInfoResponse)
async def get_webhook_info(current_user: str = Depends(get_current_user)) -> WebhookInfoResponse:
    """Get webhook information and setup instructions."""
    try:
        db_manager = get_database_manager()
        user = await db_manager.get_user_by_wallet(current_user)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        webhook_secret = "Not configured"
        if user.encrypted_webhook_secret:
            try:
                webhook_secret = decrypt_sensitive_data(user.encrypted_webhook_secret)
            except Exception:
                webhook_secret = "Error decrypting secret"

        webhook_url = f"/api/webhooks/signal/{user.webhook_uuid}"  # Relative URL

        return WebhookInfoResponse(
            webhook_url=webhook_url,
            webhook_secret=webhook_secret,
        )
    except Exception as e:
        logger.error(f"Failed to get webhook info for user {current_user}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get webhook info.")

@router.put("/webhook-secret", response_model=WebhookSecretResponse)
async def regenerate_webhook_secret(current_user: str = Depends(get_current_user)) -> WebhookSecretResponse:
    """Regenerate webhook secret."""
    try:
        new_secret = get_aesgcm_manager().generate_webhook_secret()
        encrypted_secret = encrypt_sensitive_data(new_secret)

        db_manager = get_database_manager()
        user = await db_manager.get_user_by_wallet(current_user)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        user.encrypted_webhook_secret = encrypted_secret
        await db_manager.update_user(user)

        return WebhookSecretResponse(new_secret=new_secret)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to regenerate webhook secret: {str(e)}")

@router.get("/account-balance", response_model=AccountBalanceResponse)
async def get_account_balance(current_user: str = Depends(get_current_user)) -> AccountBalanceResponse:
    """Get user's dYdX account balance and equity information."""
    try:
        db_manager = get_database_manager()
        user = await db_manager.get_user_by_wallet(current_user)

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if not user.encrypted_dydx_private_key:
            return AccountBalanceResponse(
                success=False,
                error="dYdX mnemonic not configured. Please configure it first."
            )

        try:
            mnemonic = decrypt_sensitive_data(user.encrypted_dydx_private_key)
            dydx_client = await DydxClient.create_client(mnemonic=mnemonic)
            
            account_info = await DydxClient.get_account_info(dydx_client)

            if not account_info.get("success"):
                error_message = account_info.get("error", "Failed to fetch account info from dYdX")
                logger.error(f"dYdX API error for user {current_user}: {error_message}")
                return AccountBalanceResponse(success=False, error=error_message)

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
                error=f"Failed to fetch balance. Ensure your mnemonic is valid: {str(e)}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Account balance endpoint error for user {current_user}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get account balance: {str(e)}"
        )

@router.get("/positions", response_model=OpenPositionsResponse)
async def get_open_positions(current_user: str = Depends(get_current_user)) -> OpenPositionsResponse:
    """Get user's open positions from database."""
    try:
        db_manager = get_database_manager()
        user = await db_manager.get_user_by_wallet(current_user)

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Get open positions from database
        positions = await db_manager.get_open_positions(current_user)
        
        position_list = [
            PositionData(
                id=pos.id,
                symbol=pos.symbol,
                side=pos.side,
                entry_price=str(pos.entry_price),
                size=str(pos.size),
                status=pos.status,
                opened_at=pos.opened_at.isoformat() if pos.opened_at else "",
                dydx_order_id=pos.dydx_order_id
            )
            for pos in positions
        ]

        return OpenPositionsResponse(
            success=True,
            positions=position_list
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get open positions for user {current_user}: {e}")
        return OpenPositionsResponse(
            success=False,
            positions=[],
            error=f"Failed to get open positions: {str(e)}"
        )