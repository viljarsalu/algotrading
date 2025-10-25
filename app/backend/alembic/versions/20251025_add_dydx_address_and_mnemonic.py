"""Add dYdX address and unified mnemonic fields.

Revision ID: 20251025_add_dydx_address_and_mnemonic
Revises: 20251025_add_testnet_mainnet_mnemonics
Create Date: 2025-10-25 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision = '20251025_add_dydx_address_and_mnemonic'
down_revision = '20251025_add_testnet_mainnet_mnemonics'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to users table
    op.add_column('users', sa.Column('dydx_address', sqlmodel.sql.sqltypes.AutoString(length=43), nullable=True))
    op.add_column('users', sa.Column('encrypted_dydx_mnemonic', sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True))


def downgrade() -> None:
    # Remove columns from users table
    op.drop_column('users', 'encrypted_dydx_mnemonic')
    op.drop_column('users', 'dydx_address')
