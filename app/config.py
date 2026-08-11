from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables or .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    feishu_app_id: str = Field(validation_alias="FEISHU_APP_ID")
    feishu_app_secret: str = Field(validation_alias="FEISHU_APP_SECRET")
    feishu_verification_token: str = Field(
        default="", validation_alias="FEISHU_VERIFICATION_TOKEN"
    )
    feishu_encrypt_key: str = Field(default="", validation_alias="FEISHU_ENCRYPT_KEY")

    agent_model: str = Field(
        default="openai-chat:claude-sonnet-4.6", validation_alias="AGENT_MODEL"
    )
    openai_base_url: str = Field(
        default="https://agent-api.shuiditech.com/api/v1",
        validation_alias="OPENAI_BASE_URL",
    )
    openai_api_key: SecretStr | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    water_pipe_title: str = Field(
        default="feishu-shopify-agent", validation_alias="WATER_PIPE_TITLE"
    )
    database_path: Path = Field(default=Path("data/agent.db"), validation_alias="DATABASE_PATH")
    memory_message_limit: int = Field(default=12, validation_alias="MEMORY_MESSAGE_LIMIT")
    agent_max_workers: int = Field(default=4, validation_alias="AGENT_MAX_WORKERS")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    @field_validator("feishu_app_id", "feishu_app_secret")
    @classmethod
    def credentials_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value.strip()

    @field_validator("memory_message_limit", "agent_max_workers")
    @classmethod
    def positive_integer(cls, value: int) -> int:
        if value < 1:
            raise ValueError("must be greater than zero")
        return value

    @field_validator("agent_model", "openai_base_url", "water_pipe_title")
    @classmethod
    def non_empty_agent_setting(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value.strip()


@lru_cache
def get_settings() -> Settings:
    return Settings()
