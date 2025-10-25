"""
Database models for dYdX Trading Service.

This module defines SQLModel database schemas for users and positions,
providing type-safe database operations with Pydantic validation.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship


class User(SQLModel, table=True):
    """User model for storing trader information and encrypted credentials."""

    __tablename__ = "users"

    # Primary key - Ethereum wallet address
    wallet_address: str = Field(
        primary_key=True,
        max_length=42,
        description="Ethereum wallet address (42 characters with 0x prefix)"
    )

    # Unique webhook identifier for secure API access
    webhook_uuid: str = Field(
        unique=True,
        max_length=36,
        description="UUID for webhook authentication"
    )

    # Encrypted sensitive data
    encrypted_webhook_secret: Optional[str] = Field(
        max_length=500,
        description="Encrypted webhook secret for API authentication"
    )

    dydx_testnet_address: Optional[str] = Field(
        max_length=100,
        description="dYdX testnet wallet address (dydx1...)"
    )

    dydx_mainnet_address: Optional[str] = Field(
        max_length=100,
        description="dYdX mainnet wallet address (dydx1...)"
    )

    encrypted_dydx_mnemonic: Optional[str] = Field(
        max_length=500,
        description="Encrypted dYdX V4 mnemonic phrase (12-24 words)"
    )

    encrypted_dydx_testnet_mnemonic: Optional[str] = Field(
        max_length=500,
        description="Encrypted dYdX V4 testnet mnemonic phrase (24 words)"
    )

    encrypted_dydx_mainnet_mnemonic: Optional[str] = Field(
        max_length=500,
        description="Encrypted dYdX V4 mainnet mnemonic phrase (24 words)"
    )

    dydx_network_id: Optional[int] = Field(
        default=11155111,
        description="dYdX network ID (1 for mainnet, 11155111 for testnet)"
    )

    encrypted_telegram_token: Optional[str] = Field(
        max_length=500,
        description="Encrypted Telegram bot token for notifications"
    )

    encrypted_telegram_chat_id: Optional[str] = Field(
        max_length=500,
        description="Encrypted Telegram chat ID for notifications"
    )

    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Account creation timestamp"
    )

    # Relationships
    positions: List["Position"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    def __repr__(self) -> str:
        return f"<User(wallet_address='{self.wallet_address[:10]}...', webhook_uuid='{self.webhook_uuid}')>"


class Position(SQLModel, table=True):
    """Position model for tracking trading positions."""

    __tablename__ = "positions"

    # Primary key
    id: Optional[int] = Field(
        default=None,
        primary_key=True,
        description="Unique position identifier"
    )

    # Foreign key to user
    user_address: str = Field(
        foreign_key="users.wallet_address",
        max_length=42,
        description="Wallet address of the position owner"
    )

    # Trading pair information
    symbol: str = Field(
        max_length=20,
        description="Trading pair symbol (e.g., 'BTC-USD', 'ETH-USD')"
    )

    # Position side
    side: str = Field(
        max_length=10,
        description="Position side: BUY or SELL"
    )

    # Position status
    status: str = Field(
        max_length=20,
        default="open",
        description="Position status: open, closed, cancelled"
    )

    # Financial information
    entry_price: Decimal = Field(
        max_digits=20,
        decimal_places=10,
        description="Average entry price of the position"
    )

    size: Decimal = Field(
        max_digits=20,
        decimal_places=10,
        description="Position size in base currency"
    )

    # dYdX order identifiers
    dydx_order_id: Optional[str] = Field(
        max_length=100,
        description="dYdX order ID for the main position order"
    )

    tp_order_id: Optional[str] = Field(
        max_length=100,
        description="dYdX order ID for take-profit order"
    )

    sl_order_id: Optional[str] = Field(
        max_length=100,
        description="dYdX order ID for stop-loss order"
    )

    # Metadata
    opened_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Position opening timestamp"
    )

    # Relationships
    user: User = Relationship(back_populates="positions")

    def __repr__(self) -> str:
        return f"<Position(id={self.id}, symbol='{self.symbol}', status='{self.status}')>"

    # Computed properties for convenience
    @property
    def is_open(self) -> bool:
        """Check if position is currently open."""
        return self.status.lower() == "open"

    @property
    def is_closed(self) -> bool:
        """Check if position is closed."""
        return self.status.lower() == "closed"

    @property
    def notional_value(self) -> Decimal:
        """Calculate notional value of the position."""
        return self.entry_price * self.size

    def close_position(self) -> None:
        """Mark position as closed."""
        self.status = "closed"

    def cancel_position(self) -> None:
        """Mark position as cancelled."""
        self.status = "cancelled"


# Additional models for future phases

class Trade(SQLModel, table=True):
    """Trade model for detailed trade history (Phase 3)."""

    __tablename__ = "trades"

    id: Optional[int] = Field(default=None, primary_key=True)
    position_id: int = Field(foreign_key="positions.id")
    side: str = Field(max_length=10)  # "buy" or "sell"
    price: Decimal = Field(max_digits=20, decimal_places=10)
    amount: Decimal = Field(max_digits=20, decimal_places=10)
    fee: Decimal = Field(max_digits=10, decimal_places=5)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    position: Position = Relationship()


class WebhookEvent(SQLModel, table=True):
    """Webhook event model for tracking API events (Phase 4)."""

    __tablename__ = "webhook_events"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_address: str = Field(foreign_key="users.wallet_address")
    event_type: str = Field(max_length=50)
    payload: str = Field(max_length=10000)  # JSON payload as string
    processed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: User = Relationship()


# Database utility functions

def create_tables(engine) -> None:
    """Create all database tables.

    Args:
        engine: SQLAlchemy engine instance
    """
    SQLModel.metadata.create_all(engine)


def drop_tables(engine) -> None:
    """Drop all database tables (use with caution).

    Args:
        engine: SQLAlchemy engine instance
    """
    SQLModel.metadata.drop_all(engine)


# Validation helpers

def validate_wallet_address(address: str) -> bool:
    """Validate Ethereum wallet address format.

    Args:
        address: Wallet address to validate

    Returns:
        True if valid format
    """
    if not address:
        return False
    if not address.startswith('0x'):
        return False
    if len(address) != 42:
        return False
    try:
        int(address, 16)
        return True
    except ValueError:
        return False


def validate_symbol(symbol: str) -> bool:
    """Validate trading pair symbol format.

    Args:
        symbol: Trading symbol to validate

    Returns:
        True if valid format
    """
    if not symbol or len(symbol) < 3 or len(symbol) > 20:
        return False
    # Should contain a dash separating base and quote currency
    return '-' in symbol and len(symbol.split('-')) == 2


def validate_position_status(status: str) -> bool:
    """Validate position status.

    Args:
        status: Status to validate

    Returns:
        True if valid status
    """
    valid_statuses = {'open', 'closed', 'cancelled', 'pending'}
    return status.lower() in valid_statuses