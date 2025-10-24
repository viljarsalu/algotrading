# PNL Calculation Guide - dYdX Trading Bot

## Overview

This guide provides comprehensive instructions for calculating Profit & Loss (PNL) in the dYdX trading bot. PNL calculations are critical for trading analytics and performance tracking.

## Key Concepts

### Realized PNL
**Realized PNL** is the profit/loss from positions that have been closed. It's calculated from actual entry and exit prices.

```
Realized PNL = (Exit Price - Entry Price) × Position Size × (1 if LONG, -1 if SHORT)
```

### Unrealized PNL
**Unrealized PNL** is the profit/loss from open positions based on current market price.

```
Unrealized PNL = (Current Price - Entry Price) × Position Size × (1 if LONG, -1 if SHORT)
```

### Funding Fees
**Funding fees** are periodic payments between long and short traders on perpetual contracts.

```
Funding Fee = Position Size × Funding Rate × Time Period
```

---

## Data Sources

### 1. Fills Data (from dYdX API)

The dYdX API provides fills data which contains:
- Order ID
- Fill price
- Fill size
- Fill timestamp
- Side (BUY/SELL)
- Fee amount

**API Endpoint:**
```
GET /indexer/v4/fills?subaccountId={subaccount_id}&limit=100
```

**Response Format:**
```json
{
  "fills": [
    {
      "id": "fill_id",
      "orderId": "order_id",
      "subaccountId": "subaccount_id",
      "side": "BUY",
      "quantums": "1000000",
      "price": "50000000000",
      "quoteAmount": "50000000000000000",
      "eventId": "event_id",
      "transactionHash": "0x...",
      "createdAt": "2024-01-01T00:00:00Z",
      "createdAtHeight": "1000000"
    }
  ]
}
```

### 2. Position Data

Position data includes:
- Entry price
- Current price
- Position size
- Entry timestamp
- Status (open/closed)

### 3. Market Data

Current market prices from dYdX Indexer:
```
GET /indexer/v4/markets/{marketId}
```

---

## Implementation Guide

### Step 1: Fetch Fills Data

```python
from typing import List, Dict, Any
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


async def fetch_fills(
    dydx_client,
    subaccount_id: str,
    limit: int = 100,
    created_before_height: int = None,
) -> List[Dict[str, Any]]:
    """
    Fetch fills for a subaccount from dYdX API.

    Args:
        dydx_client: Authenticated dYdX client
        subaccount_id: Subaccount ID (format: "address.subaccount_number")
        limit: Maximum number of fills to fetch (max 100)
        created_before_height: Optional block height filter

    Returns:
        List of fill records
    """
    try:
        # Get fills from dYdX Indexer
        fills_response = await dydx_client.get_fills(
            subaccount_id=subaccount_id,
            limit=limit,
            created_before_height=created_before_height,
        )

        fills = fills_response.get("fills", [])
        logger.info(f"Fetched {len(fills)} fills for {subaccount_id}")

        return fills

    except Exception as e:
        logger.error(f"Failed to fetch fills: {e}")
        return []


def parse_fill_data(fill: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse raw fill data from dYdX API.

    Args:
        fill: Raw fill record from API

    Returns:
        Parsed fill data with converted values
    """
    # dYdX uses quantums (smallest unit)
    # 1 token = 1e6 quantums
    quantums_per_token = 1e6

    size = Decimal(fill.get("quantums", 0)) / Decimal(quantums_per_token)
    price = Decimal(fill.get("price", 0)) / Decimal(1e9)  # Price in quantums
    quote_amount = Decimal(fill.get("quoteAmount", 0)) / Decimal(1e18)

    return {
        "id": fill.get("id"),
        "order_id": fill.get("orderId"),
        "side": fill.get("side"),  # BUY or SELL
        "size": float(size),
        "price": float(price),
        "quote_amount": float(quote_amount),
        "timestamp": fill.get("createdAt"),
        "height": fill.get("createdAtHeight"),
    }
```

