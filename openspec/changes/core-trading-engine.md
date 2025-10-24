# Core Trading Engine Integration - Change Proposal

## Overview
This change proposal implements Phase 3 of the dYdX Trading Bot Service: refactoring the trading logic to be stateless and operate on a per-user basis with full database integration.

## Problem Statement
The current trading engine lacks the stateless architecture required for multi-tenant operation. Functions need to be refactored to accept user-specific credentials as parameters, and state management must be moved from memory to persistent database storage.

## Goals
- Refactor all trading functions to be stateless and user-specific
- Implement database-centric position state management
- Enable isolated testing of trading engine with manual credential passing
- Ensure thread-safe operations for concurrent user trading activities

## Technical Specifications

### 1. Stateless Trading Architecture (`src/bot/`)

#### dYdX Client Module (`src/bot/dydx_client.py`)
```python
class DydxClient:
    @staticmethod
    async def create_client(mnemonic: str, network_id: int = 1) -> DydxClient:
        """Create authenticated dYdX client instance."""

    @staticmethod
    async def place_market_order(
        client: DydxClient,
        symbol: str,
        side: str,
        size: str,
        price: Optional[str] = None
    ) -> Dict[str, Any]:
        """Place market order with user-specific client."""

    @staticmethod
    async def place_limit_order(
        client: DydxClient,
        symbol: str,
        side: str,
        size: str,
        price: str,
        time_in_force: str = "GTT"
    ) -> Dict[str, Any]:
        """Place limit order with user-specific client."""

    @staticmethod
    async def cancel_order(client: DydxClient, order_id: str) -> bool:
        """Cancel existing order."""

    @staticmethod
    async def get_order_status(client: DydxClient, order_id: str) -> Dict[str, Any]:
        """Retrieve order status and details."""

    @staticmethod
    async def get_account_info(client: DydxClient) -> Dict[str, Any]:
        """Get account balances and positions."""
```

#### Telegram Manager (`src/bot/telegram_manager.py`)
```python
class TelegramManager:
    @staticmethod
    async def send_notification(
        token: str,
        chat_id: str,
        message: str,
        parse_mode: str = "HTML"
    ) -> bool:
        """Send notification to user's Telegram."""

    @staticmethod
    async def format_trade_notification(
        symbol: str,
        side: str,
        size: str,
        price: str,
        order_type: str,
        status: str
    ) -> str:
        """Format trade notification message."""

    @staticmethod
    async def format_position_notification(
        position: Position,
        action: str,
        reason: str = ""
    ) -> str:
        """Format position update notification."""
```

#### Risk Manager (`src/bot/risk_manager.py`)
```python
class RiskManager:
    @staticmethod
    def calculate_position_size(
        account_balance: float,
        risk_percentage: float,
        entry_price: float,
        stop_loss_price: float
    ) -> float:
        """Calculate safe position size based on risk management."""

    @staticmethod
    def validate_order_parameters(
        symbol: str,
        side: str,
        size: float,
        price: Optional[float] = None
    ) -> Tuple[bool, str]:
        """Validate order parameters for safety."""

    @staticmethod
    def calculate_take_profit_price(
        entry_price: float,
        stop_loss_price: float,
        risk_reward_ratio: float
    ) -> float:
        """Calculate take profit price based on risk/reward ratio."""

    @staticmethod
    def check_position_limits(
        current_positions: List[Position],
        new_position_size: float,
        max_positions: int = 10
    ) -> Tuple[bool, str]:
        """Check if new position would exceed limits."""
```

### 2. Database-Integrated State Management (`src/bot/state_manager.py`)

#### Position CRUD Operations
```python
class PositionManager:
    def __init__(self, db_session: Session):
        self.db = db_session

    async def create_position(
        self,
        user_address: str,
        symbol: str,
        side: str,
        entry_price: float,
        size: float,
        dydx_order_id: str,
        tp_order_id: str,
        sl_order_id: str
    ) -> Position:
        """Create new position record in database."""

    async def get_position(self, position_id: int) -> Optional[Position]:
        """Retrieve position by ID."""

    async def get_user_positions(
        self,
        user_address: str,
        status: Optional[str] = None
    ) -> List[Position]:
        """Get all positions for a user, optionally filtered by status."""

    async def update_position_status(
        self,
        position_id: int,
        status: str,
        **kwargs
    ) -> bool:
        """Update position status and other fields."""

    async def close_position(
        self,
        position_id: int,
        closing_price: float,
        pnl: float
    ) -> bool:
        """Mark position as closed with final details."""

    async def delete_position(self, position_id: int) -> bool:
        """Remove position record (for cancelled orders)."""
```

#### State Synchronization
```python
class StateSynchronizer:
    @staticmethod
    async def sync_position_with_dydx(
        position: Position,
        dydx_client: DydxClient
    ) -> Position:
        """Synchronize position state with dYdX."""

    @staticmethod
    async def validate_position_integrity(
        position: Position,
        expected_orders: List[str]
    ) -> Tuple[bool, str]:
        """Validate position data integrity."""

    @staticmethod
    async def cleanup_orphaned_positions(
        max_age_hours: int = 24
    ) -> int:
        """Clean up positions without corresponding dYdX orders."""
```

