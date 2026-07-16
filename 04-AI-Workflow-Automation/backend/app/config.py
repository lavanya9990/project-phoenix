from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    database_url: str = "sqlite:///./phoenix_automation.db"
    n8n_webhook_url: str = ""
    n8n_webhook_secret: str = ""
    frontend_url: str = "http://localhost:3000"
    workflow_timeout_seconds: float = 30
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

@lru_cache
def get_settings() -> Settings: return Settings()
