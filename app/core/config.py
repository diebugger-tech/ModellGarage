"""Zentrale Konfiguration (aus .env / Defaults)."""
from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    database_url: str = f"sqlite+aiosqlite:///{BASE_DIR / 'data' / 'modellgarage.db'}"
    media_dir: Path = BASE_DIR / "media"

    # eBay (Phase 3, optional)
    ebay_client_id: str = ""
    ebay_client_secret: str = ""
    ebay_env: str = "sandbox"

    @property
    def sqlite_path(self) -> Path:
        # 'sqlite+aiosqlite:///<pfad>' -> Pfad extrahieren
        return Path(self.database_url.split(":///", 1)[-1])


settings = Settings()
