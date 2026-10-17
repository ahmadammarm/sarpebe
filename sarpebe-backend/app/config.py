from typing import Literal
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str
    # Supabase is still used for Storage only; authentication is handled by this backend.
    supabase_url: str
    supabase_service_role_key: str
    gemini_api_key: str
    gemini_embedding_model: str = "gemini-embedding-2"
    gemini_generation_model: str = "gemini-3.8-flash"
    gemini_rerank_model: str = "gemini-2.5-flash-lite"
    # Only used by the offline evaluations (python -m evals.run generation --judge).
    gemini_judge_model: str = "gemini-3.8-flash"
    redis_url: str
    cors_origins: list[str] = ["http://localhost:3000"]
    max_upload_mb: int = 20

    # Retrieval (RAG). The similarity floor is calibrated with `python -m evals.run retrieval`.
    rag_candidate_k: int = 20
    rag_top_k: int = 6
    rag_rerank_shortlist: int = 12  # candidates sent to the reranker
    rag_min_similarity: float = 0.45
    rag_context_max_chars: int = 14000
    rag_use_rerank: bool = True
    # Send RETRIEVAL_DOCUMENT / RETRIEVAL_QUERY task types. gemini-embedding-2 may ignore them,
    # so this stays off until `python -m evals.run retrieval` shows a gain.
    embedding_use_task_types: bool = False
    # Pin HNSW's iterative scan (pgvector >= 0.8) so filtered searches still return enough rows.
    rag_hnsw_iterative_scan: bool = True

    # Generation. None for temperature = use the model default.
    generation_temperature: float | None = None
    generation_thinking_level: Literal["MINIMAL", "LOW", "MEDIUM", "HIGH"] | None = "MEDIUM"
    generation_max_output_tokens: int = 16000
    prompt_version: str = "lesson_plan.v2"
    # Attempts per model call for transient errors (429, 5xx, timeouts) only.
    llm_max_attempts: int = 3

    # Authentication
    auth_jwt_secret: str = Field(min_length=32)
    auth_jwt_issuer: str = "sarpebe"
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 14
    # A just-rotated refresh token presented again within this window is treated as a
    # concurrent refresh (e.g. two tabs), not as theft.
    refresh_reuse_grace_seconds: int = 30
    verification_token_ttl_hours: int = 24
    reset_token_ttl_minutes: int = 60
    require_email_verification: bool = True
    login_max_failed_attempts: int = 5
    login_lockout_minutes: int = 15

    # Email
    frontend_url: str = "http://localhost:3000"
    email_backend: Literal["console", "smtp"] = "console"
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from: str = "SARPEBE <no-reply@sarpebe.local>"
    smtp_use_starttls: bool = True

    # Unknown variables in .env (e.g. a leftover SUPABASE_JWT_SECRET) are ignored.
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
