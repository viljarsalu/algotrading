"""
Migration script to add 'side' column to positions table.
Run this script to update the database schema.
"""

import asyncio
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

async def add_side_column():
    """Add 'side' column to positions table if it doesn't exist."""
    
    # Get database URL from environment or use default
    import os
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/algotrading"
    )
    
    # Create async engine
    engine = create_async_engine(database_url, echo=True)
    
    try:
        async with engine.begin() as conn:
            # Check if column exists
            result = await conn.execute(
                text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='positions' AND column_name='side'
                """)
            )
            
            if result.fetchone():
                print("✓ Column 'side' already exists in positions table")
                return
            
            # Add the column
            print("Adding 'side' column to positions table...")
            await conn.execute(
                text("""
                    ALTER TABLE positions 
                    ADD COLUMN side VARCHAR(10) NOT NULL DEFAULT 'BUY'
                """)
            )
            await conn.commit()
            print("✓ Successfully added 'side' column to positions table")
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(add_side_column())
