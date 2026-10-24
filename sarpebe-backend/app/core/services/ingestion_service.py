import asyncio
import logging
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.exceptions import AppError
from app.core.services.embedding_service import embedding_service
from app.core.services.ocr_service import ocr_service
from app.db.models.curriculum_document import CurriculumDocument
from app.db.models.document_chunk import DocumentChunk
from app.db.repositories.curriculum_document_repository import curriculum_document_repo
from app.utils.chunking import blocks_from_plain_text, chunk_document
from app.utils.fase import fase_for_grade
from app.utils.pdf_extract import ExtractionResult, extract_pdf, no_text_warning

logger = logging.getLogger(__name__)

INGEST_VERSION = 2
EMBEDDING_BATCH_SIZE = 10


class IngestError(AppError):
    """Raised when a document cannot be turned into searchable chunks."""
    code = "ingest_failed"


@dataclass(frozen=True)
class IngestResult:
    chunk_count: int
    warnings: list[str]
    aborted: bool = False  # the document was deleted while it was being processed


NO_TEXT_MESSAGE = "PDF tidak berisi teks yang bisa dibaca. File hasil pindai belum didukung."
NO_TEXT_AFTER_OCR_MESSAGE = (
    "PDF tidak berisi teks yang bisa dibaca, dan OCR belum berhasil membaca halamannya. "
    "Coba proses ulang nanti atau unggah PDF yang lebih jelas."
)


async def apply_ocr(extraction: ExtractionResult, pdf_bytes: bytes, user_id: UUID) -> None:
    """
    Fills pages that have no text layer with an OCR transcription, up to `ocr_max_pages` pages.
    Pages that are read lose their "no text" warning; pages that could not be read, or are past
    the limit, keep it. Blank pages stay empty and keep it too.
    """
    unreadable = extraction.pages_without_text
    selected = unreadable[: settings.ocr_max_pages]
    result = await ocr_service.read_pages(pdf_bytes, selected, user_id)

    pages = {page.number: page for page in extraction.pages}
    read = [number for number, text in result.texts.items() if text]
    for number in read:
        pages[number].blocks = blocks_from_plain_text(result.texts[number], number)

    read_warnings = {no_text_warning(number) for number in read}
    extraction.warnings = [warning for warning in extraction.warnings if warning not in read_warnings]
    if read:
        extraction.warnings.append(f"{len(read)} halaman dibaca dengan OCR; periksa hasilnya.")
    if len(unreadable) > len(selected):
        extraction.warnings.append(
            f"OCR hanya membaca {len(selected)} halaman pertama yang tidak berisi teks; sisanya dilewati."
        )


def contextual_text(
    *,
    document_title: str,
    grade_level: str | None,
    subject: str | None,
    heading: str | None,
    content: str,
) -> str:
    """
    What actually gets embedded: the chunk preceded by a one-line header saying where it comes from.
    A bare sentence like "Peserta didik mampu menganalisis..." says little on its own; with the
    header the vector also encodes the document, grade, phase, subject and section. Only the
    original content is stored and shown.
    """
    parts = [document_title]
    if grade_level:
        fase = fase_for_grade(grade_level)
        parts.append(f"Kelas {grade_level}" + (f" (Fase {fase.code})" if fase else ""))
    if subject:
        parts.append(subject)
    if heading:
        parts.append(heading)
    return " | ".join(parts) + "\n" + content


async def ingest_document(
    db: AsyncSession,
    document_id: UUID,
    pdf_bytes: bytes,
    user_id: UUID,
) -> IngestResult:
    """
    Reads the PDF, chunks it, embeds the chunks and stores them, replacing any earlier chunks of
    the document (so re-ingesting is safe). Stops quietly if the document is deleted midway.
    """
    document = await db.get(CurriculumDocument, document_id)
    if not document:
        raise IngestError("Dokumen tidak ditemukan.")

    try:
        extraction = await asyncio.to_thread(extract_pdf, pdf_bytes)
    except Exception as error:  # both readers failed: the file is corrupt or not a PDF
        logger.warning("Could not read PDF for document %s: %s", document_id, error)
        raise IngestError("PDF tidak dapat dibaca. File mungkin rusak.") from error

    if settings.ocr_enabled and extraction.pages_without_text:
        await apply_ocr(extraction, pdf_bytes, user_id)
    if not extraction.has_text:
        raise IngestError(
            NO_TEXT_AFTER_OCR_MESSAGE if settings.ocr_enabled else NO_TEXT_MESSAGE
        )

    chunks = chunk_document(extraction)
    if not chunks:
        raise IngestError("Tidak ada teks yang bisa diindeks dari PDF ini.")

    await curriculum_document_repo.delete_chunks(db, document.id)

    for start in range(0, len(chunks), EMBEDDING_BATCH_SIZE):
        # Stop if the admin deleted the document while it was processing.
        if not await db.get(CurriculumDocument, document_id, populate_existing=True):
            logger.info("Document %s was deleted during processing; aborting.", document_id)
            await db.rollback()
            return IngestResult(chunk_count=0, warnings=extraction.warnings, aborted=True)

        batch = chunks[start:start + EMBEDDING_BATCH_SIZE]
        embeddings = await embedding_service.embed_texts(
            [
                contextual_text(
                    document_title=document.title,
                    grade_level=document.grade_level,
                    subject=document.subject,
                    heading=chunk.heading,
                    content=chunk.text,
                )
                for chunk in batch
            ],
            user_id,
            purpose="document",
        )
        for chunk, embedding in zip(batch, embeddings):
            db.add(DocumentChunk(
                document_id=document.id,
                chunk_content=chunk.text,
                embedding=embedding,
                page_number=chunk.page_number,
                page_end=chunk.page_end,
                heading=chunk.heading,
                chunk_type=chunk.chunk_type,
                grade_level=document.grade_level,
                subject=document.subject,
                embedding_model=settings.gemini_embedding_model,
            ))

    document.status = "completed"
    document.ingest_version = INGEST_VERSION
    document.ingest_warnings = extraction.warnings or None
    await db.commit()
    return IngestResult(chunk_count=len(chunks), warnings=extraction.warnings)
