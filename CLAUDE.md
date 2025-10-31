<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**dYdX Trading Service** - A multi-tenant SaaS platform for automated cryptocurrency trading on dYdX v4. Non-custodial architecture where users retain control of funds through Web3 authentication and local credential encryption.

**Status**: Phase 2 Complete (~9,300 lines of production code across 5 tasks)

**Tech Stack**:
- Backend: FastAPI 0.104.1 + asyncpg (async PostgreSQL)
- Frontend: Jinja2 templates + Tailwind CSS 3.3.6 + vanilla JS
- Database: PostgreSQL 14 (SQLModel ORM)
- Containers: Docker/Docker Compose

---

## Common Development Commands

### Building & Running

```bash
# Start all services (web + database)
docker-compose up -d

# Build backend without cache
docker-compose build --no-cache backend

# View logs
docker-compose logs -f web-app
docker-compose logs -f db

# Stop all services
docker-compose down

# Clean everything (including volumes)
docker-compose down -v
```

### Local Development (without Docker)

```bash
# Install dependencies
cd backend
pip install -r requirements.txt
npm install

# Run database separately
docker-compose up db -d

# Start FastAPI with hot reload
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Build frontend assets (in another terminal)
npm run dev    # Development watch
npm run prod   # Production build
```

### Testing

```bash
# Run all tests
docker-compose exec backend poetry run pytest tests/ -v

# Run specific test file
docker-compose exec backend poetry run pytest tests/test_trading_audit.py -v

# Run with coverage
docker-compose exec backend poetry run pytest tests/ --cov=src --cov-report=html

# Run single test
docker-compose exec backend poetry run pytest tests/test_pnl_calculator.py::test_calculate_realized_pnl -v
```

### Code Quality

```bash
# Format code (Black)
docker-compose exec backend poetry run black src/

# Sort imports
docker-compose exec backend poetry run isort src/

# Lint with Flake8
docker-compose exec backend poetry run flake8 src/

# Type checking (mypy)
docker-compose exec backend poetry run mypy src/
```

### Health Checks

```bash
# Basic health
curl http://localhost:8000/

# Network configuration
curl http://localhost:8000/health/network | jq

# System configuration
curl http://localhost:8000/health/config | jq

# Kubernetes readiness
curl http://localhost:8000/health/ready | jq

# PNL summary
curl http://localhost:8000/api/pnl/summary | jq

# Worker status
curl http://localhost:8000/api/worker/status | jq
```

### Database Operations

```bash
# Connect to PostgreSQL
docker-compose exec db psql -U postgres -d trading_service

# View tables
\dt

# Exit
\q

# Run migrations (automatic on startup)
docker-compose exec backend poetry run alembic upgrade head
```

### Frontend Development

```bash
# Install JS dependencies
npm install

# Watch and rebuild CSS
npm run dev

# Production CSS build
npm run prod

# Build all assets
npm run build-css
```

---

## Architecture Overview

### System Diagram

```
Client → FastAPI (Port 8000) → PostgreSQL + Workers
           ├─ Web3 Auth (eth-account)
           ├─ Webhook Receiver (2FA: UUID + Secret)
           ├─ WebSocket Server (real-time data)
           ├─ Trading Engine (dYdX integration)
           └─ Background Workers (position monitoring)
```

### Request Flow: Webhook to Execution

1. **TradingView Alert** → POST `/api/webhooks/signal/{webhook_uuid}`
2. **2FA Verification** → Validate webhook_uuid (URL) + webhook_secret (body)
3. **Fetch Credentials** → Decrypt user's dYdX mnemonic from database
4. **Trade Execution** → TradingEngine places entry + TP + SL orders
5. **State Persistence** → Save position to database
6. **Notification** → Send Telegram confirmation
7. **Monitoring** → Background worker watches order status continuously
8. **Position Closure** → Auto-close on TP/SL execution

### Core Modules

**API Routes** (`backend/src/api/`):
- `auth.py` - Web3 wallet authentication
- `webhooks.py` - Trading signal receivers with 2FA
- `user.py` - Dashboard and credential management
- `trading.py` - Direct trade execution
- `pnl.py` - P&L calculations and analytics
- `websockets.py` - Real-time data streaming
- `health.py` - System health endpoints
- `errors.py` - Error reporting

**Trading Logic** (`backend/src/bot/`):
- `dydx_client.py` - Stateless dYdX protocol client
- `trading_engine.py` - Order execution orchestrator
- `trading_audit.py` - Order/position validation
- `pnl_calculator.py` - P&L computation engine
- `state_manager.py` - Position CRUD operations
- `risk_manager.py` - Risk assessment
- `websocket_manager.py` - dYdX WebSocket connections
- `telegram_manager.py` - Telegram notifications

