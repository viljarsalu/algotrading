"""Add testnet and mainnet mnemonic columns

Revision ID: 20251025_add_mnemonics
Revises: 20251024_initial
Create Date: 2025-10-25 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '20251025_add_mnemonics'
down_revision: Union[str, None] = '20251024_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to users table
    op.add_column('users', sa.Column('encrypted_dydx_testnet_mnemonic', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True))
    op.add_column('users', sa.Column('encrypted_dydx_mainnet_mnemonic', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True))
    op.add_column('users', sa.Column('dydx_network_id', sa.Integer(), nullable=True))


def downgrade() -> None:
    # Remove columns from users table
    op.drop_column('users', 'dydx_network_id')
    op.drop_column('users', 'encrypted_dydx_mainnet_mnemonic')
    op.drop_column('users', 'encrypted_dydx_testnet_mnemonic')
