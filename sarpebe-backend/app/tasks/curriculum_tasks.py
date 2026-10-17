import asyncio
import io
from uuid import UUID
from celery.utils.log import get_task_logger
from pypdf import PdfReader

from app.core import storage
from app.tasks.celery_app import celery_app
from app.db.session import task_session_scope
from app.db.models.curriculum_document import CurriculumDocument
from app.db.models.document_chunk import DocumentChunk
from app.db.repositories.curriculum_document_repository import curriculum_document_repo
from app.utils.chunking import semantic_chunk_text
from app.core.services.embedding_service import embedding_service

logger = get_task_logger(__name__)

EMBEDDING_BATCH_SIZE = 10

async def _mark_failed(session_factory, doc_id: UUID) -> None:
    async with session_factory() as db:
        doc = await db.get(CurriculumDocument, doc_id)
        if doc:
            doc.status = "failed"
            await db.commit()

async def _process_curriculum_document(doc_id_str: str, admin_id_str: str) -> None:
    doc_id = UUID(doc_id_str)
    admin_id = UUID(admin_id_str)

    async with task_session_scope() as session_factory:
        try:
            async with session_factory() as db:
                # 1. Fetch document record
                doc = await db.get(CurriculumDocument, doc_id)
                if not doc:
                    logger.error(f"CurriculumDocument {doc_id} not found.")
                    return

                # 2. Download the PDF from storage and parse it page by page
                pdf_bytes = await asyncio.to_thread(storage.download_pdf, storage.curriculum_storage_path(doc.id))
                pages = []
                reader = PdfReader(io.BytesIO(pdf_bytes))
                for i, page in enumerate(reader.pages):
                    page_text = page.extract_text()
                    if page_text:
                        pages.append({"page_number": i + 1, "text": page_text})

                # 3. Chunk text
                chunks = semantic_chunk_text(pages)
                if not chunks:
                    doc.status = "failed"
                    await db.commit()
                    logger.error(f"Could not extract any text from the PDF {doc_id}.")
                    return

                # 4. Re-ingestion must be idempotent: drop chunks from any earlier attempt.
                await curriculum_document_repo.delete_chunks(db, doc.id)

                # 5. Embed in batches and stage the chunks
                for i in range(0, len(chunks), EMBEDDING_BATCH_SIZE):
                    # Stop quietly if the admin deleted the document while it was processing.
                    still_exists = await db.get(CurriculumDocument, doc_id, populate_existing=True)
                    if not still_exists:
                        logger.info(f"Document {doc_id} was deleted during processing; aborting.")
                        await db.rollback()
                        return

                    batch = chunks[i:i + EMBEDDING_BATCH_SIZE]
                    embeddings = await embedding_service.embed_texts(
                        [chunk_data["text"] for chunk_data in batch], admin_id
                    )
                    for chunk_data, embedding in zip(batch, embeddings):
                        db.add(DocumentChunk(
                            document_id=doc.id,
                            chunk_content=chunk_data["text"],
                            embedding=embedding,
                            page_number=chunk_data["page_number"],
                            grade_level=doc.grade_level,
                            subject=doc.subject,
                        ))

                # 6. Mark completed and commit chunks atomically
                doc.status = "completed"
                await db.commit()
                logger.info(f"Successfully processed curriculum document {doc_id}")

        except Exception as e:
            logger.exception(f"Fatal error processing document {doc_id}: {e}")
            await _mark_failed(session_factory, doc_id)

@celery_app.task(bind=True, name="tasks.process_curriculum_document", soft_time_limit=1500, time_limit=1800)
def process_curriculum_document_task(self, doc_id: str, admin_id: str):
    """
    Synchronous Celery task wrapper that downloads the PDF, extracts text, chunks it,
    computes embeddings, and saves to the database.
    """
    logger.info(f"Starting background processing for curriculum document {doc_id}")
    asyncio.run(_process_curriculum_document(doc_id, admin_id))
