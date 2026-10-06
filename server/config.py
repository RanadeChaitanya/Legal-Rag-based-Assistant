from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL_FAST: str = "gemini-3.5-flash-lite"
    GEMINI_MODEL_REASON: str = "gemini-3.8-flash"

    QDRANT_URL: str = ""
    QDRANT_API_KEY: str = ""
    QDRANT_COLLECTION: str = "legal_v1"

    CLOUDFLARE_ACCOUNT_ID: str = ""
    CLOUDFLARE_API_TOKEN: str = ""
    EMBED_MODEL: str = "@cf/baai/bge-m3"
    EMBED_DIM: int = 1024

    TOP_K_DENSE: int = 40
    TOP_K_SPARSE: int = 40
    FINAL_TOP_K: int = 8
    BM25_MODE: str = "client"  # "client" (FastEmbed) or "cloud" (Qdrant Cloud Inference)

    SESSION_DB_PATH: str = "./data/sessions.sqlite3"
    SESSION_TTL_HOURS: int = 24
    API_BASE_URL: str = "http://127.0.0.1:8000"

    def missing_credentials(self) -> List[str]:
        required = [
            "GEMINI_API_KEY",
            "QDRANT_URL",
            "QDRANT_API_KEY",
            "CLOUDFLARE_ACCOUNT_ID",
            "CLOUDFLARE_API_TOKEN",
        ]
        return [k for k in required if not getattr(self, k)]

    def require_credentials(self) -> None:
        """Call from server startup (not at import time, so tests can import settings offline)."""
        missing = self.missing_credentials()
        if missing:
            raise RuntimeError(f"Missing required settings: {', '.join(missing)}")


settings = Settings()
