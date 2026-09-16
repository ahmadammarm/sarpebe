from supabase import create_client, Client
from app.config import settings

# Use the service role key to bypass RLS when uploading curriculum documents
# since the backend service is performing the upload.
supabase_client: Client = create_client(
    settings.supabase_url,
    settings.supabase_service_role_key
)
