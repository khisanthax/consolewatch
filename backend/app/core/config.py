from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ConsoleWatch"
    environment: str = "development"
    api_host: str = "127.0.0.1"
    api_port: int = 8000
    database_url: str = "sqlite:///./consolewatch.db"
    background_watch_enabled: bool = True
    watch_manager_interval_seconds: float = 5.0
    retention_prune_interval_seconds: int = 300
    moonraker_reconnect_delay_seconds: int = 5

    model_config = SettingsConfigDict(
        env_prefix="CONSOLEWATCH_",
        env_file=".env",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
