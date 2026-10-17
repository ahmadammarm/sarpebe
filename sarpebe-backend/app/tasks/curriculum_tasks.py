import asyncio
from uuid import UUID
from celery.utils.log import get_task_logger

from app.core import storage
from app.core.services.ingestion_service import IngestError, ingest_document
from app.db.models.curriculum_document import CurriculumDocument
from app.db.session import task_session_scope
from app.tasks.celery_app import celery_app

logger = get_task_logger(__name__)


async def _mark_failed(session_factory, doc_id: UUID, reason: str | None = None) -> None:
    async with session_factory() as db:
        doc = await db.get(CurriculumDocument, doc_id)
        if doc:
            doc.status = "failed"
            if reason:
                doc.ingest_warnings = [reason]
            await db.commit()


async def _process_curriculum_document(doc_id_str: str, admin_id_str: str) -> None:
    doc_id = UUID(doc_id_str)
    admin_id = UUID(admin_id_str)

    async with task_session_scope() as session_factory:
        try:
            async with session_factory() as db:
                doc = await db.get(CurriculumDocument, doc_id)
                if not doc:
                    logger.error(f"CurriculumDocument {doc_id} not found.")
                    return

                pdf_bytes = await asyncio.to_thread(storage.download_pdf, storage.curriculum_storage_path(doc.id))
                result = await ingest_document(db, doc_id, pdf_bytes, admin_id)

            if result.aborted:
                return
            logger.info(f"Processed curriculum document {doc_id}: {result.chunk_count} chunks, {len(result.warnings)} warnings")

        except IngestError as e:
            logger.error(f"Could not index document {doc_id}: {e.message}")
            await _mark_failed(session_factory, doc_id, e.message)
        except Exception as e:
            logger.exception(f"Fatal error processing document {doc_id}: {e}")
            await _mark_failed(session_factory, doc_id, "Dokumen gagal diproses. Coba unggah ulang.")


@celery_app.task(bind=True, name="tasks.process_curriculum_document", soft_time_limit=1500, time_limit=1800)
def process_curriculum_document_task(self, doc_id: str, admin_id: str):
    """
    Synchronous Celery task wrapper: downloads the PDF, extracts text and tables, chunks it,
    embeds the chunks and saves them.
    """
    logger.info(f"Starting background processing for curriculum document {doc_id}")
    asyncio.run(_process_curriculum_document(doc_id, admin_id))
