from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    tavily_api_key: str = ""
    database_url: str = "sqlite:///./phoenix_research.db"
    frontend_url: str = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[1] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def validate_api_keys(self) -> None:
        missing = [name for name, value in (("GROQ_API_KEY", self.groq_api_key), ("TAVILY_API_KEY", self.tavily_api_key)) if not value]
        if missing:
            raise RuntimeError(f"Missing required configuration: {', '.join(missing)}")


@lru_cache
def get_settings() -> Settings:
    return Settings()
