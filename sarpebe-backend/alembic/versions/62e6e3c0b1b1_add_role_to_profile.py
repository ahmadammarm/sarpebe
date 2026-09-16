"""add role to profile

Revision ID: 62e6e3c0b1b1
Revises: 949842977c3c
Create Date: 2026-09-16 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '62e6e3c0b1b1'
down_revision: Union[str, None] = '949842977c3c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add role column with default 'user'
    op.add_column('profiles', sa.Column('role', sa.String(), server_default='user', nullable=False))


def downgrade() -> None:
    op.drop_column('profiles', 'role')
