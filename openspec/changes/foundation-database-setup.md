# Foundation and Database Setup - Change Proposal

## Overview
This change proposal implements Phase 1 of the dYdX Trading Bot Service: establishing the foundational architecture with containerized services and database connectivity.

## Problem Statement
The project currently lacks the basic infrastructure required to support a multi-tenant trading platform. We need to establish a solid foundation with proper containerization, database connectivity, and initial application structure.

## Goals
- Create a running containerized application with database connection
- Establish project directory structure following the master plan specifications
- Implement database schemas for users and positions
- Set up basic FastAPI application with health monitoring

## Technical Specifications

### 1. Project Directory Structure
```
dydx-trading-service/
├── .env                          # Master secrets and configuration
├── docker-compose.yml           # Multi-container orchestration
├── tailwind.config.js           # Tailwind CSS configuration
└── backend/
    ├── Dockerfile               # Python application container
    ├── requirements.txt         # Python dependencies
    ├── package.json            # Tailwind CSS dependencies
    └── src/
        ├── main.py             # FastAPI application entry point
        ├── core/
        │   ├── config.py       # Application configuration
        │   └── security.py     # Encryption utilities
        ├── db/
        │   ├── database.py     # Database connection and session management
        │   └── models.py       # SQLModel database schemas
        ├── static/
        │   ├── css/
        │   └── js/
        └── templates/
            ├── index.html
            └── dashboard.html
```

### 2. Docker Configuration
**docker-compose.yml** will define:
- `web-app` service: Python FastAPI application
- `db` service: PostgreSQL database
- Environment variables for database connectivity
- Volume mounts for persistent data storage
- Network configuration for service communication

### 3. Database Schema Design

#### Users Table
```python
class User(SQLModel, table=True):
    __tablename__ = "users"

    wallet_address: str = Field(primary_key=True, max_length=42)
    webhook_uuid: str = Field(unique=True, max_length=36)
    encrypted_webhook_secret: str = Field(max_length=500)
    encrypted_dydx_mnemonic: str = Field(max_length=500)
    encrypted_telegram_token: str = Field(max_length=500)
    encrypted_telegram_chat_id: str = Field(max_length=100)
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

#### Positions Table
```python
class Position(SQLModel, table=True):
    __tablename__ = "positions"

    id: int = Field(primary_key=True)
    user_address: str = Field(foreign_key="users.wallet_address", max_length=42)
    symbol: str = Field(max_length=20)
    status: str = Field(max_length=20, default="open")
    entry_price: Decimal = Field(max_digits=20, decimal_places=10)
    size: Decimal = Field(max_digits=20, decimal_places=10)
    dydx_order_id: str = Field(max_length=100)
    tp_order_id: str = Field(max_length=100)
    sl_order_id: str = Field(max_length=100)
    opened_at: datetime = Field(default_factory=datetime.utcnow)
```

### 4. Application Architecture

#### Database Layer (`src/db/database.py`)
- SQLAlchemy engine configuration with connection pooling
- Session management with proper cleanup
- Database initialization and migration utilities
- Connection health monitoring

#### Core Configuration (`src/core/config.py`)
- Environment variable management
- Database connection settings
- Application settings with validation
- Development vs production configuration

#### Security Module (`src/core/security.py`)
- AES-256 encryption/decryption utilities
- Key derivation from master password
- Secure credential handling

#### Main Application (`src/main.py`)
- FastAPI application factory
- CORS middleware configuration
- Health check endpoint (`GET /`)
- Graceful shutdown handling
- Startup and shutdown event handlers

## Implementation Plan

### Phase 1.1: Infrastructure Setup
1. Create project directory structure
2. Configure Docker and docker-compose.yml
3. Set up environment configuration
4. Implement core security utilities

### Phase 1.2: Database Foundation
1. Design and implement database models
2. Create database connection layer
3. Implement database initialization scripts
4. Add database health monitoring

### Phase 1.3: Application Framework
1. Create FastAPI application structure
2. Implement health check endpoints
3. Add startup/shutdown event handlers
4. Configure CORS and security middleware

## Dependencies
- **Runtime**: Python 3.10+, PostgreSQL 14+
- **Core**: fastapi, uvicorn, sqlmodel, pydantic
- **Database**: asyncpg, alembic
- **Security**: cryptography, python-dotenv
- **Development**: black, isort, pytest

## Security Considerations
- Environment variables for all sensitive configuration
- Database connection encryption in transit
- Secure key management for credential encryption
- No hardcoded secrets in source code
- Proper input validation and sanitization

## Testing Strategy
- Unit tests for database models and utilities
- Integration tests for database connectivity
- Health check endpoint validation
- Container startup and connectivity tests
- Security function testing with mock data

## Success Criteria
- [ ] Docker containers start successfully
- [ ] Database connection established and healthy
- [ ] Health check endpoint returns 200 OK
- [ ] Database tables created with correct schema
- [ ] Application starts without errors
- [ ] All tests pass with minimum 80% coverage

## Rollback Plan
- Database migrations include rollback capabilities
- Docker volumes can be removed to reset state
- Environment configuration is version controlled
- No external dependencies affected by this phase

## Future Dependencies
This foundation enables subsequent phases:
- Phase 2: Web3 Authentication & User Dashboard
- Phase 3: Core Trading Engine Integration
- Phase 4: Secure Webhook Implementation
- Phase 5: Background Position Monitoring

## Open Questions
- Database hosting strategy (local development vs cloud production)
- Encryption key management approach
- Log aggregation and monitoring setup
- Backup and disaster recovery requirements

## References
- Master Plan: Phase 1 - Foundation & Database Setup
- Project Context: openspec/project.md
- Technology Stack specifications