from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    # Application
    app_name: str = "OnePilot"
    app_version: str = "1.0.0"
    debug: bool = True
    environment: str = "development"

    # PostgreSQL
    metadata_db_host: str = "localhost"
    metadata_db_port: int = 5432
    metadata_db_name: str = "onepilot_metadata"
    metadata_db_user: str = "onepilot"
    metadata_db_password: str = "changeme_in_production"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    # Ollama
    ollama_host: str = "http://localhost:11434"
    ollama_model: str = "mistral"

    # Sécurité
    secret_key: str = "changeme"
    jwt_secret_key: str = "changeme"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # Logging
    log_level: str = "INFO"
    log_file: str = "data/logs/onepilot.log"
    log_max_bytes: int = 10485760
    log_backup_count: int = 5

    # Embeddings
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    vector_store_path: str = "data/vector_store"
    chroma_persist_directory: str = "data/vector_store/chroma"

    # Whisper STT
    whisper_model: str = "base"
    whisper_device: str = "cpu"
    whisper_language: str = "fr"

    # TTS
    tts_model: str = "tts_models/fr/css10/vits"
    tts_device: str = "cpu"

    # Performance
    cache_ttl: int = 3600
    query_timeout: int = 60
    max_concurrent_queries: int = 10
    max_upload_size: int = 52428800
    max_question_length: int = 500
    rate_limit_per_minute: int = 60

    # Features flags
    enable_voice: bool = True
    enable_dashboards: bool = True
    enable_rag: bool = True
    enable_learning: bool = True
    enable_analytics: bool = True

    # Dev uniquement
    reload: bool = True
    show_sql_queries: bool = False
    mock_llm: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.metadata_db_user}:{self.metadata_db_password}"
            f"@{self.metadata_db_host}:{self.metadata_db_port}/{self.metadata_db_name}"
        )


settings = Settings()