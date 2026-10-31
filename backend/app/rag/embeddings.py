from langchain_ollama import OllamaEmbeddings

from ..config import Settings


def create_embeddings(settings: Settings) -> OllamaEmbeddings:
    return OllamaEmbeddings(model=settings.embedding_model, base_url=settings.ollama_base_url)

