# Phase 2 OpenSpec Proposals - dYdX Trading Bot

## Overview

This document contains formal OpenSpec proposals for 5 interconnected tasks in Phase 2. Each proposal follows the OpenSpec format with clear requirements, scenarios, and implementation tasks.

---

# Task 1: Verify Test Exchange Setup

## Proposal

### Why
Network configuration is implicit in environment settings, making it easy to misconfigure. We need explicit validation and documentation to prevent accidental mainnet trades during development.

### What Changes
- Add `NetworkValidator` class for testnet/mainnet validation
- Implement environment-based network selection
- Add safety checks preventing mainnet in non-production
- Create comprehensive documentation
- Add health check endpoint confirming connectivity
- Create environment validation script

### Impact
- **Affected specs**: Network Configuration, Health Monitoring
- **Affected code**: `src/bot/dydx_client.py`, `src/core/config.py`, `src/main.py`
- **Breaking changes**: None

### Requirements

#### Requirement: Network Configuration Validation
The system SHALL validate network configuration at startup.

**Scenarios:**
- **WHEN** application starts in development **THEN** automatically use testnet
- **WHEN** application starts in production **THEN** automatically use mainnet
- **WHEN** production attempts testnet **THEN** raise error and refuse startup
- **WHEN** development uses mainnet **THEN** log warning but allow with confirmation

#### Requirement: Network Health Check
The system SHALL provide health check endpoint confirming connectivity.

**Scenarios:**
- **WHEN** GET `/health/network` called **THEN** return network type, chain ID, status
- **WHEN** network unreachable **THEN** return 503 with error details
- **WHEN** network mismatch detected **THEN** return 400 with configuration error

---

# Task 2: Enhance Dashboard with Real-time WebSocket Data

## Proposal

### Why
Current dashboard uses HTTP polling every 15 seconds. dYdX provides native WebSocket feeds for real-time updates. Implementing WebSocket subscriptions will provide instant updates and reduce API load.

### What Changes
- Implement `WebSocketManager` for dYdX Indexer WebSocket
- Subscribe to `v4_subaccounts` for account balance updates
- Subscribe to `v4_orders` for order status changes
- Subscribe to `v4_trades` for trade fill notifications
- Add connection heartbeat handling (ping/pong every 30s)
- Implement automatic reconnection with exponential backoff
- Add fallback to HTTP polling if WebSocket fails
- Update dashboard frontend for real-time updates
- Add connection status indicator

### Impact
- **Affected specs**: Dashboard, Real-time Data, WebSocket Integration
- **Affected code**: `src/api/websockets.py`, `src/bot/websocket_manager.py`, frontend
- **Breaking changes**: None (backward compatible)

### Requirements

#### Requirement: WebSocket Connection Management
The system SHALL establish and maintain WebSocket connections.

**Scenarios:**
- **WHEN** dashboard connects **THEN** establish WebSocket to dYdX Indexer
- **WHEN** WebSocket receives heartbeat ping **THEN** respond with pong within 10 seconds
- **WHEN** WebSocket disconnects **THEN** attempt reconnection with exponential backoff
- **WHEN** reconnection fails after 5 attempts **THEN** fallback to HTTP polling

#### Requirement: Real-time Account Updates
The system SHALL stream account balance and position changes.

**Scenarios:**
- **WHEN** WebSocket connects **THEN** subscribe to v4_subaccounts channel
- **WHEN** account balance changes **THEN** send update to dashboard within 100ms
- **WHEN** new position opened **THEN** send position data to dashboard

#### Requirement: Real-time Order Updates
The system SHALL stream order status changes.

**Scenarios:**
- **WHEN** order placed **THEN** subscribe to v4_orders channel
- **WHEN** order status changes **THEN** send update to dashboard immediately
- **WHEN** order filled **THEN** send fill notification with price and size

---

# Task 3: Audit & Align Trading Logic with Best Practices

## Proposal

### Why
Trading engine needs verification against dYdX v4 best practices. Order lifecycle, position management, and error handling should be audited for reliability.

### What Changes
- Audit order lifecycle tracking
- Verify time_in_force parameter usage (GTT, IOC, FOK)
- Validate position entry/exit logic
- Check TP/SL order placement and cancellation
- Verify gas fee estimation
- Ensure order rejection handling
- Add comprehensive logging
- Create audit report
- Add unit tests for edge cases

### Impact
- **Affected specs**: Trading Engine, Order Management, Position Management
- **Affected code**: `src/bot/dydx_client.py`, `src/workers/dydx_order_monitor.py`
- **Breaking changes**: None (improvements only)

### Requirements

#### Requirement: Order Lifecycle Validation
The system SHALL correctly track orders through complete lifecycle.

