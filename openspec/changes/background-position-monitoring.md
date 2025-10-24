# Background Position Monitoring Service - Change Proposal

## Overview
This change proposal implements Phase 5 of the dYdX Trading Bot Service: creating a reliable background monitoring system that automatically tracks and closes positions across all users with real-time dYdX synchronization.

## Problem Statement
Open positions require continuous monitoring to detect when take-profit (TP) or stop-loss (SL) orders are filled, ensuring timely position closure and user notification. The current system lacks automated background processes for production-scale position management.

## Goals
- Implement background worker for continuous position monitoring
- Enable real-time synchronization with dYdX order status
- Automate position closure when TP/SL orders are filled
- Provide reliable notification system for position lifecycle events

## Technical Specifications

### 1. Background Worker Architecture

#### Worker Process Management (`src/workers/position_monitor.py`)
```python
class PositionMonitorWorker:
    def __init__(
        self,
        db_session: Session,
        monitoring_interval: int = 30,
        max_workers: int = 5
    ):
        self.db = db_session
        self.monitoring_interval = monitoring_interval
        self.max_workers = max_workers
        self.is_running = False

    async def start_monitoring(self) -> None:
        """Start the background monitoring process."""

    async def stop_monitoring(self) -> None:
        """Gracefully stop the monitoring process."""

    async def monitoring_loop(self) -> None:
        """Main monitoring loop with error handling and recovery."""

    async def process_open_positions(self) -> List[Position]:
        """Query database for all open positions across users."""

    async def check_position_batch(
        self,
        positions: List[Position]
    ) -> List[Dict[str, Any]]:
        """Check multiple positions concurrently for efficiency."""
```

#### Worker Lifecycle Management
```python
class WorkerManager:
    @staticmethod
    async def initialize_worker(
        app: FastAPI,
        db_url: str,
        config: Dict[str, Any]
    ) -> PositionMonitorWorker:
        """Initialize and start worker with application."""

    @staticmethod
    async def graceful_shutdown(app: FastAPI) -> None:
        """Handle graceful shutdown of worker processes."""

    @staticmethod
    async def health_check() -> Dict[str, Any]:
        """Monitor worker health and performance metrics."""
```

### 2. Position Monitoring Logic

#### dYdX Order Status Checking
```python
class DydxOrderMonitor:
    @staticmethod
    async def check_order_status_batch(
        orders: List[Dict[str, str]],
        credentials: Dict[str, str]
    ) -> Dict[str, Dict[str, Any]]:
        """Check status of multiple dYdX orders efficiently."""

    @staticmethod
    async def get_order_details(
        client: DydxClient,
        order_id: str
    ) -> Dict[str, Any]:
        """Get detailed order information from dYdX."""

    @staticmethod
    async def cancel_order_if_exists(
        client: DydxClient,
        order_id: str
    ) -> bool:
        """Safely cancel order with existence check."""

    @staticmethod
    async def validate_order_ownership(
        order_id: str,
        expected_symbol: str,
        credentials: Dict[str, str]
    ) -> bool:
        """Verify order belongs to expected position."""
```

#### Position State Machine
```python
class PositionStateManager:
    @staticmethod
    async def evaluate_position_state(
        position: Position,
        dydx_orders: Dict[str, Dict[str, Any]]
    ) -> Tuple[str, str]:
        """Determine if position should be closed based on order status."""

    @staticmethod
    async def calculate_position_pnl(
        position: Position,
        closing_price: float,
        closing_size: float
    ) -> float:
        """Calculate final P&L for position closure."""

    @staticmethod
    async def determine_closing_reason(
        tp_order_status: str,
        sl_order_status: str,
        entry_order_status: str
    ) -> str:
        """Determine why position was closed (TP, SL, or manual)."""

    @staticmethod
    async def validate_position_closure(
        position: Position,
        closing_data: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Validate position closure data integrity."""
```

### 3. Automated Position Closure

