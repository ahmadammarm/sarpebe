"""AI pipeline metadata: plan traceability, chunk structure, document ingestion info

Revision ID: c4d8e1f2a903
Revises: b7e2f4a91c35
Create Date: 2026-10-18 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'c4d8e1f2a903'
down_revision: Union[str, Sequence[str], None] = 'b7e2f4a91c35'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Every existing plan keeps the original content format (schema_version 1).
    op.add_column('lesson_plans', sa.Column('schema_version', sa.Integer(), server_default='1', nullable=False))
    op.add_column('lesson_plans', sa.Column('request_options', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('lesson_plans', sa.Column('prompt_version', sa.String(), nullable=True))
    op.add_column('lesson_plans', sa.Column('model_name', sa.String(), nullable=True))
    op.add_column('lesson_plans', sa.Column('generation_meta', postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    op.add_column('document_chunks', sa.Column('heading', sa.Text(), nullable=True))
    op.add_column('document_chunks', sa.Column('chunk_type', sa.String(), server_default='text', nullable=False))
    op.add_column('document_chunks', sa.Column('page_end', sa.Integer(), nullable=True))
    op.add_column('document_chunks', sa.Column('embedding_model', sa.String(), nullable=True))

    # Existing documents were produced by the first ingestion pipeline (version 1).
    op.add_column('curriculum_documents', sa.Column('ingest_version', sa.Integer(), server_default='1', nullable=False))
    op.add_column('curriculum_documents', sa.Column('ingest_warnings', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade() -> None:
    op.drop_column('curriculum_documents', 'ingest_warnings')
    op.drop_column('curriculum_documents', 'ingest_version')
    op.drop_column('document_chunks', 'embedding_model')
    op.drop_column('document_chunks', 'page_end')
    op.drop_column('document_chunks', 'chunk_type')
    op.drop_column('document_chunks', 'heading')
    op.drop_column('lesson_plans', 'generation_meta')
    op.drop_column('lesson_plans', 'model_name')
    op.drop_column('lesson_plans', 'prompt_version')
    op.drop_column('lesson_plans', 'request_options')
    op.drop_column('lesson_plans', 'schema_version')
