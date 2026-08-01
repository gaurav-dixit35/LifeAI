import json
from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "LifeAI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    SECRET_KEY: str = "change-this-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    REMEMBER_ME_EXPIRE_MINUTES: int = 60 * 24 * 30
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30
    DATABASE_URL: str = "sqlite+aiosqlite:///./lifeai.db"
    FRONTEND_APP_URL: str = "http://localhost:3000"

    ADMIN_EMAIL: str = "gd36990@gmail.com"
    ADMIN_PASSWORD: str = "gd1234"
    GOOGLE_CLIENT_ID: str = ""

    ENABLE_EXTERNAL_LLM: bool = True
    LIFE_AI_PROVIDER_ORDER: list[str] = ["gemini", "openrouter", "groq"]

    GEMINI_API_KEY: str = ""
    GEMINI_MODEL_NAME: str = "gemini-2.0-flash"

    OPENROUTER_API_KEY: str = ""
    OPENROUTER_MODEL_NAME: str = "meta-llama/llama-3.1-8b-instruct"
    OPENROUTER_SITE_URL: str = "http://localhost:3000"
    OPENROUTER_APP_NAME: str = "LifeAI"

    GROQ_API_KEY: str = ""
    GROQ_MODEL_NAME: str = "llama-3.1-8b-instant"

    HUGGINGFACE_API_KEY: str = ""
    HF_MODEL_NAME: str = "mistralai/Mistral-7B-Instruct-v0.2"
    HF_MAX_TOKENS: int = 1100
    HF_TEMPERATURE: float = 0.25

    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    OLLAMA_MODEL_NAME: str = "llama3.2:3b"

    CODE_AI_DEFAULT_TRAINING_PATH: str = "../other/training.txt"
    CODE_AI_MAX_CONTEXT_CHARS: int = 18000

    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, value: object) -> bool:
        if isinstance(value, bool):
            return value
        if value is None:
            return True
        normalized = str(value).strip().lower()
        if normalized in {"1", "true", "yes", "on", "debug", "development", "dev"}:
            return True
        if normalized in {"0", "false", "no", "off", "release", "production", "prod"}:
            return False
        return bool(value)

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if not value:
            return value
        prefix = "sqlite+aiosqlite:///"
        if not value.startswith(prefix):
            return value
        path_part = value[len(prefix):]
        if path_part in {":memory:", ""}:
            return value
        candidate = Path(path_part)
        if candidate.is_absolute():
            return value
        base_dir = Path(__file__).resolve().parent
        resolved = (base_dir / candidate).resolve().as_posix()
        return f"{prefix}{resolved}"

    @field_validator("CORS_ORIGINS", "LIFE_AI_PROVIDER_ORDER", mode="before")
    @classmethod
    def parse_string_list(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, list):
            return value
        if not value:
            return []
        value = value.strip()
        if value.startswith("["):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                parsed = None
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        return [item.strip() for item in value.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
