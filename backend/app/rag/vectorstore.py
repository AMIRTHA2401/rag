from pathlib import Path
from typing import Any

import chromadb
from langchain_chroma import Chroma

from ..config import Settings
from .embeddings import create_embeddings


class VectorStore:
    def __init__(self, settings: Settings, embeddings: Any | None = None) -> None:
        settings.ensure_directories()
        self.settings = settings
        self.client = chromadb.PersistentClient(path=str(Path(settings.chroma_persist_directory)))
        self.embeddings = embeddings or create_embeddings(settings)
        self.store = Chroma(
            client=self.client,
            collection_name="documents",
            embedding_function=self.embeddings,
        )

    def add_documents(self, documents: list[Any], ids: list[str]) -> None:
        if documents:
            self.store.add_documents(documents, ids=ids)

    def search(self, query: str, k: int | None = None) -> list[Any]:
        return self.store.similarity_search(query, k=k or self.settings.top_k)

    def has_documents(self) -> bool:
        return self.store._collection.count() > 0

    def list_documents(self) -> list[dict[str, Any]]:
        records = self.store._collection.get(include=["metadatas"])
        documents: dict[str, dict[str, Any]] = {}
        for metadata in records.get("metadatas") or []:
            if not metadata:
                continue
            document_id = str(metadata.get("document_id", ""))
            if document_id and document_id not in documents:
                source_path = Path(str(metadata.get("source_path", "")))
                documents[document_id] = {
                    "id": document_id,
                    "name": str(metadata.get("document_name", source_path.name)),
                    "size": source_path.stat().st_size if source_path.exists() else 0,
                    "chunks": 0,
                }
            if document_id:
                documents[document_id]["chunks"] += 1
        return list(documents.values())

    def delete_document(self, document_id: str) -> None:
        self.store._collection.delete(where={"document_id": document_id})
