"""
Authentication API endpoints for Web3 wallet authentication.

This module provides endpoints for user authentication using Web3 wallet signatures,
including login, logout, verification, and user creation.
"""

import uuid
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
import jwt

from ..core.security import (
    JWT_ALGORITHM,
    get_aesgcm_manager,
    get_credential_validator,
    get_jwt_secret,
    get_web3_manager,
    encrypt_sensitive_data,
    verify_jwt_token,
)
from ..db.database import get_database_manager
from ..db.models import User

# Create router
router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Security scheme for JWT tokens
security = HTTPBearer(auto_error=False)

# JWT configuration
JWT_EXPIRATION_HOURS = 24

# Pydantic models for request/response
class LoginRequest(BaseModel):
    """Request model for user login."""
    wallet_address: str = Field(..., description="Ethereum wallet address")
    message: str = Field(..., description="Signed message")
    signature: str = Field(..., description="Wallet signature")

class LoginResponse(BaseModel):
    """Response model for successful login."""
    access_token: str = Field(..., description="JWT access token")
    user_data: Dict[str, Any] = Field(..., description="User information")
    expires_in: int = Field(..., description="Token expiration in seconds")

class CreateUserRequest(BaseModel):
    """Request model for user creation."""
    wallet_address: str = Field(..., description="Ethereum wallet address")
    message: str = Field(..., description="Message that was signed")
    signature: str = Field(..., description="Signature for verification")

class CreateUserResponse(BaseModel):
    """Response model for user creation."""
    webhook_uuid: str = Field(..., description="Unique webhook identifier")
    webhook_secret: str = Field(..., description="Webhook secret (display only)")

class LogoutResponse(BaseModel):
    """Response model for logout."""
    message: str = Field(..., description="Logout confirmation message")

class VerifyResponse(BaseModel):
    """Response model for token verification."""
    valid: bool = Field(..., description="Token validity status")
    user_address: Optional[str] = Field(None, description="User wallet address if valid")
    expires_at: Optional[str] = Field(None, description="Token expiration timestamp")

# Utility functions
def create_access_token(wallet_address: str) -> str:
    """Create JWT access token for authenticated user.

    Args:
        wallet_address: User's wallet address

    Returns:
        JWT token string
    """
    expiration = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    payload = {
        "sub": wallet_address,
        "exp": expiration,
        "iat": datetime.utcnow(),
        "type": "access"
    }

    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)

def verify_access_token(token: str) -> Optional[str]:
    """Verify JWT access token and extract wallet address.

    Args:
        token: JWT token string

    Returns:
        Wallet address if valid, None otherwise
    """
    payload = verify_jwt_token(token)
    if payload:
        return payload.get("sub")
    return None

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Dependency to get current authenticated user.

    Args:
        credentials: Bearer token credentials

    Returns:
        Wallet address of authenticated user

    Raises:
        HTTPException: If token is invalid or missing
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    wallet_address = verify_access_token(credentials.credentials)
    if not wallet_address:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return wallet_address