**Scenarios:**
- **WHEN** order placed **THEN** track as PENDING
- **WHEN** order filled **THEN** update to FILLED
- **WHEN** order partially filled **THEN** update to PARTIALLY_FILLED
- **WHEN** order cancelled **THEN** update to CANCELLED
- **WHEN** order rejected **THEN** update to REJECTED with error reason

#### Requirement: Time-in-Force Parameter Validation
The system SHALL correctly use time_in_force parameters.

**Scenarios:**
- **WHEN** GTT specified **THEN** order remains active until expiration
- **WHEN** IOC specified **THEN** order fills immediately or cancels
- **WHEN** FOK specified **THEN** order fills completely or cancels
- **WHEN** invalid time_in_force provided **THEN** reject with clear error

---

# Task 4: Implement Advanced Position & Order Management

## Proposal

### Why
Users need visibility into historical PNL, ability to cancel all orders, order history with filters, and detailed position information for comprehensive trading analytics.

### What Changes
- Implement PNL calculation from fills data
- Add "cancel all open orders" functionality
- Implement order history view with pagination
- Add position summary with realized/unrealized PNL
- Create dashboard components for positions and orders
- Add position filtering and sorting
- Add detailed position information display

### Impact
- **Affected specs**: Position Management, Order Management, Dashboard
- **Affected code**: `src/bot/position_manager.py`, `src/api/orders.py`
- **Breaking changes**: None
- **Database changes**: Add PNL tracking fields to positions table
- **API changes**: New endpoints for order management and position details

### Requirements

#### Requirement: Historical PNL Calculation
The system SHALL calculate realized and unrealized PNL.

**Scenarios:**
- **WHEN** position closed **THEN** calculate realized PNL from entry and exit prices
- **WHEN** position open **THEN** calculate unrealized PNL from current market price
- **WHEN** partial fills occur **THEN** calculate PNL for filled portion
- **WHEN** multiple fills occur **THEN** aggregate PNL correctly

#### Requirement: Order Management
The system SHALL provide comprehensive order management.

**Scenarios:**
- **WHEN** user requests cancel all **THEN** cancel all open orders
- **WHEN** order history requested **THEN** return last 50 orders with pagination
- **WHEN** filter applied **THEN** filter by status, symbol, or date range
- **WHEN** order details requested **THEN** return fill prices and partial fill info

---

# Task 5: Comprehensive Error Handling & Resilience

## Proposal

### Why
Application needs production-grade resilience. API errors, rate limits, and connection issues should be handled gracefully with clear user feedback and automatic recovery.

### What Changes
- Enhance error categorization and classification
- Implement rate limit detection and handling
- Add circuit breaker pattern for failing endpoints
- Implement graceful degradation
- Add user-facing error notifications
- Implement retry logic with exponential backoff
- Add error rate metrics endpoint
- Add comprehensive error logging
- Create error recovery strategies

### Impact
- **Affected specs**: Error Handling, Resilience, Monitoring
- **Affected code**: `src/core/error_handler.py`, `src/workers/error_handler.py`, API endpoints
- **Breaking changes**: None
- **Database changes**: Add error metrics table
- **API changes**: New error metrics endpoint

### Requirements

#### Requirement: API Error Handling
The system SHALL catch and handle all dYdX API errors gracefully.

**Scenarios:**
- **WHEN** API returns 400 **THEN** log error and return meaningful message
- **WHEN** API returns 429 (rate limited) **THEN** queue request and retry
- **WHEN** API returns 500 **THEN** retry with exponential backoff
- **WHEN** API timeout occurs **THEN** retry up to 3 times then fail gracefully

#### Requirement: Rate Limiting
The system SHALL detect and handle rate limiting gracefully.

**Scenarios:**
- **WHEN** rate limit detected **THEN** queue requests and process sequentially
- **WHEN** rate limit status available **THEN** add to health check
- **WHEN** rate limit exceeded **THEN** notify user with estimated wait time

#### Requirement: Connection Resilience
The system SHALL maintain functionality during connection issues.

**Scenarios:**
- **WHEN** WebSocket fails **THEN** automatically fallback to HTTP polling
- **WHEN** connection restored **THEN** resume WebSocket subscriptions
- **WHEN** circuit breaker open **THEN** use cached data or fallback endpoint
- **WHEN** multiple errors occur **THEN** implement exponential backoff

---

## Implementation Sequence

**Recommended order:**
1. Task 1 (2-3 hours) - Foundation for safe network configuration
2. Task 3 (3-4 hours) - Verify trading logic before enhancement
3. Task 5 (2-3 hours) - Error handling foundation for all tasks
4. Task 2 (6-8 hours) - Real-time updates with solid error handling
5. Task 4 (6-8 hours) - Advanced features on stable foundation

**Total estimated effort:** 20-27 hours
