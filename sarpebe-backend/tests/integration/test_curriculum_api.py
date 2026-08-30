import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock
import io
from fpdf import FPDF

pytestmark = pytest.mark.asyncio(loop_scope="session")

def create_valid_dummy_pdf():
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('helvetica', 'B', 12)
    pdf.cell(0, 10, 'Dummy Curriculum Text for Testing RAG System.')
    pdf_bytes = bytes(pdf.output())
    return pdf_bytes

async def test_upload_invalid_file_extension(async_client: AsyncClient, override_auth, mock_user):
    """Test that uploading a non-pdf file is rejected."""
    files = {'file': ('test.txt', b'this is text', 'text/plain')}
    data = {'grade_level': '10', 'subject': 'Biologi'}
    
    response = await async_client.post("/api/curriculum/upload", data=data, files=files)
    assert response.status_code == 400
    assert "Only PDF files" in response.json()["detail"]

async def test_upload_corrupted_pdf(async_client: AsyncClient, override_auth, mock_user):
    """Test that an unparseable/corrupted PDF is handled gracefully."""
    files = {'file': ('test.pdf', b'Not a real PDF file bytes', 'application/pdf')}
    data = {'grade_level': '10', 'subject': 'Biologi'}
    
    response = await async_client.post("/api/curriculum/upload", data=data, files=files)
    assert response.status_code == 400
    assert "Failed to parse PDF" in response.json()["detail"] or "extract any text" in response.json()["detail"]

async def test_upload_valid_pdf_success(async_client: AsyncClient, override_auth, mock_user, mocker):
    """Test uploading a valid PDF parses, chunks, and mocks the embedding call."""
    # Mock the external Gemini embedding call
    mock_embed = mocker.patch(
        "app.api.routers.curriculum.embedding_service.embed_text",
        new_callable=AsyncMock
    )
    # Return a fake 768-dimension vector
    mock_embed.return_value = [0.1] * 768

    pdf_bytes = create_valid_dummy_pdf()
    files = {'file': ('dummy_curriculum.pdf', pdf_bytes, 'application/pdf')}
    data = {'grade_level': '10', 'subject': 'Biologi'}
    
    response = await async_client.post("/api/curriculum/upload", data=data, files=files)
    
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["title"] == "dummy_curriculum.pdf"
    assert res_data["document_type"] == "pdf"
    assert "id" in res_data
    
    # Ensure the embedding service was called (meaning text was extracted and chunked)
    mock_embed.assert_called()
