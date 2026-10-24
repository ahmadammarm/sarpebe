import asyncio
import io
import logging
from dataclasses import dataclass, field
from uuid import UUID

import pypdfium2
from google.genai import types
from pydantic import BaseModel, Field

from app.config import settings
from app.core.exceptions import ContentBlockedError, LLMOutputError, TransientLLMError
from app.core.llm_client import ensure_usable, generate_structured
from app.core.prompts.ocr import OCR_SYSTEM_INSTRUCTION, PAGE_REQUEST
from app.schemas.json_schema import to_gemini_schema

logger = logging.getLogger(__name__)

OCR_MAX_OUTPUT_TOKENS = 8000
PDF_POINTS_PER_INCH = 72

# A page that fails in one of these ways is skipped; the rest of the document is still read.
PAGE_ERRORS = (ContentBlockedError, LLMOutputError, TransientLLMError)


class OcrPage(BaseModel):
    text: str = Field(description="Teks halaman, disalin apa adanya. Kosong jika halaman tidak memuat teks.")


OCR_SCHEMA = to_gemini_schema(OcrPage)


@dataclass
class OcrResult:
    texts: dict[int, str] = field(default_factory=dict)  # page number -> transcription (may be empty)
    failed: list[int] = field(default_factory=list)


def _render_pages(pdf_bytes: bytes, page_numbers: list[int], dpi: int) -> dict[int, bytes]:
    """PNG bytes for the given 1-based pages. Synchronous and CPU-bound: call it in a thread."""
    images: dict[int, bytes] = {}
    pdf = pypdfium2.PdfDocument(pdf_bytes)
    try:
        for number in page_numbers:
            bitmap = pdf[number - 1].render(scale=dpi / PDF_POINTS_PER_INCH)
            buffer = io.BytesIO()
            bitmap.to_pil().save(buffer, format="PNG")
            images[number] = buffer.getvalue()
    finally:
        pdf.close()
    return images


async def _read_page(number: int, png: bytes, user_id: UUID, semaphore: asyncio.Semaphore) -> tuple[int, str | None]:
    """The transcription of one page, or None if the model could not be used for it."""
    async with semaphore:
        try:
            response = await generate_structured(
                model=settings.gemini_ocr_model,
                system_instruction=OCR_SYSTEM_INSTRUCTION,
                contents=[
                    types.Content(
                        role="user",
                        parts=[types.Part.from_bytes(data=png, mime_type="image/png"), types.Part(text=PAGE_REQUEST)],
                    )
                ],
                json_schema=OCR_SCHEMA,
                operation_type="ocr",
                user_id=user_id,
                temperature=0.0,
                max_output_tokens=OCR_MAX_OUTPUT_TOKENS,
            )
            text = OcrPage.model_validate_json(ensure_usable(response)).text
        except PAGE_ERRORS as error:
            logger.warning("OCR skipped page %s: %s", number, error)
            return number, None
        except ValueError:  # the answer was not the JSON we asked for
            logger.warning("OCR skipped page %s: answer did not match the schema", number)
            return number, None
        return number, text.strip()


class OcrService:
    @staticmethod
    async def read_pages(pdf_bytes: bytes, page_numbers: list[int], user_id: UUID) -> OcrResult:
        """
        Transcribes pages that have no text layer, at most `ocr_concurrency` at a time.
        A page that cannot be read is reported in `failed` instead of failing the document.
        """
        if not page_numbers:
            return OcrResult()

        images = await asyncio.to_thread(_render_pages, pdf_bytes, page_numbers, settings.ocr_render_dpi)
        semaphore = asyncio.Semaphore(settings.ocr_concurrency)
        answers = await asyncio.gather(*(_read_page(n, images[n], user_id, semaphore) for n in page_numbers))

        result = OcrResult()
        for number, text in answers:
            if text is None:
                result.failed.append(number)
            else:
                result.texts[number] = text
        return result

ocr_service = OcrService()
