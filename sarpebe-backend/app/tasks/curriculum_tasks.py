import asyncio
import os
import tempfile
import urllib.request
from uuid import UUID
from celery.utils.log import get_task_logger
from pypdf import PdfReader

from app.tasks.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.db.models.curriculum_document import CurriculumDocument
from app.db.models.document_chunk import DocumentChunk
from app.utils.chunking import semantic_chunk_text
from app.core.services.embedding_service import embedding_service

logger = get_task_logger(__name__)

async def _process_curriculum_document(doc_id_str: str, admin_id_str: str, grade_level: str, subject: str) -> None:
    async with AsyncSessionLocal() as db:
        doc_id = UUID(doc_id_str)
        admin_id = UUID(admin_id_str)

        # 1. Fetch document record
        doc = await db.get(CurriculumDocument, doc_id)
        if not doc:
            logger.error(f"CurriculumDocument {doc_id} not found.")
            return

        url = doc.url_path
        tmp_path = ""
        try:
            # 2. Download the PDF from the URL
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as response:
                    tmp.write(response.read())
                tmp_path = tmp.name

            # 3. Parse PDF
            pages = []
            reader = PdfReader(tmp_path)
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    pages.append({"page_number": i + 1, "text": page_text})

            # 4. Chunk text
            chunks = semantic_chunk_text(pages)
            if not chunks:
                doc.status = "failed"
                await db.commit()
                logger.error(f"Could not extract any text from the PDF {doc_id}.")
                return

            # 5. Embed and save chunks
            # Batch process embeddings
            BATCH_SIZE = 10
            for i in range(0, len(chunks), BATCH_SIZE):
                batch = chunks[i:i + BATCH_SIZE]

                # Create concurrent tasks for the batch
                embedding_tasks = [
                    embedding_service.embed_text(db, chunk_data["text"], admin_id)
                    for chunk_data in batch
                ]

                # Wait for all embeddings in this batch to complete
                embeddings = await asyncio.gather(*embedding_tasks)

                # Add to database
                for chunk_data, embedding in zip(batch, embeddings):
                    chunk_obj = DocumentChunk(
                        document_id=doc.id,
                        chunk_content=chunk_data["text"],
                        embedding=embedding,
                        page_number=chunk_data["page_number"],
                        grade_level=grade_level,
                        subject=subject
                    )
                    db.add(chunk_obj)

            # 6. Update document status to completed
            doc.status = "completed"
            await db.commit()
            logger.info(f"Successfully processed curriculum document {doc_id}")

        except Exception as e:
            logger.exception(f"Fatal error processing document {doc_id}: {e}")
            await db.rollback()

            # Update to failed
            async with AsyncSessionLocal() as fallback_db:
                failed_doc = await fallback_db.get(CurriculumDocument, doc_id)
                if failed_doc:
                    failed_doc.status = "failed"
                    await fallback_db.commit()
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)

@celery_app.task(bind=True, name="tasks.process_curriculum_document")
def process_curriculum_document_task(self, doc_id: str, admin_id: str, grade_level: str, subject: str):
    """
    Synchronous Celery task wrapper that downloads the PDF, extracts text, chunks it,
    computes embeddings, and saves to the database.
    """
    logger.info(f"Starting background processing for curriculum document {doc_id}")
    asyncio.run(_process_curriculum_document(doc_id, admin_id, grade_level, subject))
