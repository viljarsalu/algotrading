# Project Context

## Purpose
A secure, reliable, and user-friendly SaaS platform that empowers cryptocurrency traders to automate their strategies on the dYdX v4 exchange. The service features modern Web3 login, private dashboard for credential management, and a highly secure two-factor webhook system for executing trades based on TradingView alerts. Each user maintains complete privacy with notifications delivered to their personal Telegram channel.

## Tech Stack
- **Backend**: Python 3.12, FastAPI framework with async support
- **Frontend**: Vanilla JavaScript with Jinja2 templating
- **Styling**: Tailwind CSS for responsive UI
- **Database**: PostgreSQL 14 with SQLModel ORM and Alembic migrations
- **Web3 Integration**: web3.py for wallet authentication and signature verification
- **Trading**: dydx-v4-client for dYdX exchange integration
- **Notifications**: python-telegram-bot for secure user notifications
- **Background Jobs**: Celery with Redis for asynchronous task processing
- **Data Analysis**: Pandas, NumPy, and Matplotlib for trading analytics
- **Configuration**: Dynaconf for environment-based configuration management
- **Logging**: Structlog for structured logging and monitoring
- **Error Tracking**: Sentry for production error monitoring and alerting
- **Rate Limiting**: SlowAPI for API protection and abuse prevention
- **Real-time**: WebSockets for live trading data and notifications
- **Containerization**: Multi-stage Docker builds with Docker Compose orchestration
- **Security**: AES-256 encryption for sensitive credentials with comprehensive middleware

## Project Conventions

### Code Style
- **Language**: Python (PEP 8 compliant with Black formatting)
- **Naming**: snake_case for functions/variables, PascalCase for classes, SCREAMING_SNAKE_CASE for constants
- **Imports**: Group standard library, third-party, then local imports (alphabetically within groups)
- **Type Hints**: Use comprehensive type annotations for all function parameters and return values
- **Documentation**: Google-style docstrings for all public functions and classes
- **Line Length**: Maximum 88 characters (Black default)
- **Error Handling**: Explicit exception handling with descriptive error messages

### Architecture Patterns
- **Multi-tenant Architecture**: Each user has isolated credentials and webhook endpoints
- **Stateless Design**: All trading functions accept user credentials as parameters
- **Repository Pattern**: Database operations centralized through repository classes
- **Service Layer**: Business logic separated into dedicated service classes
- **Dependency Injection**: FastAPI dependency system for database sessions and configuration
- **Background Jobs**: Celery-based task queue with Redis for asynchronous processing
- **Worker Pattern**: Dedicated position monitoring workers with health checks and graceful shutdown
- **Health Check Pattern**: Kubernetes-ready health endpoints for liveness and readiness probes
- **Middleware Pattern**: Comprehensive security, validation, and rate limiting middleware
- **Configuration Pattern**: Environment-based configuration with Dynaconf and validation
- **Structured Logging**: Centralized logging with structured data for monitoring and debugging

### Testing Strategy
- **Unit Tests**: Test individual functions and classes in isolation
- **Integration Tests**: Test API endpoints and database operations
- **E2E Tests**: Full webhook-to-trade execution flows
- **Test Coverage**: Minimum 80% coverage for core business logic
- **Mocking**: Use pytest-mock for external service dependencies (dYdX, Telegram)
- **Test Data**: Factory pattern for creating test users and positions
- **Security Tests**: Validate encryption, authentication, and authorization

### Git Workflow
- **Branch Strategy**: feature/, bugfix/, hotfix/, release/ prefixes
- **Commits**: Conventional commits format - type(scope): description
- **Pull Requests**: Required for all changes with description and testing instructions
- **Code Review**: All PRs require approval from at least one maintainer
- **Main Branch**: Protected with required status checks and PR reviews

## Deployment Architecture
- **Container Strategy**: Multi-stage Docker builds for optimized production images
- **Orchestration**: Docker Compose for local development and single-node deployment
- **Database**: PostgreSQL 14 with persistent volumes and initialization scripts
- **Health Monitoring**: Comprehensive health checks for both application and database
- **Service Discovery**: Container networking with dedicated bridge network
- **Data Persistence**: Named volumes for database data with proper backup strategy
- **Environment Management**: Production-ready configuration with secrets management
- **Scaling Ready**: Architecture supports horizontal scaling with Redis clustering

## Domain Context
**DeFi Trading Automation**: This platform operates in the decentralized finance (DeFi) space, specifically automated trading on perpetual contracts. Key concepts include:
- **dYdX v4**: Layer 2 Ethereum protocol for perpetual trading with low fees and fast execution
- **Web3 Authentication**: Users sign messages with their wallet instead of traditional passwords
- **Webhook Trading**: TradingView alerts trigger automated position management
- **Risk Management**: Take Profit (TP) and Stop Loss (SL) orders for position protection
- **Non-custodial**: Service never holds user funds, only executes trades with provided credentials

## Important Constraints
- **Security First**: All user credentials must be encrypted using AES-256 with comprehensive middleware protection
- **Non-custodial Architecture**: Service cannot withdraw funds, only trade on user's behalf
- **Two-factor Webhook Security**: All trades require both URL path and body validation
- **Resource Limits**: SlowAPI rate limiting with configurable thresholds to prevent abuse
- **Regulatory Compliance**: No US users due to CFTC regulations on perpetual trading
- **Privacy**: Complete user isolation - no shared state between tenants
- **Uptime Requirements**: 99.9% uptime SLA for trading operations with health check monitoring
- **Data Protection**: Request size limits and input validation to prevent payload attacks
- **Error Handling**: Comprehensive error tracking with Sentry for production monitoring
- **Performance**: Background job processing to ensure API responsiveness during peak loads

## External Dependencies
- **dYdX v4 Protocol**: Primary trading venue for perpetual contracts
- **Ethereum Network**: For Web3 authentication and transaction settlement
- **TradingView**: Alert generation for trading signals
- **Telegram API**: Secure notification delivery to users
- **Redis**: In-memory data structure store for Celery broker and caching
- **Sentry**: Error tracking and performance monitoring service
- **Docker Hub**: Container image distribution and registry
- **PostgreSQL Cloud**: Production database hosting (AWS RDS/Neon)
- **Web3 Providers**: Ethereum node providers for blockchain interactions
