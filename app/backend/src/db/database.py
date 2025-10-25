"""
Database connection and session management for dYdX Trading Service.

This module provides SQLAlchemy engine configuration, session management,
database initialization, and health monitoring capabilities.
"""

import os
import logging
from typing import Generator, Optional
from contextlib import contextmanager

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import text, event
import asyncio

from .models import create_tables, User, Position

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and sessions."""

    def __init__(self, database_url: Optional[str] = None):
        """Initialize database manager.

        Args:
            database_url: Database connection URL. If not provided,
                         uses DATABASE_URL environment variable.
        """
        self.database_url = database_url or os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("Database URL not provided")

        # Configure engine based on environment
        self.is_testing = os.getenv('APP_ENV') == 'testing'

        if self.is_testing:
            # Use in-memory SQLite for testing
            self.engine = create_async_engine(
                "sqlite+aiosqlite:///:memory:",
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
                echo=True  # Log SQL for testing
            )
        else:
            # Use connection pooling for production
            self.engine = create_async_engine(
                self.database_url,
                echo=os.getenv('DEBUG', 'false').lower() == 'true',
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,  # Recycle connections after 1 hour
            )

        # Create async session factory
        self.async_session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def initialize_database(self) -> None:
        """Initialize database with tables and seed data."""
        try:
            # Create all tables using async engine
            async with self.engine.begin() as conn:
                await conn.run_sync(create_tables)

            # Test connection with a simple query
            session = self.async_session_factory()
            try:
                result = await session.execute(text("SELECT 1"))
                result.fetchone()  # fetchone() is synchronous in SQLAlchemy 2.0
            finally:
                await session.close()

            logger.info("Database initialized successfully")

        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise

    async def check_health(self) -> dict:
        """Check database connection health.

        Returns:
            Dictionary with health status and metrics
        """
        health_info = {
            'status': 'unknown',
            'response_time_ms': None,
            'error': None
        }

        try:
            start_time = asyncio.get_event_loop().time()

            # Simple health check query using async session directly
            session = self.async_session_factory()
            try:
                result = await session.execute(text("SELECT 1 as health_check"))
                row = result.fetchone()  # fetchone() is synchronous in SQLAlchemy 2.0

                if row and row.health_check == 1:
                    end_time = asyncio.get_event_loop().time()
                    health_info.update({
                        'status': 'healthy',
                        'response_time_ms': round((end_time - start_time) * 1000, 2)
                    })
                else:
                    health_info.update({
                        'status': 'unhealthy',
                        'error': 'Unexpected health check response'
                    })
            finally:
                await session.close()

        except Exception as e:
            end_time = asyncio.get_event_loop().time()
            health_info.update({
                'status': 'unhealthy',
                'response_time_ms': round((end_time - start_time) * 1000, 2),
                'error': str(e)
            })

        return health_info

    @contextmanager
    def get_session(self) -> Generator[AsyncSession, None, None]:
        """Get database session with automatic cleanup.

        Yields:
            AsyncSession: Database session

        Example:
            async with db_manager.get_session() as session:
                user = await session.get(User, "0x123...")
                # Session automatically closed after context
        """
        session = self.async_session_factory()
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            session.rollback()
            raise
        finally:
            asyncio.create_task(session.close())

    async def get_user_by_wallet(self, wallet_address: str) -> Optional[User]:
        """Get user by wallet address.

        Args:
            wallet_address: Ethereum wallet address

        Returns:
            User instance or None if not found
        """
        session = self.async_session_factory()
        try:
            from sqlalchemy import select
            result = await session.execute(
                select(User).where(User.wallet_address == wallet_address)
            )
            return result.scalar_one_or_none()
        finally:
            await session.close()

    async def get_user_by_webhook_uuid(self, webhook_uuid: str) -> Optional[User]:
        """Get user by webhook UUID.

        Args:
            webhook_uuid: Webhook authentication UUID

        Returns:
            User instance or None if not found
        """
        session = self.async_session_factory()
        try:
            from sqlalchemy import select
            result = await session.execute(
                select(User).where(User.webhook_uuid == webhook_uuid)
            )
            return result.scalar_one_or_none()
        finally:
            await session.close()

    async def create_user(self, user: User) -> User:
        """Create new user.

        Args:
            user: User instance to create

        Returns:
            Created user instance

        Raises:
            ValueError: If user already exists or validation fails
        """
        session = self.async_session_factory()
        try:
            session.add(user)
            await session.commit()
            await session.refresh(user)
            logger.info(f"Created user: {user.wallet_address}")
            return user
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to create user: {e}")
            raise
        finally:
            await session.close()

    async def update_user(self, user: User) -> User:
        """Update existing user.

        Args:
            user: User instance with updated data

        Returns:
            Updated user instance

        Raises:
            ValueError: If user not found or validation fails
        """
        session = self.async_session_factory()
        try:
            session.add(user)
            await session.commit()
            await session.refresh(user)
            logger.info(f"Updated user: {user.wallet_address}")
            return user
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to update user: {e}")
            raise
        finally:
            await session.close()

    async def get_positions_by_user(self, wallet_address: str) -> list[Position]:
        """Get all positions for a user.

        Args:
            wallet_address: User's wallet address

        Returns:
            List of user's positions
        """
        session = self.async_session_factory()
        try:
            from sqlalchemy import select
            result = await session.execute(
                select(Position)
                .where(Position.user_address == wallet_address)
                .order_by(Position.opened_at.desc())
            )
            return result.scalars().all()
        finally:
            await session.close()

    async def get_open_positions(self, wallet_address: str) -> list[Position]:
        """Get open positions for a user.

        Args:
            wallet_address: User's wallet address

        Returns:
            List of user's open positions
        """
        session = self.async_session_factory()
        try:
            from sqlalchemy import select
            result = await session.execute(
                select(Position)
                .where(Position.user_address == wallet_address, Position.status == "open")
                .order_by(Position.opened_at.desc())
            )
            return result.scalars().all()
        finally:
            await session.close()

    async def create_position(self, position: Position) -> Position:
        """Create new position.

        Args:
            position: Position instance to create

        Returns:
            Created position instance
        """
        session = self.async_session_factory()
        try:
            session.add(position)
            await session.commit()
            await session.refresh(position)
            logger.info(f"Created position: {position.id} for user: {position.user_address}")
            return position
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to create position: {e}")
            raise
        finally:
            await session.close()

    async def update_position(self, position: Position) -> Position:
        """Update existing position.

        Args:
            position: Position instance with updated data

        Returns:
            Updated position instance
        """
        session = self.async_session_factory()
        try:
            position.updated_at = datetime.utcnow()
            session.add(position)
            await session.commit()
            await session.refresh(position)
            logger.info(f"Updated position: {position.id}")
            return position
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to update position: {e}")
            raise
        finally:
            await session.close()

    async def close(self) -> None:
        """Close database connections."""
        await self.engine.dispose()
        logger.info("Database connections closed")


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_database_manager() -> DatabaseManager:
    """Get or create global database manager instance."""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager


# Dependency for FastAPI
async def get_db():
    """FastAPI dependency for database sessions.

    Yields:
        AsyncSession: Database session for request lifecycle
    """
    db_manager = get_database_manager()
    session = db_manager.async_session_factory()
    try:
        yield session
    finally:
        await session.close()




# Utility functions for database operations

async def init_db() -> None:
    """Initialize database with tables."""
    db_manager = get_database_manager()
    await db_manager.initialize_database()


async def check_db_health() -> dict:
    """Check database health status."""
    db_manager = get_database_manager()
    return await db_manager.check_health()


async def create_sample_data() -> None:
    """Create sample data for development/testing."""
    db_manager = get_database_manager()

    # Create sample user if it doesn't exist
    sample_user = await db_manager.get_user_by_wallet("0x1234567890123456789012345678901234567890")
    if not sample_user:
        sample_user = User(
            wallet_address="0x1234567890123456789012345678901234567890",
            webhook_uuid="550e8400-e29b-41d4-a716-446655440000"
        )
        await db_manager.create_user(sample_user)

        # Create sample position
        sample_position = Position(
            user_address=sample_user.wallet_address,
            symbol="BTC-USD",
            entry_price=Decimal('45000.00'),
            size=Decimal('0.001'),
            dydx_order_id="sample_order_123"
        )
        await db_manager.create_position(sample_position)

        logger.info("Sample data created")