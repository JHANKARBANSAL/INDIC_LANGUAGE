"""
Application configuration for IndicSQL.
Loads settings from environment variables and .env file.
"""

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global configuration settings for the IndicSQL multi-agent system."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # General App Settings
    environment: str = Field(default="development", description="Environment mode")
    log_level: str = Field(default="INFO", description="Logging level")
    app_host: str = Field(default="0.0.0.0", description="API host")
    app_port: int = Field(default=8000, description="API port")

    # LLM Settings
    ollama_host: str = Field(default="http://localhost:11434", description="Ollama API base URL")
    ollama_model: str = Field(default="qwen2.5:3b", description="Default Ollama model")
    sarvam_api_key: Optional[str] = Field(default=None, description="Sarvam AI API key")
    sarvam_model_endpoint: str = Field(
        default="https://api.sarvam.ai/v1", description="Sarvam API endpoint"
    )
    openai_api_base: str = Field(
        default="http://localhost:8000/v1", description="OpenAI compatible base URL"
    )
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI compatible API key")

    # Embeddings & Vector Store
    embedding_model_name: str = Field(
        default="intfloat/multilingual-e5-large", description="Cross-lingual embedding model"
    )
    qdrant_host: str = Field(default="localhost", description="Qdrant host")
    qdrant_port: int = Field(default=6333, description="Qdrant port")
    qdrant_collection: str = Field(
        default="ndap_schema_elements", description="Schema vector collection"
    )

    # DuckDB Sandbox Limits
    duckdb_database_path: str = Field(
        default=":memory:", description="Path to DuckDB database file or :memory:"
    )
    duckdb_memory_limit_mb: int = Field(
        default=512, description="Max memory budget in MB for DuckDB sandbox"
    )
    duckdb_timeout_seconds: float = Field(
        default=2.0, description="Execution timeout for DuckDB queries"
    )


settings = Settings()
