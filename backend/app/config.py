"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    OPENAI_API_KEY: str = ""
    DATABASE_URL: str = "sqlite:///./onboarding.db"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
