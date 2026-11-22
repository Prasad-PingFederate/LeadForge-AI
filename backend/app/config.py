from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database & Storage
    database_url: str = "sqlite+aiosqlite:///./leadforge.db"
    redis_url: str = "redis://localhost:6379/0"

    # LLM Settings (provider-agnostic)
    llm_provider: str = "openai"  # "openai" | "anthropic" | "gemini" | "mock"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"

    # Search & Intent Connectors
    serper_api_key: str = ""
    tavily_api_key: str = ""
    brave_api_key: str = ""

    # Enrichment Providers (optional)
    hunter_api_key: str = ""
    apollo_api_key: str = ""
    million_verifier_api_key: str = ""

    # Deliverability & Mailer
    smtp_host: str = "smtp.resend.com"
    smtp_port: int = 587
    smtp_user: str = "resend"
    smtp_password: str = ""
    default_from_email: str = "outreach@leadforge.ai"
    unsubscribe_base_url: str = "http://localhost:8000/api/unsubscribe"
    daily_send_cap: int = 50
    min_interval_seconds: int = 45
    max_interval_seconds: int = 180

    # Server & Security
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
