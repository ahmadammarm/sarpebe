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
        return CurriculumDocument(**data, uploaded_at=datetime.now(timezone.utc))
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
