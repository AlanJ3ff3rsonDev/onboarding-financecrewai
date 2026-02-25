"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OPENAI_API_KEY: str = ""
    SEARCH_API_KEY: str = ""
    API_KEY: str = ""
    DATABASE_URL: str = "sqlite:///./onboarding.db"
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173,https://portal.financecrew.ai"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