# API Endpoints

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest) -> LoginResponse:
    """Authenticate user with Web3 wallet signature.

    Args:
        request: Login request with wallet address, message, and signature

    Returns:
        Access token and user data

    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Get Web3 manager for signature verification
        import logging
        logger = logging.getLogger(__name__)
        print(f"DEBUG: Getting Web3 manager for wallet: {request.wallet_address}")
        logger.info(f"Getting Web3 manager for wallet: {request.wallet_address}")
        web3_manager = get_web3_manager()
        print("DEBUG: Web3 manager obtained successfully")
        logger.info("Web3 manager obtained successfully")

        # Verify the signature
        logger.info(f"Verifying signature for wallet: {request.wallet_address}")
        is_valid = web3_manager.verify_signature(
            request.wallet_address,
            request.message,
            request.signature
        )
        logger.info(f"Signature verification result: {is_valid}")

        if not is_valid:
            logger.info(f"Invalid signature for wallet: {request.wallet_address}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature"
            )

        # Get database manager
        logger.info("Getting database manager")
        db_manager = get_database_manager()
        logger.info("Database manager obtained successfully")

        # Check if user exists
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Checking if user exists: {request.wallet_address}")
        user = await db_manager.get_user_by_wallet(request.wallet_address)
        logger.info(f"User lookup result: {user is not None}")
        logger.info(f"User object: {user}")

        if not user:
            logger.info(f"User not found, returning 404 for: {request.wallet_address}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found. Please create account first."
            )

        # Create access token
        logger.info(f"Creating access token for wallet: {request.wallet_address}")
        access_token = create_access_token(request.wallet_address)
        logger.info("Access token created successfully")

        # Prepare user data response
        logger.info("Preparing user data response")
        user_data = {
            "wallet_address": user.wallet_address,
            "webhook_uuid": user.webhook_uuid,
            "created_at": user.created_at.isoformat(),
            "has_credentials": any([
                user.encrypted_dydx_mnemonic,
                user.encrypted_dydx_testnet_mnemonic,
                user.encrypted_dydx_mainnet_mnemonic,
                user.encrypted_telegram_token,
                user.encrypted_telegram_chat_id
            ])
        }
        logger.info(f"User data prepared: {user_data}")

        logger.info("Creating LoginResponse object")
        response = LoginResponse(
            access_token=access_token,
            user_data=user_data,
            expires_in=JWT_EXPIRATION_HOURS * 3600
        )
        logger.info("LoginResponse object created successfully")
        logger.info(f"Returning response for wallet: {request.wallet_address}")

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )

@router.post("/logout", response_model=LogoutResponse)
async def logout(current_user: str = Depends(get_current_user)) -> LogoutResponse:
    """Logout user (mainly for token invalidation on client side).

    Args:
        current_user: Authenticated user's wallet address

    Returns:
        Logout confirmation
    """
    # In a stateless JWT implementation, logout is handled client-side
    # by removing the token. This endpoint is mainly for consistency.

    return LogoutResponse(message="Successfully logged out")

@router.get("/verify", response_model=VerifyResponse)
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> VerifyResponse:
    """Verify JWT token validity.

    Args:
        credentials: Bearer token credentials

    Returns:
        Token verification status
    """
    if not credentials:
        return VerifyResponse(valid=False)

    wallet_address = verify_access_token(credentials.credentials)

    if wallet_address:
        # Calculate expiration time for response
        try:
            payload = jwt.decode(
                credentials.credentials,
                get_jwt_secret(),
                algorithms=[JWT_ALGORITHM],
            )
            expiration_timestamp = payload.get("exp")
            if expiration_timestamp:
                expires_at = datetime.fromtimestamp(expiration_timestamp).isoformat()
            else:
                expires_at = None

            return VerifyResponse(
                valid=True,
                user_address=wallet_address,
                expires_at=expires_at
            )
        except jwt.JWTError:
            pass

    return VerifyResponse(valid=False)

@router.get("/generate-message")
async def generate_message(wallet_address: str) -> Dict[str, str]:
    """Generate a message for wallet signature verification.

    Args:
        wallet_address: Wallet address for message generation

    Returns:
        Dict containing the message to be signed
    """
    try:
        # Get Web3 manager for message generation
        web3_manager = get_web3_manager()

        # Generate message for the wallet address
        message = web3_manager.generate_message(wallet_address)

        return {"message": message}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Message generation failed: {str(e)}"
        )

@router.post("/create-user", response_model=CreateUserResponse)
async def create_user(request: CreateUserRequest) -> CreateUserResponse:
    """Create new user account with Web3 wallet authentication.

    Args:
        request: User creation request with wallet address, message, and signature

    Returns:
        Webhook UUID and secret for API access

    Raises:
        HTTPException: If user already exists or creation fails
    """
    try:
        # Get Web3 manager for signature verification
        web3_manager = get_web3_manager()

        # Verify the signature against the provided message
        is_valid = web3_manager.verify_signature(
            request.wallet_address,
            request.message,
            request.signature
        )

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid signature for user creation"
            )

        # Get database manager
        db_manager = get_database_manager()

        # Check if user already exists
        existing_user = await db_manager.get_user_by_wallet(request.wallet_address)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already exists"
            )

        # Generate webhook credentials
        webhook_uuid = str(uuid.uuid4())
        webhook_secret = get_aesgcm_manager().generate_webhook_secret()

        # Encrypt webhook secret for storage
        encrypted_secret = encrypt_sensitive_data(webhook_secret)

        # Create new user
        new_user = User(
            wallet_address=request.wallet_address,
            webhook_uuid=webhook_uuid,
            encrypted_webhook_secret=encrypted_secret,
            created_at=datetime.utcnow()
        )

        # Save to database
        created_user = await db_manager.create_user(new_user)

        return CreateUserResponse(
            webhook_uuid=created_user.webhook_uuid,
            webhook_secret=webhook_secret  # Only returned once during creation
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"User creation failed: {str(e)}"
        )