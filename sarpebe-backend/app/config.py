from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str
    supabase_jwt_secret: str
    gemini_api_key: str
    gemini_embedding_model: str = "gemini-embedding-2"
    gemini_generation_model: str = "gemini-2.5-flash-lite"
    redis_url: str
    free_tier_quota: int = 3

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
