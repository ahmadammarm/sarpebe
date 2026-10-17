import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.config import settings
from app.core.services import ingestion_service
from app.core.services.ingestion_service import IngestError, contextual_text, ingest_document
from app.db.models.curriculum_document import CurriculumDocument
from tests.unit.test_pdf_extract import blank_pdf, build_pdf

async_test = pytest.mark.asyncio(loop_scope="session")

USER_ID = uuid.uuid4()


class FakeDb:
    """Just enough of AsyncSession for ingestion. `gone_after` makes get() return None from then on."""

    def __init__(self, document, gone_after=None):
        self.document = document
        self.gone_after = gone_after
        self.get_calls = 0
        self.added = []
        self.commit = AsyncMock()
        self.rollback = AsyncMock()

    async def get(self, model, key, populate_existing=False):
        self.get_calls += 1
        if self.gone_after is not None and self.get_calls > self.gone_after:
            return None
        return self.document

    def add(self, obj):
        self.added.append(obj)


@pytest.fixture
def document():
    return CurriculumDocument(
        id=uuid.uuid4(), title="CP IPS.pdf", document_type="CP", url_path="http://x/doc.pdf",
        grade_level="9", subject="ips", status="processing",
    )


@pytest.fixture
def embedded(mocker):
    """Replaces the embedding call and records the texts it was asked to embed."""
    calls = []

    async def fake_embed(texts, user_id, *, purpose="document", lesson_plan_id=None):
        calls.append({"texts": list(texts), "purpose": purpose})
        return [[0.1] * 768 for _ in texts]

    mocker.patch.object(ingestion_service.embedding_service, "embed_texts", side_effect=fake_embed)
    mocker.patch.object(ingestion_service.curriculum_document_repo, "delete_chunks", new_callable=AsyncMock)
    return calls


def test_contextual_text_says_where_the_chunk_comes_from():
    text = contextual_text(
        document_title="CP IPS.pdf", grade_level="9", subject="ips",
        heading="Elemen Pemahaman", content="Peserta didik mampu menganalisis.",
    )
    assert text == "CP IPS.pdf | Kelas 9 (Fase D) | ips | Elemen Pemahaman\nPeserta didik mampu menganalisis."


def test_contextual_text_omits_what_is_missing():
    text = contextual_text(document_title="Dok", grade_level=None, subject=None, heading=None, content="Isi")
    assert text == "Dok\nIsi"
    free_text_grade = contextual_text(document_title="Dok", grade_level="X", subject=None, heading=None, content="Isi")
    assert free_text_grade == "Dok | Kelas X\nIsi"


@async_test
async def test_ingest_stores_chunks_with_structure_and_marks_the_document(document, embedded):
    db = FakeDb(document)

    result = await ingest_document(db, document.id, build_pdf(), USER_ID)

    assert result.chunk_count == len(db.added) >= 2
    kinds = {chunk.chunk_type for chunk in db.added}
    assert kinds == {"text", "table"}
    table = next(c for c in db.added if c.chunk_type == "table")
    assert table.chunk_content.startswith("| Elemen | Capaian |")
    assert table.heading == "Elemen Pemahaman IPS"
    assert all(c.embedding_model == settings.gemini_embedding_model for c in db.added)
    assert all((c.grade_level, c.subject) == ("9", "ips") for c in db.added)
    assert (document.status, document.ingest_version) == ("completed", ingestion_service.INGEST_VERSION)
    db.commit.assert_awaited_once()


@async_test
async def test_embedding_input_has_the_contextual_header_but_stored_text_does_not(document, embedded):
    db = FakeDb(document)
    await ingest_document(db, document.id, build_pdf(), USER_ID)

    embedded_texts = [t for call in embedded for t in call["texts"]]
    assert all(t.startswith("CP IPS.pdf | Kelas 9 (Fase D) | ips") for t in embedded_texts)
    assert all(call["purpose"] == "document" for call in embedded)
    assert all(not chunk.chunk_content.startswith("CP IPS.pdf |") for chunk in db.added)


@async_test
async def test_ingest_replaces_earlier_chunks(document, embedded, mocker):
    delete = ingestion_service.curriculum_document_repo.delete_chunks
    await ingest_document(FakeDb(document), document.id, build_pdf(), USER_ID)
    delete.assert_awaited_once()


@async_test
async def test_ingest_stops_quietly_when_the_document_is_deleted_midway(document, embedded):
    db = FakeDb(document, gone_after=1)  # present at the start, gone at the first batch check

    result = await ingest_document(db, document.id, build_pdf(), USER_ID)

    assert result.aborted and result.chunk_count == 0
    db.rollback.assert_awaited_once()
    db.commit.assert_not_awaited()


@async_test
async def test_a_pdf_without_any_text_is_rejected_with_a_clear_message(document, embedded):
    with pytest.raises(IngestError, match="hasil pindai"):
        await ingest_document(FakeDb(document), document.id, blank_pdf(), USER_ID)


@async_test
async def test_a_corrupt_file_is_rejected_with_a_clear_message(document, embedded):
    with pytest.raises(IngestError, match="rusak"):
        await ingest_document(FakeDb(document), document.id, b"not a pdf", USER_ID)


@async_test
async def test_a_missing_document_is_rejected(embedded):
    db = MagicMock()
    db.get = AsyncMock(return_value=None)
    with pytest.raises(IngestError, match="tidak ditemukan"):
        await ingest_document(db, uuid.uuid4(), build_pdf(), USER_ID)
