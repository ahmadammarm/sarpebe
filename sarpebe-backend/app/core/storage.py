from supabase import create_client, Client
from app.config import settings

BUCKET = "sarpebe-storage"

# Use the service role key to bypass RLS when uploading curriculum documents
# since the backend service is performing the upload.
supabase_client: Client = create_client(
    settings.supabase_url,
    settings.supabase_service_role_key
)


def curriculum_storage_path(document_id) -> str:
    return f"curriculum/{document_id}.pdf"


def upload_pdf(path: str, content: bytes) -> None:
    supabase_client.storage.from_(BUCKET).upload(
        path=path,
        file=content,
        file_options={"content-type": "application/pdf"},
    )


def download_pdf(path: str) -> bytes:
    return supabase_client.storage.from_(BUCKET).download(path)


def remove(path: str) -> None:
    supabase_client.storage.from_(BUCKET).remove([path])


def public_url(path: str) -> str:
    # Built manually: get_public_url() has returned an empty value in this project.
    return f"{settings.supabase_url}/storage/v1/object/public/{BUCKET}/{path}"