### 3. Trading Engine Integration

#### Main Trading Controller (`src/bot/trading_engine.py`)
```python
class TradingEngine:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.position_manager = PositionManager(db_session)

    async def execute_trade_signal(
        self,
        user_address: str,
        dydx_mnemonic: str,
        telegram_token: str,
        telegram_chat_id: str,
        signal_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute complete trade from signal to notification."""

    async def process_tradingview_signal(
        self,
        symbol: str,
        side: str,
        price: Optional[float],
        size: Optional[float],
        **kwargs
    ) -> Dict[str, Any]:
        """Process TradingView webhook signal."""

    async def manage_position_lifecycle(
        self,
        position_id: int,
        dydx_client: DydxClient
    ) -> Dict[str, Any]:
        """Monitor and manage single position lifecycle."""
```

## Implementation Plan

### Phase 3.1: Stateless Function Refactoring
1. **Refactor dYdX client** to accept credentials as parameters
2. **Update Telegram manager** for user-specific notifications
3. **Enhance risk manager** with user-specific calculations
4. **Remove global state** from all trading functions

### Phase 3.2: Database State Integration
1. **Implement PositionManager** with full CRUD operations
2. **Create StateSynchronizer** for dYdX state validation
3. **Add data integrity checks** and cleanup utilities
4. **Implement transaction safety** for state updates

### Phase 3.3: Trading Engine Assembly
1. **Build TradingEngine** as main coordination class
2. **Integrate all components** with dependency injection
3. **Add comprehensive error handling** and logging
4. **Implement retry logic** for network operations

### Phase 3.4: Isolated Testing Framework
1. **Create test credential factory** for safe testing
2. **Build mock dYdX client** for offline testing
3. **Implement integration tests** with test database
4. **Add performance benchmarks** for trading operations

## Dependencies

### Core Dependencies
- **dYdX Integration**: `dydx-v4-client` with stateless configuration
- **Database**: Enhanced SQLModel with relationship loading
- **Async Operations**: `asyncio` for concurrent position monitoring
- **Decimal Precision**: `decimal.Decimal` for financial calculations

### Testing Dependencies
- **Mock Framework**: `pytest-mock` for external service mocking
- **Test Database**: `pytest-asyncio` with test database isolation
- **Factory Pattern**: `factory-boy` for test data generation
- **Performance Testing**: `pytest-benchmark` for trading operation metrics

## Security Considerations

### Credential Handling
- **Runtime Decryption**: Credentials decrypted only when needed
- **Memory Security**: Secure handling of sensitive data in memory
- **Audit Logging**: Track all credential access for security monitoring
- **Automatic Cleanup**: Clear sensitive data from memory after use

### Trading Security
- **Position Validation**: Verify all trading parameters before execution
- **Rate Limiting**: Prevent excessive trading operations per user
- **Order Validation**: Ensure orders match user intent and risk limits
- **Emergency Stops**: Circuit breakers for unusual market conditions

### Database Security
- **Transaction Integrity**: Atomic operations for position updates
- **Concurrency Control**: Handle simultaneous position modifications
- **Data Consistency**: Validation before and after state changes
- **Backup Strategy**: Regular snapshots of trading state

## Testing Strategy

### Unit Tests
- **Stateless Functions**: Test each function with mock credentials
- **Database Operations**: Test CRUD operations in isolation
- **Risk Calculations**: Validate position sizing and limit calculations
- **Error Conditions**: Test failure scenarios and edge cases

### Integration Tests
- **End-to-End Trading**: Test complete trade execution flow
- **Database Consistency**: Verify state changes across operations
- **Concurrent Operations**: Test multiple users trading simultaneously
- **Network Resilience**: Handle dYdX API failures gracefully

### Performance Tests
- **Trading Speed**: Measure order placement and execution times
- **Database Performance**: Monitor query performance under load
- **Memory Usage**: Track memory consumption during trading operations
- **Concurrent Load**: Test system behavior with multiple active positions

## Success Criteria
- [ ] All trading functions accept user credentials as parameters
- [ ] Position state fully managed through database CRUD operations
- [ ] Trading engine passes isolated testing with manual credentials
- [ ] No global state or shared resources between users
- [ ] All tests pass with minimum 90% coverage
- [ ] Performance benchmarks meet latency requirements
- [ ] Database operations maintain ACID compliance

## Rollback Plan
- **Backward Compatibility**: New stateless functions don't break existing code
- **Gradual Migration**: Can roll back individual components if needed
- **Data Preservation**: Position data remains intact during rollback
- **Feature Flags**: Enable/disable trading engine components independently

## Future Dependencies
This phase enables:
- **Phase 4**: Secure Webhook Implementation
- **Phase 5**: Background Position Monitoring

## Open Questions
- **Risk Management Parameters**: Default risk/reward ratios and position limits
- **Order Types**: Which dYdX order types to support initially
- **Performance Requirements**: Target latency for order execution
- **Monitoring Strategy**: Real-time position monitoring implementation

## References
- Master Plan: Phase 3 - Core Trading Engine Integration
- Project Context: openspec/project.md
- Previous Proposals:
  - openspec/changes/foundation-database-setup.md
  - openspec/changes/web3-authentication-dashboard.md