#### Position Closure Orchestrator
```python
class PositionClosureOrchestrator:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.position_manager = PositionManager(db_session)

    async def close_position_automatically(
        self,
        position: Position,
        credentials: Dict[str, str],
        closing_reason: str,
        closing_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Orchestrate complete automatic position closure."""

    async def step_1_cancel_remaining_orders(
        self,
        position: Position,
        credentials: Dict[str, str]
    ) -> List[str]:
        """Cancel any remaining open orders for the position."""

    async def step_2_update_database(
        self,
        position: Position,
        closing_data: Dict[str, Any]
    ) -> Position:
        """Update position status in database."""

    async def step_3_send_closure_notification(
        self,
        position: Position,
        credentials: Dict[str, str],
        closing_data: Dict[str, Any]
    ) -> bool:
        """Send position closure notification to user."""

    async def step_4_log_closure_event(
        self,
        position: Position,
        closing_data: Dict[str, Any]
    ) -> None:
        """Log position closure for audit and monitoring."""
```

#### Batch Processing Optimization
```python
class BatchProcessor:
    @staticmethod
    async def process_positions_batch(
        positions: List[Position],
        credentials_map: Dict[str, Dict[str, str]],
        max_concurrent: int = 10
    ) -> List[Dict[str, Any]]:
        """Process multiple positions concurrently for efficiency."""

    @staticmethod
    async def handle_partial_failures(
        results: List[Dict[str, Any]],
        original_positions: List[Position]
    ) -> List[Position]:
        """Handle cases where some positions fail processing."""

    @staticmethod
    async def retry_failed_positions(
        failed_positions: List[Position],
        retry_count: int = 3,
        backoff_seconds: int = 60
    ) -> List[Dict[str, Any]]:
        """Retry failed position processing with exponential backoff."""
```

### 4. Notification and Alerting

#### Telegram Notification System
```python
class PositionNotificationManager:
    @staticmethod
    async def send_position_closure_notification(
        credentials: Dict[str, str],
        position: Position,
        closing_data: Dict[str, Any]
    ) -> bool:
        """Send detailed position closure notification."""

    @staticmethod
    async def format_closure_message(
        position: Position,
        closing_reason: str,
        pnl: float,
        closing_price: float
    ) -> str:
        """Format position closure message with all relevant details."""

    @staticmethod
    async def send_monitoring_alert(
        alert_type: str,
        message: str,
        admin_credentials: Dict[str, str]
    ) -> bool:
        """Send system monitoring alerts to administrators."""
```

#### Monitoring and Alerting
```python
class MonitoringManager:
    @staticmethod
    async def track_monitoring_metrics(
        cycle_time: float,
        positions_processed: int,
        positions_closed: int,
        errors: List[str]
    ) -> None:
        """Track monitoring performance metrics."""

    @staticmethod
    async def detect_anomalies(
        current_cycle: Dict[str, Any],
        historical_data: List[Dict[str, Any]]
    ) -> List[str]:
        """Detect unusual patterns in position monitoring."""

    @staticmethod
    async def generate_health_report() -> Dict[str, Any]:
        """Generate comprehensive system health report."""
```

## Implementation Plan

### Phase 5.1: Background Worker Foundation
1. **Create worker process architecture** with lifecycle management
2. **Implement database query optimization** for position fetching
3. **Add worker health monitoring** and metrics collection
4. **Create graceful shutdown** handling

### Phase 5.2: Position Monitoring Logic
1. **Build dYdX order status checking** with batch optimization
2. **Implement position state evaluation** logic
3. **Create P&L calculation** utilities
4. **Add data integrity validation** for all operations

### Phase 5.3: Automated Closure System
1. **Build position closure orchestrator** with rollback capabilities
2. **Implement batch processing** for efficiency
3. **Add retry logic** with exponential backoff
4. **Create comprehensive error handling** and logging

### Phase 5.4: Notification and Monitoring
1. **Integrate Telegram notifications** for position closures
2. **Implement monitoring dashboard** metrics
3. **Add alerting system** for system issues
4. **Create audit logging** for compliance

