from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(BaseSettings):
    """Base configuration class for the application."""

    ENV_STATE: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore", 
    )

class GlobalConfig(BaseConfig):
    DATABASE_URL: str | None = None
    DB_FORCE_ROLL_BACK: bool = False
    LOGTAIL_API_KEY: str | None = None
    SECRET_KEY: str | None = None
    ALGORITHM: str | None = None


class DevConfig(GlobalConfig):
    class Config:
        env_prefix = "DEV_"


class ProdConfig(GlobalConfig):
    class Config:
        env_prefix = "PROD_"


class TestConfig(GlobalConfig):
    DATABASE_URL: str = "sqlite:///:memory:"
    DB_FORCE_ROLL_BACK: bool = True

    class Config:
        env_prefix = "TEST_"


@lru_cache
def get_config(env_state: str):
    configs = {"dev": DevConfig, "prod": ProdConfig, "test": TestConfig}
    return configs[env_state]()


config = get_config(BaseConfig().ENV_STATE)
