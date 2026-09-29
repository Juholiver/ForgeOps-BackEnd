from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), env_file_encoding="utf-8")

    APP_ENV: str = "development"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    APP_SECRET_KEY: str = "change-me-in-production"

    DB_BACKEND: str = "postgres"  # "postgres" | "sqlite"
    SQLITE_PATH: str = "forgeops_dev.db"

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "forgeops"
    POSTGRES_USER: str = "forgeops"
    POSTGRES_PASSWORD: str = "forgeops"

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "forgeops"
    RABBITMQ_PASSWORD: str = "forgeops"
    RABBITMQ_VHOST: str = "/"

    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    LOG_LEVEL: str = "INFO"

    @property
    def uses_sqlite(self) -> bool:
        return self.DB_BACKEND.lower() == "sqlite"

    @model_validator(mode="after")
    def check_production_secrets(self) -> "Settings":
        if self.APP_ENV != "production":
            return self
        if self.APP_SECRET_KEY == "change-me-in-production":
            raise ValueError(
                "APP_SECRET_KEY must be set to a strong random value when APP_ENV=production"
            )
        if not self.uses_sqlite and self.POSTGRES_PASSWORD == "forgeops":
            raise ValueError("POSTGRES_PASSWORD must be changed when APP_ENV=production")
        if self.RABBITMQ_PASSWORD == "forgeops":
            raise ValueError("RABBITMQ_PASSWORD must be changed when APP_ENV=production")
        return self

    @property
    def database_url(self) -> str:
        if self.uses_sqlite:
            return f"sqlite+aiosqlite:///{self.SQLITE_PATH}"
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def sync_database_url(self) -> str:
        if self.uses_sqlite:
            return f"sqlite:///{self.SQLITE_PATH}"
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def rabbitmq_url(self) -> str:
        return (
            f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}"
            f"@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}{self.RABBITMQ_VHOST}"
        )


settings = Settings()
