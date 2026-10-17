"""add job_id to lesson_plans and grade/subject to curriculum_documents

Revision ID: a3c1d9e47b20
Revises: 5f8613dc7ef8
Create Date: 2026-10-17 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3c1d9e47b20'
down_revision: Union[str, Sequence[str], None] = '5f8613dc7ef8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('lesson_plans', sa.Column('job_id', sa.String(), nullable=True))
    op.create_index(op.f('ix_lesson_plans_job_id'), 'lesson_plans', ['job_id'], unique=False)

    op.add_column('curriculum_documents', sa.Column('grade_level', sa.String(), nullable=True))
    op.add_column('curriculum_documents', sa.Column('subject', sa.String(), nullable=True))

    # Chunk labels are matched exactly during retrieval, so store them in canonical form
    # (trimmed, whitespace-collapsed, lower-cased) to match app.utils.labels.normalize_label.
    op.execute(
        r"""
        UPDATE document_chunks
        SET grade_level = lower(regexp_replace(btrim(grade_level), '\s+', ' ', 'g')),
            subject = lower(regexp_replace(btrim(subject), '\s+', ' ', 'g'))
        """
    )

    # Backfill document-level labels from their (already normalized) chunks.
    op.execute(
        """
        UPDATE curriculum_documents d
        SET grade_level = c.grade_level, subject = c.subject
        FROM (
            SELECT DISTINCT ON (document_id) document_id, grade_level, subject
            FROM document_chunks
            ORDER BY document_id
        ) c
        WHERE c.document_id = d.id
        """
    )


def downgrade() -> None:
    op.drop_column('curriculum_documents', 'subject')
    op.drop_column('curriculum_documents', 'grade_level')
    op.drop_index(op.f('ix_lesson_plans_job_id'), table_name='lesson_plans')
    op.drop_column('lesson_plans', 'job_id')
