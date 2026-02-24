from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    # Authentication
    better_auth_secret: str = "NX83Ogb4FAGFppGPnkjbDP1iykJ6NPSH"

    # LLM Provider: "groq" (free) or "openai" (paid). Auto-detects from available keys if not set.
    llm_provider: str = ""

    # OpenAI
    openai_api_key: str = ""

    # Groq (free tier — https://console.groq.com)
    groq_api_key: str = ""
    groq_model: str = "meta-llama/llama-4-scout-17b-16e-instruct"

    # Database
    database_url: str = "sqlite:///./todo.db"  # Default for development
    neon_db_url: Optional[str] = None

    # API
    api_prefix: str = "/api"

    # CORS
    frontend_origin: str = "http://localhost:3000"
    cors_origins: str = ""  # Additional CORS origins (comma-separated)

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )


settings = Settings()
