"""retrieval indexes: full-text search column, label index and HNSW vector index

Revision ID: d5e9f3a4b017
Revises: c4d8e1f2a903
Create Date: 2026-10-18 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'd5e9f3a4b017'
down_revision: Union[str, Sequence[str], None] = 'c4d8e1f2a903'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Full-text search over heading + content. A generated column stays in sync on every insert
    # and update without application code; the 'indonesian' configuration stems Indonesian words.
    op.execute(
        """
        ALTER TABLE document_chunks
        ADD COLUMN search_vector tsvector
        GENERATED ALWAYS AS (
            to_tsvector('indonesian', coalesce(heading, '') || ' ' || chunk_content)
        ) STORED
        """
    )
    op.execute(
        "CREATE INDEX ix_document_chunks_search_vector ON document_chunks USING gin (search_vector)"
    )

    # Every search filters on grade AND subject, so index the pair.
    op.execute(
        "CREATE INDEX ix_document_chunks_grade_subject ON document_chunks (grade_level, subject)"
    )

    # Approximate nearest-neighbour index for cosine distance. On a small table the planner still
    # scans sequentially, which is fine; this keeps search fast as documents accumulate.
    # Filtered queries rely on hnsw.iterative_scan (pgvector >= 0.8), set per query by the app.
    op.execute(
        """
        CREATE INDEX ix_document_chunks_embedding_hnsw
        ON document_chunks USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_document_chunks_embedding_hnsw")
    op.execute("DROP INDEX IF EXISTS ix_document_chunks_grade_subject")
    op.execute("DROP INDEX IF EXISTS ix_document_chunks_search_vector")
    op.execute("ALTER TABLE document_chunks DROP COLUMN IF EXISTS search_vector")