### Step 2: Calculate Entry and Exit Prices

```python
from typing import Optional, Tuple
from enum import Enum


class PositionSide(Enum):
    """Position side enumeration."""
    LONG = "LONG"
    SHORT = "SHORT"


def calculate_average_entry_price(
    fills: List[Dict[str, Any]], side: PositionSide
) -> float:
    """
    Calculate average entry price from fills.

    Args:
        fills: List of fill records
        side: Position side (LONG or SHORT)

    Returns:
        Average entry price
    """
    if not fills:
        return 0.0

    # Filter fills by side
    side_str = "BUY" if side == PositionSide.LONG else "SELL"
    entry_fills = [f for f in fills if f["side"] == side_str]

    if not entry_fills:
        return 0.0

    # Calculate weighted average price
    total_size = sum(f["size"] for f in entry_fills)
    total_cost = sum(f["size"] * f["price"] for f in entry_fills)

    if total_size == 0:
        return 0.0

    average_price = total_cost / total_size
    return average_price


def calculate_exit_price(
    fills: List[Dict[str, Any]], side: PositionSide
) -> float:
    """
    Calculate average exit price from fills.

    Args:
        fills: List of fill records
        side: Position side (LONG or SHORT)

    Returns:
        Average exit price
    """
    if not fills:
        return 0.0

    # Filter fills by opposite side (exit fills)
    side_str = "SELL" if side == PositionSide.LONG else "BUY"
    exit_fills = [f for f in fills if f["side"] == side_str]

    if not exit_fills:
        return 0.0

    # Calculate weighted average price
    total_size = sum(f["size"] for f in exit_fills)
    total_cost = sum(f["size"] * f["price"] for f in exit_fills)

    if total_size == 0:
        return 0.0

    average_price = total_cost / total_size
    return average_price
```

### Step 3: Calculate Realized PNL

```python
def calculate_realized_pnl(
    entry_price: float,
    exit_price: float,
    position_size: float,
    side: PositionSide,
    fees: float = 0.0,
) -> float:
    """
    Calculate realized PNL for a closed position.

    Args:
        entry_price: Average entry price
        exit_price: Average exit price
        position_size: Total position size
        side: Position side (LONG or SHORT)
        fees: Total trading fees paid

    Returns:
        Realized PNL (positive = profit, negative = loss)
    """
    if entry_price == 0 or position_size == 0:
        return 0.0

    # Calculate price difference
    price_diff = exit_price - entry_price

    # For LONG positions: profit if exit > entry
    # For SHORT positions: profit if exit < entry (so negate)
    if side == PositionSide.LONG:
        pnl = price_diff * position_size
    else:  # SHORT
        pnl = -price_diff * position_size

    # Subtract fees
    pnl -= fees

    return pnl


def calculate_pnl_percentage(
    entry_price: float,
    exit_price: float,
    side: PositionSide,
) -> float:
    """
    Calculate PNL as percentage of entry price.

    Args:
        entry_price: Average entry price
        exit_price: Average exit price
        side: Position side

    Returns:
        PNL percentage (e.g., 5.0 for 5% profit)
    """
    if entry_price == 0:
        return 0.0

    price_diff = exit_price - entry_price

    if side == PositionSide.LONG:
        pnl_pct = (price_diff / entry_price) * 100
    else:  # SHORT
        pnl_pct = (-price_diff / entry_price) * 100

    return pnl_pct
```

### Step 4: Calculate Unrealized PNL

