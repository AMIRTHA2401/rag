from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ollama_base_url: str = "http://localhost:11434"
    llm_model: str = "llama3.2:3b"
    embedding_model: str = "nomic-embed-text"
    chroma_persist_directory: str = "./data/chroma_db"
    chunk_size: int = 800
    chunk_overlap: int = 150
    top_k: int = 5
    max_retrieval_retries: int = 2
    max_generation_retries: int = 2
    data_directory: str = "./data/documents"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    def ensure_directories(self) -> None:
        Path(self.chroma_persist_directory).mkdir(parents=True, exist_ok=True)
        Path(self.data_directory).mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    return settings