## Dependencies

### Core Dependencies
- **Background Tasks**: `asyncio` with proper task management
- **Concurrent Processing**: `aiohttp` for parallel dYdX API calls
- **Database Optimization**: `sqlalchemy` with connection pooling
- **Metrics Collection**: `prometheus-client` for monitoring

### Monitoring Dependencies
- **Health Checks**: `healthcheck` for worker health validation
- **Structured Logging**: `structlog` for operational visibility
- **Alert Management**: `sentry-sdk` for error tracking
- **Performance Monitoring**: `datadog` or `newrelic` integration

## Security Considerations

### Credential Management
- **Per-User Credential Isolation**: Each position processed with its own credentials
- **Minimal Credential Exposure**: Credentials loaded only when needed
- **Automatic Credential Cleanup**: Secure cleanup after each processing cycle
- **Credential Rotation**: Support for periodic credential updates

### System Security
- **Resource Limits**: Prevent worker from consuming excessive resources
- **Rate Limiting**: Respect dYdX API rate limits across all users
- **Error Isolation**: Prevent errors in one position from affecting others
- **Access Logging**: Complete audit trail for all position access

### Data Protection
- **Transaction Integrity**: Atomic operations for position updates
- **Backup Consistency**: Ensure monitoring doesn't interfere with backups
- **Data Validation**: Verify all data before database updates
- **Privacy Protection**: No cross-user data exposure

## Testing Strategy

### Unit Tests
- **Worker Logic**: Test position monitoring and state evaluation
- **Order Checking**: Mock dYdX API responses for various scenarios
- **Closure Logic**: Test position closure with different outcomes
- **Error Handling**: Validate error recovery and retry mechanisms

### Integration Tests
- **Database Operations**: Test position queries and updates under load
- **External API Integration**: Validate dYdX and Telegram API interactions
- **Concurrent Processing**: Test multiple workers processing positions
- **State Consistency**: Verify position state remains consistent

### Load Tests
- **High Position Volume**: Test with large numbers of open positions
- **Concurrent Users**: Validate performance across many users
- **API Rate Limits**: Test behavior when approaching dYdX limits
- **Memory Usage**: Monitor memory consumption during extended operation

### Resilience Tests
- **Network Failures**: Test behavior during dYdX API outages
- **Database Issues**: Validate handling of database connectivity problems
- **Partial Failures**: Test recovery when some positions fail processing
- **Resource Exhaustion**: Validate behavior under resource constraints

## Success Criteria
- [ ] Background worker starts and runs continuously with FastAPI
- [ ] Open positions are queried from database at regular intervals
- [ ] dYdX order status is checked for each open position
- [ ] TP/SL order fills trigger automatic position closure
- [ ] Remaining orders are cancelled when positions are closed
- [ ] Database position status is updated correctly
- [ ] Users receive closure notifications via Telegram
- [ ] All operations maintain data consistency and integrity
- [ ] Performance meets monitoring frequency requirements
- [ ] All tests pass with minimum 90% coverage

## Rollback Plan
- **Worker Disabling**: Can disable worker without affecting other components
- **Graceful Degradation**: System continues operating if worker fails
- **Data Consistency**: Position data remains intact during rollback
- **Emergency Stop**: Immediate worker termination capability

## Future Dependencies
This completes the core dYdX Trading Bot Service with all planned functionality.

## Open Questions
- **Monitoring Frequency**: Optimal interval for position checking
- **Scalability Limits**: Maximum number of positions per monitoring cycle
- **Alert Thresholds**: When to trigger administrative alerts
- **Performance Optimization**: Further optimization opportunities for high-volume scenarios

## References
- Master Plan: Phase 5 - Background Position Monitoring
- Project Context: openspec/project.md
- Previous Proposals:
  - openspec/changes/foundation-database-setup.md
  - openspec/changes/web3-authentication-dashboard.md
  - openspec/changes/core-trading-engine.md
  - openspec/changes/secure-webhook-system.md