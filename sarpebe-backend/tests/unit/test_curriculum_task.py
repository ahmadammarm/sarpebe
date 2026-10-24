import uuid
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock

import pytest

from app.core.services.ingestion_service import IngestError, IngestResult
from app.db.models.curriculum_document import CurriculumDocument
from app.tasks import curriculum_tasks

async_test = pytest.mark.asyncio(loop_scope="session")

ADMIN_ID = uuid.uuid4()


class FakeSession:
    def __init__(self, document):
        self.document = document
        self.commit = AsyncMock()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def get(self, model, key):
        return self.document


@pytest.fixture
def document():
    return CurriculumDocument(
        id=uuid.uuid4(), title="CP IPS.pdf", document_type="CP", url_path="http://x/doc.pdf",
        grade_level="9", subject="ips", status="processing",
    )


@pytest.fixture
def worker(mocker, document):
    session = FakeSession(document)

    @asynccontextmanager
    async def fake_scope():
        yield lambda: session

    mocker.patch.object(curriculum_tasks, "task_session_scope", fake_scope)
    mocker.patch.object(curriculum_tasks.storage, "download_pdf", return_value=b"%PDF-")
    ingest = mocker.patch.object(
        curriculum_tasks, "ingest_document", new_callable=AsyncMock,
        return_value=IngestResult(chunk_count=4, warnings=[]),
    )
    return type("Worker", (), {"session": session, "ingest": ingest})


async def run(document):
    await curriculum_tasks._process_curriculum_document(str(document.id), str(ADMIN_ID))


@async_test
async def test_the_stored_pdf_is_ingested_on_behalf_of_the_admin(worker, document):
    await run(document)

    args = worker.ingest.await_args.args
    assert args[1:] == (document.id, b"%PDF-", ADMIN_ID)
    assert document.status == "processing"  # completion is set by ingest_document itself
    worker.session.commit.assert_not_awaited()


@async_test
async def test_a_document_that_cannot_be_indexed_is_marked_failed_with_the_reason(worker, document):
    worker.ingest.side_effect = IngestError("PDF tidak dapat dibaca. File mungkin rusak.")

    await run(document)

    assert document.status == "failed"
    assert document.ingest_warnings == ["PDF tidak dapat dibaca. File mungkin rusak."]
    worker.session.commit.assert_awaited_once()


@async_test
async def test_an_unexpected_error_marks_the_document_failed_without_leaking_its_text(worker, document):
    worker.ingest.side_effect = RuntimeError("connection reset by peer: postgres://secret")

    await run(document)

    assert document.status == "failed"
    assert document.ingest_warnings == ["Dokumen gagal diproses. Coba unggah ulang."]


@async_test
async def test_a_document_deleted_meanwhile_is_ignored(worker, document):
    worker.session.document = None

    await run(document)

    worker.ingest.assert_not_awaited()


@async_test
async def test_an_aborted_ingest_changes_nothing(worker, document):
    worker.ingest.return_value = IngestResult(chunk_count=0, warnings=[], aborted=True)

    await run(document)

    assert document.status == "processing"
    worker.session.commit.assert_not_awaited()
