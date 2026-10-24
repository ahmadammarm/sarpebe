import uuid
import pytest
from datetime import datetime, timezone
from httpx import AsyncClient
from unittest.mock import AsyncMock
from fpdf import FPDF
from app.api.deps import require_admin
from app.db.models.curriculum_document import CurriculumDocument

pytestmark = pytest.mark.asyncio(loop_scope="session")

@pytest.fixture
def override_admin_auth(mock_user):
    async def _mock_require_admin():
        mock_user.role = "admin"
        return mock_user
    from app.main import app
    app.dependency_overrides[require_admin] = _mock_require_admin
    yield
    app.dependency_overrides.pop(require_admin, None)

def create_valid_dummy_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0, 10, 'Dummy Curriculum Text for Testing RAG System.')
    return bytes(pdf.output())

FORM = {'grade_level': ' 10 ', 'subject': 'Biologi'}

async def test_upload_invalid_file_extension(async_client: AsyncClient, override_admin_auth):
    files = {'file': ('test.txt', b'%PDF-1.4 but named txt', 'text/plain')}
    response = await async_client.post("/api/curriculum/upload", data=FORM, files=files)
    assert response.status_code == 400
    assert "Only PDF files" in response.json()["detail"]

async def test_upload_rejects_non_pdf_content(async_client: AsyncClient, override_admin_auth):
    files = {'file': ('fake.pdf', b'this is not a pdf', 'application/pdf')}
    response = await async_client.post("/api/curriculum/upload", data=FORM, files=files)
    assert response.status_code == 400
    assert "not a valid PDF" in response.json()["detail"]

async def test_upload_rejects_oversized_file(async_client: AsyncClient, override_admin_auth, mocker):
    mocker.patch("app.core.services.curriculum_service.settings.max_upload_mb", 0)
    files = {'file': ('big.pdf', create_valid_dummy_pdf(), 'application/pdf')}
    response = await async_client.post("/api/curriculum/upload", data=FORM, files=files)
    assert response.status_code == 400
    assert "upload limit" in response.json()["detail"]

async def test_upload_requires_admin(async_client: AsyncClient, override_auth):
    files = {'file': ('dummy.pdf', create_valid_dummy_pdf(), 'application/pdf')}
    response = await async_client.post("/api/curriculum/upload", data=FORM, files=files)
    assert response.status_code == 403
    assert response.json()["code"] == "forbidden"

async def test_upload_valid_pdf_success(async_client: AsyncClient, override_admin_auth, mock_db, mocker):
    """A valid PDF is stored, committed, then handed to Celery - in that order."""
    order = []
    mocker.patch("app.core.services.curriculum_service.storage.upload_pdf")
    mock_db.commit.side_effect = lambda: order.append("commit")
    mock_delay = mocker.patch(
        "app.tasks.curriculum_tasks.process_curriculum_document_task.delay",
        side_effect=lambda *a, **k: order.append("delay"),
    )
    mocker.patch("app.core.services.curriculum_service.storage.public_url", return_value="http://fake-url/doc.pdf")

    async def fake_create(db, data):
        # The real repository flushes and refreshes, which fills the column defaults.
        return CurriculumDocument(**data, ingest_version=1, uploaded_at=datetime.now(timezone.utc))
    mocker.patch(
        "app.core.services.curriculum_service.curriculum_document_repo.create",
        new_callable=AsyncMock,
        side_effect=fake_create,
    )

    files = {'file': ('dummy_curriculum.pdf', create_valid_dummy_pdf(), 'application/pdf')}
    response = await async_client.post(
        "/api/curriculum/upload",
        data={**FORM, "document_type": "ATP"},
        files=files,
    )

    assert response.status_code == 202
    body = response.json()
    assert body["title"] == "dummy_curriculum.pdf"
    assert body["document_type"] == "ATP"
    assert body["grade_level"] == "10"
    assert body["subject"] == "biologi"
    assert body["status"] == "processing"

    assert order == ["commit", "delay"]
    mock_delay.assert_called_once()

async def test_upload_rejects_unknown_document_type(async_client: AsyncClient, override_admin_auth):
    files = {'file': ('dummy.pdf', create_valid_dummy_pdf(), 'application/pdf')}
    response = await async_client.post(
        "/api/curriculum/upload", data={**FORM, "document_type": "pdf"}, files=files
    )
    assert response.status_code == 422

async def test_delete_missing_document_is_404(async_client: AsyncClient, override_admin_auth, mocker):
    mocker.patch(
        "app.core.services.curriculum_service.curriculum_document_repo.get",
        new_callable=AsyncMock,
        return_value=None,
    )
    response = await async_client.delete(f"/api/curriculum/{uuid.uuid4()}")
    assert response.status_code == 404


# --- listing, editing, processing again ----------------------------------------------------------

REPO = "app.core.services.curriculum_service.curriculum_document_repo"
DELAY = "app.tasks.curriculum_tasks.process_curriculum_document_task.delay"


def make_document(**overrides):
    values = dict(
        id=uuid.uuid4(), title="CP IPS.pdf", document_type="CP", url_path="http://x/doc.pdf",
        grade_level="9", subject="ips", status="completed", ingest_version=2, ingest_warnings=None,
        uploaded_at=datetime.now(timezone.utc),
    )
    values.update(overrides)
    return CurriculumDocument(**values)


