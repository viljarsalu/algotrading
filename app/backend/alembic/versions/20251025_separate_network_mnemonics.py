"""Separate mnemonics for testnet and mainnet

Revision ID: 20251025_separate_mnemonics
Revises: 20251025_network
Create Date: 2025-10-25 14:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '20251025_separate_mnemonics'
down_revision: Union[str, None] = '20251025_network'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add separate mnemonic columns for testnet and mainnet
    op.add_column('users', sa.Column('encrypted_dydx_testnet_mnemonic', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True))
    op.add_column('users', sa.Column('encrypted_dydx_mainnet_mnemonic', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True))
    
    # Drop old single mnemonic column if it exists
    try:
        op.drop_column('users', 'encrypted_dydx_private_key')
    except Exception:
        pass  # Column might not exist in all environments


def downgrade() -> None:
    # Restore old single mnemonic column
    op.add_column('users', sa.Column('encrypted_dydx_private_key', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True))
    
    # Drop new separate columns
    op.drop_column('users', 'encrypted_dydx_testnet_mnemonic')
    op.drop_column('users', 'encrypted_dydx_mainnet_mnemonic')
