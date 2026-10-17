"""
Re-ingests curriculum documents with the current pipeline (table-aware reading, heading-aware
chunking, contextual embeddings, normalized vectors). Run from sarpebe-backend/:

    python -m scripts.reindex_documents                 # documents still on an older ingest_version
    python -m scripts.reindex_documents --all           # every document
    python -m scripts.reindex_documents --id <uuid>     # one document

Safe to run repeatedly: each document's chunks are replaced inside one transaction. Embedding costs
are logged against the first admin account.
"""
import argparse
import asyncio
import sys
from uuid import UUID

from sqlalchemy import select

from app.core import storage
from app.core.services.ingestion_service import INGEST_VERSION, IngestError, ingest_document
from app.db.models.curriculum_document import CurriculumDocument
from app.db.models.profile import Profile
from app.db.session import AsyncSessionLocal


async def main(reindex_all: bool, only_id: UUID | None) -> int:
    async with AsyncSessionLocal() as db:
        admin = (await db.execute(select(Profile).where(Profile.role == "admin").limit(1))).scalar_one_or_none()
        if not admin:
            print("No admin account found; embedding costs need a user to be logged against.")
            return 1

        query = select(CurriculumDocument).order_by(CurriculumDocument.uploaded_at)
        if only_id:
            query = query.where(CurriculumDocument.id == only_id)
        elif not reindex_all:
            query = query.where(CurriculumDocument.ingest_version < INGEST_VERSION)
        documents = list((await db.execute(query)).scalars().all())

    if not documents:
        print("Nothing to reindex.")
        return 0

    failures = 0
    for document in documents:
        label = f"{document.title} ({document.id})"
        async with AsyncSessionLocal() as db:
            try:
                pdf_bytes = storage.download_pdf(storage.curriculum_storage_path(document.id))
                result = await ingest_document(db, document.id, pdf_bytes, admin.id)
                note = f", {len(result.warnings)} warning(s)" if result.warnings else ""
                print(f"ok      {label}: {result.chunk_count} chunks{note}")
            except IngestError as error:
                await db.rollback()
                failures += 1
                print(f"failed  {label}: {error.message}")
            except Exception as error:  # a missing storage file, a network error, ...
                await db.rollback()
                failures += 1
                print(f"failed  {label}: {error}")
    return 1 if failures else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--all", action="store_true", help="reindex every document, not only outdated ones")
    parser.add_argument("--id", type=UUID, help="reindex a single document")
    args = parser.parse_args()
    sys.exit(asyncio.run(main(args.all, args.id)))
