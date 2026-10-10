from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./data/certificates.db"
    generated_dir: Path = Path("data/generated")

    model_config = SettingsConfigDict(env_file=".env", env_prefix="", extra="ignore")


settings = Settings()
settings.generated_dir.mkdir(parents=True, exist_ok=True)