**Background Workers** (`backend/src/workers/`):
- `position_monitor.py` - Monitors open positions
- `monitoring_manager.py` - Orchestrates monitoring
- `dydx_order_monitor.py` - Tracks order status
- `position_closure_orchestrator.py` - Handles position closure
- `notification_manager.py` - Sends user notifications
- `error_handler.py` - Centralized error handling

**Security & Config** (`backend/src/core/`):
- `security.py` - AES-256 encryption/decryption (master key in .env)
- `config.py` - Pydantic settings management
- `network_validator.py` - Testnet/mainnet safety checks
- `resilience.py` - Circuit breaker + retry logic
- `logging_config.py` - Structured logging

**Database** (`backend/src/db/`):
- `models.py` - SQLModel schemas (User, Position, WebhookEvent)
- `database.py` - AsyncSession + connection pooling

---

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    wallet_address VARCHAR(42) PRIMARY KEY,           -- Ethereum address
    webhook_uuid VARCHAR(36) UNIQUE NOT NULL,         -- Unique webhook ID
    encrypted_webhook_secret VARCHAR(500),            -- 2FA secret (AES-256)
    encrypted_dydx_mnemonic VARCHAR(500),             -- Trading credentials (AES-256)
    encrypted_telegram_token VARCHAR(500),            -- Telegram token (AES-256)
    encrypted_telegram_chat_id VARCHAR(500),          -- Telegram chat ID (AES-256)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Positions Table
```sql
CREATE TABLE positions (
    id SERIAL PRIMARY KEY,
    user_address VARCHAR(42) REFERENCES users ON DELETE CASCADE,
    symbol VARCHAR(20),                               -- e.g., BTC-USD
    status VARCHAR(20),                               -- open/closed/cancelled
    entry_price DECIMAL(20,10),
    size DECIMAL(20,10),
    dydx_order_id VARCHAR(100),                       -- Main entry order
    tp_order_id VARCHAR(100),                         -- Take-profit order
    sl_order_id VARCHAR(100),                         -- Stop-loss order
    opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP,
    realized_pnl DECIMAL(20,10),
    fees DECIMAL(20,10)
);
```

### WebhookEvent Table (Audit Log)
```sql
CREATE TABLE webhook_events (
    id SERIAL PRIMARY KEY,
    webhook_uuid VARCHAR(36),
    event_type VARCHAR(50),
    status VARCHAR(20),
    payload JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Configuration & Environment

### Critical Environment Variables

| Variable | Purpose | Format | Required |
|----------|---------|--------|----------|
| `MASTER_ENCRYPTION_KEY` | AES-256 key for sensitive data | 64-char hex (32 bytes) | Yes |
| `DATABASE_URL` | PostgreSQL connection | `postgresql://user:pwd@host/db` | Yes |
| `INDEXER_REST_URL` | dYdX API endpoint | URL | Yes |
| `INDEXER_WS_URL` | dYdX WebSocket endpoint | WSS URL | Yes |
| `DYDX_V4_PRIVATE_KEY` | Trading account key | Hex private key | Yes |
| `DYDX_V4_API_WALLET_ADDRESS` | Trading account address | dydx1... address | Yes |
| `APP_ENV` | Environment | development/production | No (default: development) |
| `DEBUG` | Debug mode | true/false | No |
| `CORS_ORIGINS` | Allowed origins | JSON list | No |

### Generate Encryption Key

```bash
python3 -c "import secrets; print('MASTER_ENCRYPTION_KEY=' + secrets.token_hex(32))"
```

### Testnet vs Mainnet

**Testnet Configuration** (safe for development):
```env
APP_ENV=development
INDEXER_REST_URL=https://indexer.v4testnet.dydx.exchange
INDEXER_WS_URL=wss://indexer.v4testnet.dydx.exchange/v4/ws
```

**Mainnet Configuration** (production - real money):
```env
APP_ENV=production
INDEXER_REST_URL=https://indexer.dydx.trade/v4
INDEXER_WS_URL=wss://indexer.dydx.trade/v4/ws
```

**Safety Note**: Network validator prevents unsafe configurations (e.g., production env with testnet URLs). See `backend/src/core/network_validator.py`.

---

## Key Implementation Details

### Security Architecture

1. **AES-256 Encryption** (`core/security.py`):
   - Master key stored in `.env` only (never in code)
   - All sensitive data encrypted at rest (mnemonics, API tokens)
   - Encryption/decryption on database write/read