```python
async def calculate_unrealized_pnl(
    dydx_client,
    position_id: str,
    entry_price: float,
    position_size: float,
    side: PositionSide,
    symbol: str,
) -> Tuple[float, float]:
    """
    Calculate unrealized PNL for an open position.

    Args:
        dydx_client: Authenticated dYdX client
        position_id: Position ID
        entry_price: Entry price
        position_size: Position size
        side: Position side
        symbol: Trading pair symbol (e.g., 'BTC-USD')

    Returns:
        Tuple of (unrealized_pnl, current_price)
    """
    try:
        # Get current market price
        market_data = await dydx_client.get_market_price(symbol)

        if not market_data.get("success"):
            logger.warning(f"Failed to get market price for {symbol}")
            return 0.0, 0.0

        current_price = float(market_data.get("price", 0))

        if current_price == 0 or entry_price == 0:
            return 0.0, current_price

        # Calculate unrealized PNL
        price_diff = current_price - entry_price

        if side == PositionSide.LONG:
            unrealized_pnl = price_diff * position_size
        else:  # SHORT
            unrealized_pnl = -price_diff * position_size

        return unrealized_pnl, current_price

    except Exception as e:
        logger.error(f"Failed to calculate unrealized PNL: {e}")
        return 0.0, 0.0
```

### Step 5: Calculate Total Fees

```python
def calculate_total_fees(fills: List[Dict[str, Any]]) -> float:
    """
    Calculate total trading fees from fills.

    Args:
        fills: List of fill records

    Returns:
        Total fees in quote currency
    """
    total_fees = 0.0

    for fill in fills:
        # dYdX includes fees in the quote amount
        # Fee calculation: size * price * fee_rate
        # Typical fee rate: 0.05% (0.0005)
        size = fill.get("size", 0)
        price = fill.get("price", 0)
        fee_rate = 0.0005  # 0.05% default

        fee = size * price * fee_rate
        total_fees += fee

    return total_fees


def calculate_funding_fees(
    position_size: float,
    funding_rate: float,
    hours_held: float,
) -> float:
    """
    Calculate funding fees for perpetual positions.

    Args:
        position_size: Position size
        funding_rate: Funding rate (typically 0.0001 to 0.001)
        hours_held: Number of hours position was held

    Returns:
        Funding fees paid
    """
    # Funding is typically paid every 8 hours
    # funding_fee = position_size * funding_rate * (hours_held / 8)
    funding_periods = hours_held / 8
    funding_fees = position_size * funding_rate * funding_periods

    return funding_fees
```

### Step 6: Complete PNL Calculation Function

```python
from dataclasses import dataclass
from datetime import datetime


@dataclass
class PNLSummary:
    """PNL calculation summary."""
    position_id: str
    symbol: str
    side: PositionSide
    entry_price: float
    exit_price: Optional[float]
    current_price: Optional[float]
    position_size: float
    entry_timestamp: datetime
    exit_timestamp: Optional[datetime]
    realized_pnl: float
    unrealized_pnl: float
    total_fees: float
    pnl_percentage: float
    status: str  # "open" or "closed"


async def calculate_complete_pnl(
    dydx_client,
    position_id: str,
    symbol: str,
    side: PositionSide,
    position_size: float,
    entry_timestamp: datetime,
    exit_timestamp: Optional[datetime] = None,
) -> PNLSummary:
    """
    Calculate complete PNL summary for a position.

    Args:
        dydx_client: Authenticated dYdX client
        position_id: Position ID
        symbol: Trading pair symbol
        side: Position side
        position_size: Position size
        entry_timestamp: Entry timestamp
        exit_timestamp: Exit timestamp (None if open)

    Returns:
        PNL summary with all calculations
    """
    try:
        # Fetch fills for this position
        fills = await fetch_fills(dydx_client, position_id)

        if not fills:
            logger.warning(f"No fills found for position {position_id}")
            return None

        # Parse fills
        parsed_fills = [parse_fill_data(f) for f in fills]

        # Calculate entry price
        entry_price = calculate_average_entry_price(parsed_fills, side)

        # Calculate total fees
        total_fees = calculate_total_fees(parsed_fills)

        # Determine if position is open or closed
        is_closed = exit_timestamp is not None

        if is_closed:
            # Calculate realized PNL
            exit_price = calculate_exit_price(parsed_fills, side)
            realized_pnl = calculate_realized_pnl(
                entry_price, exit_price, position_size, side, total_fees
            )
            pnl_percentage = calculate_pnl_percentage(
                entry_price, exit_price, side
            )
            unrealized_pnl = 0.0
            current_price = exit_price
            status = "closed"
        else:
            # Calculate unrealized PNL
            unrealized_pnl, current_price = await calculate_unrealized_pnl(
                dydx_client,
                position_id,
                entry_price,
                position_size,
                side,
                symbol,
            )
            realized_pnl = 0.0
            pnl_percentage = calculate_pnl_percentage(
                entry_price, current_price, side
            )
            status = "open"

        return PNLSummary(
            position_id=position_id,
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            exit_price=exit_price if is_closed else None,
            current_price=current_price,
            position_size=position_size,
            entry_timestamp=entry_timestamp,
            exit_timestamp=exit_timestamp,
            realized_pnl=realized_pnl,
            unrealized_pnl=unrealized_pnl,
            total_fees=total_fees,
            pnl_percentage=pnl_percentage,
            status=status,
        )

    except Exception as e:
        logger.error(f"Failed to calculate complete PNL: {e}")
        return None
```

