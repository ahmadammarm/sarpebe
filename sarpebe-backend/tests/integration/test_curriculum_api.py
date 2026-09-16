import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch, MagicMock
import io
from fpdf import FPDF
from app.api.deps import require_admin

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
    pdf_bytes = bytes(pdf.output())
    return pdf_bytes

async def test_upload_invalid_file_extension(async_client: AsyncClient, override_admin_auth, mock_user):
    """Test that uploading a non-pdf file is rejected."""
    files = {'file': ('test.txt', b'this is text', 'text/plain')}
    data = {'grade_level': '10', 'subject': 'Biologi'}

    response = await async_client.post("/api/curriculum/upload", data=data, files=files)
    assert response.status_code == 400
    assert "Only PDF files" in response.json()["detail"]

async def test_upload_valid_pdf_success(async_client: AsyncClient, override_admin_auth, mock_user, mocker):
    """Test uploading a valid PDF returns 202 and delegates processing to Celery."""
    # Mock supabase storage
    mock_supabase = mocker.patch("app.api.routers.curriculum.supabase_client")
    mock_supabase.storage.from_().get_public_url.return_value = "http://fake-url/doc.pdf"

    # Mock the celery task
    mock_celery_task = mocker.patch("app.api.routers.curriculum.process_curriculum_document_task.delay")

    pdf_bytes = create_valid_dummy_pdf()
    files = {'file': ('dummy_curriculum.pdf', pdf_bytes, 'application/pdf')}
    data = {'grade_level': '10', 'subject': 'Biologi'}

    response = await async_client.post("/api/curriculum/upload", data=data, files=files)

    assert response.status_code == 202
    res_data = response.json()
    assert res_data["title"] == "dummy_curriculum.pdf"
    assert res_data["document_type"] == "pdf"
    assert res_data["status"] == "processing"
    assert "id" in res_data

    # Ensure the celery task was dispatched
    mock_celery_task.assert_called_once()