2. **Two-Factor Webhook Authentication** (`api/webhooks.py`):
   - Factor 1: Unique `webhook_uuid` in URL path
   - Factor 2: `webhook_secret` in request body
   - HMAC validation for message integrity

3. **Web3 Authentication** (`api/auth.py`):
   - Signature verification using `eth-account`
   - Message-based auth (no passwords)
   - Wallet address as user identity

4. **Rate Limiting** (`main.py`):
   - slowapi: 200 requests/day, 50/hour by default
   - Custom rate limit handlers

5. **Security Headers** (`main.py`):
   - X-Content-Type-Options, X-Frame-Options, CSP
   - HSTS for HTTPS enforcement

### Trading Engine

1. **DydxClient** (`bot/dydx_client.py`):
   - Stateless interface to dYdX protocol
   - Per-user credentials passed as parameters
   - Supports both testnet and mainnet

2. **TradingEngine** (`bot/trading_engine.py`):
   - Orchestrates complete trade execution
   - Places entry + TP + SL orders atomically
   - Error handling and rollback on failure

3. **TradingAudit** (`bot/trading_audit.py`):
   - Validates order parameters (price, size, leverage)
   - Validates order lifecycle (state transitions)
   - Audit report generation

4. **StateManager** (`bot/state_manager.py`):
   - CRUD operations for positions
   - Transaction management
   - Relationship handling (user ↔ positions)

### Position Monitoring

1. **PositionMonitor** (`workers/position_monitor.py`):
   - Continuous monitoring of open positions
   - Polls order status from dYdX chain
   - Auto-closes on TP/SL execution

2. **Error Handling** (`workers/error_handler.py`):
   - Circuit breaker pattern
   - Exponential backoff retry logic
   - Error categorization

3. **Notifications** (`workers/notification_manager.py`):
   - Telegram alerts for trade execution/closure
   - Extensible for email, Discord, etc.

### Real-time Features

1. **WebSocketManager** (`bot/websocket_manager.py`):
   - Maintains dYdX WebSocket connections
   - Automatic reconnection with backoff
   - Channel subscription management

2. **WebSocketHandlers** (`bot/websocket_handlers.py`):
   - Account update handler (balance changes)
   - Order update handler (status changes)
   - Trade update handler (fill notifications)

---

## Testing Strategy

### Test Organization

```
backend/tests/
├── test_auth.py               # Web3 authentication
├── test_webhooks.py           # Webhook endpoints + 2FA
├── test_trading_engine.py     # Trade execution
├── test_trading_audit.py      # Order validation
├── test_pnl_calculator.py     # P&L calculations
├── test_state_manager.py      # Position CRUD
├── test_risk_manager.py       # Risk validation
└── fixtures/                  # Shared test fixtures
```

### Running Tests

```bash
# All tests
docker-compose exec backend poetry run pytest tests/ -v

# Specific file
docker-compose exec backend poetry run pytest tests/test_trading_audit.py -v

# Single test
docker-compose exec backend poetry run pytest tests/test_trading_audit.py::test_validate_order -v

# With coverage
docker-compose exec backend poetry run pytest tests/ --cov=src
```

### Test Database

- **Development**: Uses PostgreSQL (container)
- **Testing**: Uses SQLite in-memory (aiosqlite) for speed
- Schema auto-created on test startup

---

## API Endpoints Quick Reference

### Health & Monitoring
- `GET /` - Basic health
- `GET /health/detailed` - System info
- `GET /health/network` - Network config status
- `GET /health/config` - App config check
- `GET /health/ready` - K8s readiness
- `GET /health/live` - K8s liveness
- `GET /api/worker/status` - Worker metrics

### Authentication
- `POST /api/auth/login` - Web3 login
- `POST /api/auth/create-user` - Create account
- `GET /api/auth/generate-message` - Get sig message

### Trading
- `POST /api/webhooks/signal/{webhook_uuid}` - Webhook receiver
- `POST /api/trading/execute` - Manual trade
- `POST /api/trading/close/{position_id}` - Close position
- `GET /api/user/positions` - User's positions

### Analytics
- `GET /api/pnl/summary` - P&L summary
- `GET /api/pnl/history` - Historical P&L
- `GET /api/pnl/performance` - Performance metrics
- `GET /api/equity-curve/data` - Equity curve data

### WebSocket
- `WS /ws/dashboard` - Dashboard updates
- `WS /ws/dydx-stream` - dYdX data stream

**Full API docs**: http://localhost:8000/docs (Swagger UI)

---

## Common Development Tasks

### Adding a New Endpoint