@pytest.fixture
def document(mocker):
    doc = make_document()

    async def fake_update(db, obj, changes):
        for field, value in changes.items():
            setattr(obj, field, value)
        return obj

    mocker.patch(f"{REPO}.get", new_callable=AsyncMock, return_value=doc)
    mocker.patch(f"{REPO}.update", new_callable=AsyncMock, side_effect=fake_update)
    return doc


async def test_the_list_is_paginated_and_shows_warnings(async_client: AsyncClient, override_admin_auth, mocker):
    scanned = make_document(ingest_warnings=["2 halaman dibaca dengan OCR; periksa hasilnya."])
    paginated = mocker.patch(f"{REPO}.list_paginated", new_callable=AsyncMock, return_value=([scanned], 41))

    response = await async_client.get("/api/curriculum", params={"skip": 20, "limit": 10})

    assert response.status_code == 200
    body = response.json()
    assert (body["total"], body["skip"], body["limit"]) == (41, 20, 10)
    assert body["items"][0]["ingest_warnings"] == ["2 halaman dibaca dengan OCR; periksa hasilnya."]
    assert paginated.await_args.args[1:] == (20, 10)


@pytest.mark.parametrize("params", [{"skip": -1}, {"limit": 0}, {"limit": 101}])
async def test_the_list_rejects_out_of_range_paging(async_client: AsyncClient, override_admin_auth, params):
    assert (await async_client.get("/api/curriculum", params=params)).status_code == 422


async def test_changing_the_title_or_type_does_not_process_the_document_again(
    async_client: AsyncClient, override_admin_auth, document, mock_db, mocker
):
    delay = mocker.patch(DELAY)

    response = await async_client.patch(
        f"/api/curriculum/{document.id}", json={"title": "  CP IPS Fase D.pdf ", "document_type": "ATP"}
    )

    assert response.status_code == 200
    assert (response.json()["title"], response.json()["document_type"]) == ("CP IPS Fase D.pdf", "ATP")
    assert response.json()["status"] == "completed"
    delay.assert_not_called()
    mock_db.commit.assert_awaited_once()


async def test_changing_the_grade_processes_the_document_again_after_the_commit(
    async_client: AsyncClient, override_admin_auth, document, mock_db, mocker
):
    order = []
    mock_db.commit.side_effect = lambda: order.append("commit")
    delay = mocker.patch(DELAY, side_effect=lambda *a, **k: order.append("delay"))

    response = await async_client.patch(f"/api/curriculum/{document.id}", json={"grade_level": " 10 ", "subject": "IPS"})

    assert response.status_code == 200
    assert response.json()["grade_level"] == "10" and response.json()["status"] == "processing"
    assert order == ["commit", "delay"]
    assert delay.call_args.args[0] == str(document.id)


async def test_sending_the_same_grade_and_subject_is_not_a_change(
    async_client: AsyncClient, override_admin_auth, document, mocker
):
    delay = mocker.patch(DELAY)

    response = await async_client.patch(f"/api/curriculum/{document.id}", json={"grade_level": "9", "subject": " IPS "})

    assert response.status_code == 200 and response.json()["status"] == "completed"
    delay.assert_not_called()


@pytest.mark.parametrize("body", [{}, {"title": "   "}, {"grade_level": ""}, {"document_type": "pdf"}])
async def test_an_empty_or_invalid_edit_is_rejected(async_client: AsyncClient, override_admin_auth, document, body):
    response = await async_client.patch(f"/api/curriculum/{document.id}", json=body)
    assert response.status_code == 422


async def test_a_document_being_processed_cannot_be_edited_or_reindexed(
    async_client: AsyncClient, override_admin_auth, document, mocker
):
    document.status = "processing"
    delay = mocker.patch(DELAY)

    edit = await async_client.patch(f"/api/curriculum/{document.id}", json={"title": "Baru"})
    again = await async_client.post(f"/api/curriculum/{document.id}/reindex")

    assert edit.status_code == again.status_code == 409
    assert edit.json()["code"] == again.json()["code"] == "invalid_state"
    delay.assert_not_called()


async def test_reindex_marks_the_document_processing_and_hands_it_to_the_worker_after_the_commit(
    async_client: AsyncClient, override_admin_auth, document, mock_db, mock_user, mocker
):
    document.status = "failed"
    order = []
    mock_db.commit.side_effect = lambda: order.append("commit")
    delay = mocker.patch(DELAY, side_effect=lambda *a, **k: order.append("delay"))

    response = await async_client.post(f"/api/curriculum/{document.id}/reindex")

    assert response.status_code == 202 and response.json()["status"] == "processing"
    assert order == ["commit", "delay"]
    delay.assert_called_once_with(str(document.id), str(mock_user.id))


async def test_editing_or_reindexing_a_missing_document_is_404(async_client: AsyncClient, override_admin_auth, mocker):
    mocker.patch(f"{REPO}.get", new_callable=AsyncMock, return_value=None)
    missing = uuid.uuid4()

    edit = await async_client.patch(f"/api/curriculum/{missing}", json={"title": "Baru"})
    again = await async_client.post(f"/api/curriculum/{missing}/reindex")

    assert edit.status_code == again.status_code == 404


async def test_editing_and_reindexing_need_an_admin(async_client: AsyncClient, override_auth):
    some_id = uuid.uuid4()

    edit = await async_client.patch(f"/api/curriculum/{some_id}", json={"title": "Baru"})
    again = await async_client.post(f"/api/curriculum/{some_id}/reindex")
    listing = await async_client.get("/api/curriculum")

    assert edit.status_code == again.status_code == listing.status_code == 403
