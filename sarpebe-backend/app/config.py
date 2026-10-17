from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str
    supabase_url: str
    supabase_service_role_key: str
    supabase_jwt_secret: str
    gemini_api_key: str
    gemini_embedding_model: str = "gemini-embedding-2"
    gemini_generation_model: str = "gemini-2.5-flash-lite"
    redis_url: str
    cors_origins: list[str] = ["http://localhost:3000"]
    max_upload_mb: int = 20

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
