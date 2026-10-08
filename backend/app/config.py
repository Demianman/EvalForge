from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./evalforge.db"
    session_secret: str = "dev-only-change-me"
    cors_origins: str = "http://localhost:3000"
    job_mode: str = "sync"
    redis_url: str = "redis://localhost:6379/0"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
