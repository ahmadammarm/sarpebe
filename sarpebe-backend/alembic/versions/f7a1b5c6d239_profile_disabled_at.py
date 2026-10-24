"""profiles.disabled_at: lets an administrator block an account without deleting it

Revision ID: f7a1b5c6d239
Revises: e6f0a4b5c128
Create Date: 2026-10-24 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'f7a1b5c6d239'
down_revision: Union[str, Sequence[str], None] = 'e6f0a4b5c128'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Nullable: every existing account stays active.
    op.add_column("profiles", sa.Column("disabled_at", sa.TIMESTAMP(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("profiles", "disabled_at")
