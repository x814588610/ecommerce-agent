"""应用配置。"""

from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """从环境变量和 .env 文件加载的应用配置。"""

    app_name: str = "E-commerce Agent"
    app_env: str = "development"
    app_debug: bool = True

    database_url: str = "sqlite:///./data/ecommerce.db"

    qdrant_url: str = ""
    qdrant_path: str = "data/qdrant"
    qdrant_collection: str = "products"
    qdrant_policy_collection: str = "policies"

    llm_base_url: str = "https://api.deepseek.com"
    llm_model: str = "deepseek-chat"
    llm_api_key: SecretStr = SecretStr("")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """返回缓存的应用配置。"""

    return Settings()
