# Secure Two-Factor Webhook System - Change Proposal

## Overview
This change proposal implements Phase 4 of the dYdX Trading Bot Service: activating the end-to-end trading flow triggered by a secure, two-factor webhook system with complete trade execution orchestration.

## Problem Statement
The trading engine requires a secure, reliable mechanism to receive trading signals from external sources (TradingView) and execute trades with proper authentication and user isolation. The current system lacks the webhook infrastructure for production trading activation.

## Goals
- Implement secure two-factor webhook authentication system
- Enable complete end-to-end trade execution from webhook to notification
- Ensure user isolation and credential security throughout the trading flow
- Provide robust error handling and monitoring for production reliability

## Technical Specifications

### 1. Webhook Router Architecture (`src/api/webhooks.py`)

#### Two-Factor Authentication System
```python
class WebhookAuthenticator:
    @staticmethod
    async def verify_two_factor(
        webhook_uuid: str,
        request_body: Dict[str, Any],
        db_session: Session
    ) -> Tuple[bool, Optional[User], str]:
        """Verify webhook UUID from URL and secret from request body."""

    @staticmethod
    async def extract_webhook_secret(request_body: Dict[str, Any]) -> str:
        """Extract webhook secret from request body."""

    @staticmethod
    async def validate_request_format(
        request_body: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Validate TradingView webhook request format."""

    @staticmethod
    async def rate_limit_check(
        webhook_uuid: str,
        window_seconds: int = 60,
        max_requests: int = 10
    ) -> bool:
        """Implement rate limiting for webhook requests."""
```

#### Main Webhook Router
```python
class WebhookRouter:
    def __init__(self, db_session: Session, trading_engine: TradingEngine):
        self.db = db_session
        self.trading_engine = trading_engine

    async def handle_webhook(
        self,
        webhook_uuid: str,
        request: Request
    ) -> Dict[str, Any]:
        """Main webhook handler with two-factor verification."""

    async def process_tradingview_signal(
        self,
        user: User,
        signal_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process verified TradingView signal into trade execution."""

    async def handle_verification_failure(
        self,
        reason: str,
        webhook_uuid: str
    ) -> Dict[str, Any]:
        """Handle authentication failures securely."""
```

### 2. Trade Execution Orchestration

#### Credential Management Integration
```python
class CredentialManager:
    @staticmethod
    async def fetch_user_credentials(
        user: User,
        master_key: str,
        db_session: Session
    ) -> Dict[str, str]:
        """Securely decrypt and return user credentials."""

    @staticmethod
    async def validate_credentials(credentials: Dict[str, str]) -> Tuple[bool, str]:
        """Validate decrypted credentials for trading."""

    @staticmethod
    async def cleanup_credentials(credentials: Dict[str, str]) -> None:
        """Securely clear credentials from memory."""
```

#### Complete Trade Execution Flow
```python
class TradeOrchestrator:
    def __init__(self, db_session: Session, trading_engine: TradingEngine):
        self.db = db_session
        self.trading_engine = trading_engine

    async def execute_complete_trade(
        self,
        user: User,
        signal_data: Dict[str, Any],
        master_key: str
    ) -> Dict[str, Any]:
        """Orchestrate complete trade execution from signal to notification."""

    async def step_1_credential_retrieval(
        self,
        user: User,
        master_key: str
    ) -> Dict[str, str]:
        """Step 1: Decrypt user credentials."""

    async def step_2_risk_calculation(
        self,
        credentials: Dict[str, str],
        signal_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Step 2: Calculate position size and validate risk."""

    async def step_3_trade_execution(
        self,
        credentials: Dict[str, str],
        risk_parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Step 3: Execute trade on dYdX."""

    async def step_4_position_persistence(
        self,
        user: User,
        trade_result: Dict[str, Any]
    ) -> Position:
        """Step 4: Save position to database."""

    async def step_5_notification_delivery(
        self,
        credentials: Dict[str, str],
        position: Position,
        trade_result: Dict[str, Any]
    ) -> bool:
        """Step 5: Send confirmation notification."""
```

### 3. TradingView Integration

#### Signal Processing
```python
class TradingViewSignalProcessor:
    @staticmethod
    def parse_tradingview_webhook(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Parse TradingView webhook format into internal signal format."""

    @staticmethod
    def validate_signal_data(signal_data: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate required signal fields and data types."""

    @staticmethod
    def normalize_symbol_format(symbol: str) -> str:
        """Normalize TradingView symbol format to dYdX format."""

    @staticmethod
    def extract_order_parameters(signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract price, size, and order type from signal."""
```

#### Signal Format Support
```python
# Supported TradingView alert formats
TRADINGVIEW_FORMATS = {
    "simple": {
        "symbol": "BTCUSDT",
        "side": "buy|sell",
        "price": "optional",
        "size": "optional"
    },
    "advanced": {
        "symbol": "BTCUSDT",
        "side": "buy|sell",
        "order_type": "market|limit",
        "price": "float",
        "size": "float",
        "take_profit": "optional",
        "stop_loss": "optional"
    }
}
```

