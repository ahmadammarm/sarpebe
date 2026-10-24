"""lesson plan index on (user_id, created_at) for the list and the generation quota

Revision ID: e6f0a4b5c128
Revises: d5e9f3a4b017
Create Date: 2026-10-24 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'e6f0a4b5c128'
down_revision: Union[str, Sequence[str], None] = 'd5e9f3a4b017'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index("ix_lesson_plans_user_created", "lesson_plans", ["user_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_lesson_plans_user_created", table_name="lesson_plans")