---

## Database Schema

### Positions Table

```sql
CREATE TABLE positions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    symbol VARCHAR(20) NOT NULL,
    side VARCHAR(10) NOT NULL,  -- 'LONG' or 'SHORT'
    size DECIMAL(20, 8) NOT NULL,
    entry_price DECIMAL(20, 8) NOT NULL,
    exit_price DECIMAL(20, 8),
    current_price DECIMAL(20, 8),
    entry_timestamp TIMESTAMP NOT NULL,
    exit_timestamp TIMESTAMP,
    realized_pnl DECIMAL(20, 8),
    unrealized_pnl DECIMAL(20, 8),
    total_fees DECIMAL(20, 8),
    pnl_percentage DECIMAL(10, 4),
    status VARCHAR(20) NOT NULL,  -- 'open', 'closed', 'liquidated'
    dydx_order_id VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_positions_user_id ON positions(user_id);
CREATE INDEX idx_positions_status ON positions(status);
CREATE INDEX idx_positions_symbol ON positions(symbol);
```

### Fills Table

```sql
CREATE TABLE fills (
    id SERIAL PRIMARY KEY,
    position_id INTEGER NOT NULL REFERENCES positions(id),
    dydx_fill_id VARCHAR(100) UNIQUE NOT NULL,
    order_id VARCHAR(100) NOT NULL,
    side VARCHAR(10) NOT NULL,  -- 'BUY' or 'SELL'
    size DECIMAL(20, 8) NOT NULL,
    price DECIMAL(20, 8) NOT NULL,
    quote_amount DECIMAL(20, 8) NOT NULL,
    fee DECIMAL(20, 8),
    timestamp TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_fills_position_id ON fills(position_id);
CREATE INDEX idx_fills_order_id ON fills(order_id);
```

---

## API Endpoint Example

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/positions", tags=["positions"])