## Implementation Plan

### Phase 4.1: Webhook Security Foundation
1. **Implement two-factor authentication** system
2. **Create webhook router** with proper error handling
3. **Add rate limiting** and DDoS protection
4. **Implement comprehensive logging** for security monitoring

### Phase 4.2: Trade Execution Pipeline
1. **Build credential management** integration
2. **Create trade orchestrator** with step-by-step execution
3. **Implement risk validation** at each step
4. **Add transaction rollback** capabilities

### Phase 4.3: TradingView Integration
1. **Implement signal parsing** for multiple formats
2. **Add signal validation** and normalization
3. **Create format conversion** utilities
4. **Add TradingView-specific error handling**

### Phase 4.4: Production Hardening
1. **Implement comprehensive monitoring** and alerting
2. **Add performance optimization** for high-frequency trading
3. **Create webhook testing utilities** for development
4. **Implement graceful degradation** for external service failures

## Dependencies

### Core Dependencies
- **Webhook Processing**: `pydantic` for request validation
- **Rate Limiting**: `slowapi` with Redis backend
- **Background Tasks**: `celery` for async trade processing
- **Monitoring**: `structlog` for structured logging

### Security Dependencies
- **DDoS Protection**: `cloudflare` or `nginx` rate limiting
- **Request Validation**: `jsonschema` for webhook payload validation
- **Audit Logging**: `audit-log` for security event tracking
- **IP Whitelisting**: `ipwhitelist` for additional security

## Security Considerations

### Webhook Security
- **Two-Factor Authentication**: UUID + secret requirement
- **Replay Attack Prevention**: Nonce validation and request deduplication
- **Rate Limiting**: Progressive rate limiting with backoff
- **IP Validation**: Optional IP whitelisting for additional security

### Credential Security
- **Minimal Exposure**: Credentials decrypted only when needed
- **Memory Protection**: SecureString usage for sensitive data
- **Automatic Cleanup**: Immediate credential clearing after use
- **Access Auditing**: Complete audit trail for credential access

### Trade Security
- **Pre-Trade Validation**: Risk checks before any trade execution
- **Order Limits**: Maximum position sizes and daily volume limits
- **Emergency Controls**: Circuit breakers for extreme market conditions
- **Rollback Safety**: Safe position closure on critical errors

## Testing Strategy

### Unit Tests
- **Authentication**: Two-factor verification with various scenarios
- **Signal Processing**: TradingView format parsing and validation
- **Orchestration**: Individual step testing with mocked dependencies
- **Error Handling**: Failure mode testing for each component

### Integration Tests
- **End-to-End Flow**: Complete webhook → trade → notification cycle
- **Database Consistency**: Position creation and state management
- **External Services**: dYdX and Telegram API integration testing
- **Concurrent Webhooks**: Multiple simultaneous trading signals

### Security Tests
- **Authentication Bypass**: Attempt various attack vectors
- **Rate Limiting**: DDoS simulation and validation
- **Credential Exposure**: Verify no sensitive data leakage
- **Replay Attacks**: Test signal replay prevention

### Load Tests
- **High Frequency**: Multiple webhooks per second simulation
- **Concurrent Users**: Simultaneous trading across many users
- **Database Performance**: Position table performance under load
- **External API Limits**: dYdX API rate limit handling

## Success Criteria
- [ ] Two-factor webhook authentication working correctly
- [ ] Complete trade execution from webhook to notification
- **Security**: All authentication bypass attempts fail
- [ ] Rate limiting prevents abuse without blocking legitimate traffic
- [ ] All external service failures handled gracefully
- [ ] Database operations maintain consistency under load
- [ ] Performance meets latency requirements for trading
- [ ] All tests pass with minimum 90% coverage

## Rollback Plan
- **Feature Flags**: Webhook processing can be disabled per user
- **Gradual Rollout**: Enable for test users before full deployment
- **Emergency Stop**: Immediate webhook disabling capability
- **Data Safety**: No data loss during rollback procedures

## Future Dependencies
This phase enables:
- **Phase 5**: Background Position Monitoring

## Open Questions
- **Webhook Format Evolution**: How to handle TradingView format changes
- **Emergency Procedures**: Automated trading halt mechanisms
- **Performance Scaling**: Horizontal scaling strategy for high-volume trading
- **Compliance Requirements**: Additional logging for regulatory compliance

## References
- Master Plan: Phase 4 - Secure Webhook Implementation
- Project Context: openspec/project.md
- Previous Proposals:
  - openspec/changes/foundation-database-setup.md
  - openspec/changes/web3-authentication-dashboard.md
  - openspec/changes/core-trading-engine.md