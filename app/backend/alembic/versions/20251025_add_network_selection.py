"""Add per-user network selection support

Revision ID: 20251025_network
Revises: 20251024_initial
Create Date: 2025-10-25 14:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '20251025_network'
down_revision: Union[str, None] = '20251024_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add dydx_network_id column to users table
    op.add_column('users', sa.Column('dydx_network_id', sa.Integer(), nullable=True, server_default='11155111'))


def downgrade() -> None:
    # Drop dydx_network_id column
    op.drop_column('users', 'dydx_network_id')