@router.get("/{position_id}/pnl")
async def get_position_pnl(
    position_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Get PNL summary for a position.

    Returns:
        {
            "position_id": 123,
            "symbol": "BTC-USD",
            "side": "LONG",
            "entry_price": 50000.00,
            "current_price": 52000.00,
            "position_size": 1.0,
            "realized_pnl": 0.00,
            "unrealized_pnl": 2000.00,
            "pnl_percentage": 4.0,
            "status": "open"
        }
    """
    try:
        # Get position from database
        position = db.query(Position).filter(
            Position.id == position_id,
            Position.user_id == current_user.id
        ).first()

        if not position:
            return {"error": "Position not found"}, 404

        # Calculate PNL
        dydx_client = await DydxClient.create_client()
        pnl_summary = await calculate_complete_pnl(
            dydx_client,
            position.dydx_order_id,
            position.symbol,
            PositionSide[position.side],
            position.size,
            position.entry_timestamp,
            position.exit_timestamp,
        )

        if not pnl_summary:
            return {"error": "Failed to calculate PNL"}, 500

        # Update database
        position.realized_pnl = pnl_summary.realized_pnl
        position.unrealized_pnl = pnl_summary.unrealized_pnl
        position.pnl_percentage = pnl_summary.pnl_percentage
        position.current_price = pnl_summary.current_price
        db.commit()

        return pnl_summary

    except Exception as e:
        logger.error(f"Failed to get position PNL: {e}")
        return {"error": str(e)}, 500


@router.get("/summary")
async def get_pnl_summary(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Get PNL summary for all user positions.

    Returns:
        {
            "total_realized_pnl": 5000.00,
            "total_unrealized_pnl": 2000.00,
            "total_pnl": 7000.00,
            "win_rate": 0.75,
            "positions_count": 10,
            "closed_positions_count": 8,
            "open_positions_count": 2
        }
    """
    try:
        # Get all positions
        positions = db.query(Position).filter(
            Position.user_id == current_user.id
        ).all()

        # Calculate totals
        total_realized = sum(p.realized_pnl or 0 for p in positions)
        total_unrealized = sum(p.unrealized_pnl or 0 for p in positions)
        total_pnl = total_realized + total_unrealized

        # Calculate win rate
        closed_positions = [p for p in positions if p.status == "closed"]
        winning_positions = [p for p in closed_positions if (p.realized_pnl or 0) > 0]
        win_rate = len(winning_positions) / len(closed_positions) if closed_positions else 0

        return {
            "total_realized_pnl": total_realized,
            "total_unrealized_pnl": total_unrealized,
            "total_pnl": total_pnl,
            "win_rate": win_rate,
            "positions_count": len(positions),
            "closed_positions_count": len(closed_positions),
            "open_positions_count": len(positions) - len(closed_positions),
        }

    except Exception as e:
        logger.error(f"Failed to get PNL summary: {e}")
        return {"error": str(e)}, 500
```

---

## Testing

```python
import pytest
from decimal import Decimal


def test_calculate_average_entry_price():
    """Test average entry price calculation."""
    fills = [
        {"side": "BUY", "size": 1.0, "price": 50000},
        {"side": "BUY", "size": 1.0, "price": 51000},
    ]

    entry_price = calculate_average_entry_price(fills, PositionSide.LONG)
    assert entry_price == 50500.0


def test_calculate_realized_pnl_long():
    """Test realized PNL for LONG position."""
    pnl = calculate_realized_pnl(
        entry_price=50000,
        exit_price=52000,
        position_size=1.0,
        side=PositionSide.LONG,
        fees=10.0,
    )
    assert pnl == 1990.0  # (52000 - 50000) * 1.0 - 10


def test_calculate_realized_pnl_short():
    """Test realized PNL for SHORT position."""
    pnl = calculate_realized_pnl(
        entry_price=50000,
        exit_price=48000,
        position_size=1.0,
        side=PositionSide.SHORT,
        fees=10.0,
    )
    assert pnl == 1990.0  # -(48000 - 50000) * 1.0 - 10


def test_calculate_pnl_percentage():
    """Test PNL percentage calculation."""
    pnl_pct = calculate_pnl_percentage(
        entry_price=50000,
        exit_price=52000,
        side=PositionSide.LONG,
    )
    assert pnl_pct == 4.0
```

---

## Summary

This guide covers:
1. ✅ Fetching fills data from dYdX API
2. ✅ Calculating average entry/exit prices
3. ✅ Computing realized and unrealized PNL
4. ✅ Handling fees and funding costs
5. ✅ Database schema for tracking
6. ✅ API endpoints for PNL queries
7. ✅ Testing strategies

Use these implementations as the foundation for your PNL calculation system.