1. Create handler in `backend/src/api/` or extend existing module
2. Use Pydantic models for request/response validation
3. Add authentication decorator if needed: `@require_auth` or `@require_webhook_auth`
4. Include comprehensive error handling
5. Add tests in `backend/tests/`
6. Update `ALL_ROUTES.md` documentation

### Adding a Database Migration

1. Modify `backend/src/db/models.py` SQLModel definition
2. Auto-migration on startup (Alembic configured)
3. Or manually: `docker-compose exec backend poetry run alembic revision --autogenerate -m "description"`

### Debugging

1. **View logs**: `docker-compose logs -f web-app`
2. **Health check**: `curl http://localhost:8000/health/detailed | jq`
3. **API docs**: http://localhost:8000/docs
4. **DB query**: `docker-compose exec db psql -U postgres -d trading_service`

### Deploying Configuration Changes

1. Update `.env` file
2. Run validation: `docker-compose exec backend python backend/validate_network_config.py`
3. Restart service: `docker-compose restart web-app`
4. Verify: `curl http://localhost:8000/health/network`

---

## File Organization Principles

- **API Routes**: `backend/src/api/` - HTTP endpoints grouped by feature
- **Bot Logic**: `backend/src/bot/` - Core trading and protocol logic
- **Workers**: `backend/src/workers/` - Background tasks and long-running processes
- **Core**: `backend/src/core/` - Shared utilities (config, security, logging)
- **Database**: `backend/src/db/` - Schema and connection management
- **Frontend**: `backend/src/templates/` and `backend/src/static/` - HTML + CSS/JS
- **Tests**: `backend/tests/` - Parallel structure to src/ for imports

---

## Important Notes

### Non-Custodial Architecture

- Service never holds user funds or manages wallets
- Users provide their dYdX mnemonic (encrypted and stored)
- Users authenticate via Web3 signature verification
- Trading keys held locally by users or in encrypted storage

### State Management

- Positions stored in PostgreSQL for durability
- Order IDs tracked to handle dYdX acknowledgments
- Background workers poll dYdX for position updates
- Position closure triggers notification and cleanup

### Error Handling

- Circuit breaker pattern prevents cascading failures
- Exponential backoff for transient errors
- Structured logging for debugging (structlog)
- Error categories: user_input, dydx_api, internal, network

### Security

- All API endpoints validate input with Pydantic
- Webhook endpoints require 2FA (UUID + secret)
- Rate limiting prevents abuse
- CORS restricted to configured origins
- No sensitive data in error responses

---

## Useful Documentation Files

| File | Purpose |
|------|---------|
| `MASTER-PLAN.md` | Overall roadmap and architecture |
| `ALL_ROUTES.md` | Complete API documentation |
| `PHASE2_OPENSPEC_PROPOSALS.md` | Task specifications |
| `WEBSOCKET_INTEGRATION_GUIDE.md` | WebSocket code examples |
| `PNL_CALCULATION_GUIDE.md` | P&L methodology and examples |
| `TESTNET_MAINNET_GUIDE.md` | Network switching guide |
| `TASK1_INTEGRATION_COMPLETE.md` through `TASK5_ERROR_HANDLING.md` | Phase 2 task details |

---

## Quick Reference

### Development Workflow

```bash
# 1. Start services
docker-compose up -d

# 2. Check health
curl http://localhost:8000/health/detailed

# 3. Run tests
docker-compose exec backend poetry run pytest tests/ -v

# 4. Format code
docker-compose exec backend poetry run black src/

# 5. View logs
docker-compose logs -f web-app

# 6. Stop services
docker-compose down
```

### Adding a Feature

1. Plan in `MASTER-PLAN.md` or task doc
2. Implement in appropriate module
3. Add tests (test files parallel src/ structure)
4. Run: `poetry run pytest tests/`, `black src/`, `mypy src/`
5. Update documentation
6. Commit with clear message

### Debugging Production Issues

1. Check health endpoint: `/health/detailed`
2. Check logs: `docker-compose logs web-app`
3. Check database: `docker-compose exec db psql -U postgres -d trading_service`
4. Check worker status: `/api/worker/status`
5. Check network config: `/health/network`

---

## Stack Highlights

- **Async Everything**: FastAPI + asyncpg for high concurrency
- **Production-Ready**: Error handling, logging, monitoring, health checks
- **Type Safety**: Full mypy strict mode with type hints
- **Security-First**: Encryption at rest, 2FA, rate limiting, CORS
- **Testable**: Comprehensive test suite with fixtures
- **Observable**: Structured logging, health endpoints, error tracking
