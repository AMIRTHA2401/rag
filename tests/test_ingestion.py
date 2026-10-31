from pathlib import Path

from backend.app.config import Settings
from backend.app.rag.ingestion import ingest_file


class FakeStore:
    def __init__(self):
        self.added = []
        self.deleted = []

    def delete_document(self, document_id):
        self.deleted.append(document_id)

    def add_documents(self, documents, ids):
        self.added.extend(zip(documents, ids))


def test_text_ingestion_preserves_metadata(tmp_path: Path):
    source = tmp_path / "guide.txt"
    source.write_text("A " * 1000, encoding="utf-8")
    store = FakeStore()
    result = ingest_file(source, Settings(chunk_size=80, chunk_overlap=10), store)
    assert result["name"] == "guide.txt"
    assert result["chunks"] > 1
    assert store.added[0][0].metadata["document_name"] == "guide.txt"


def test_unsupported_file_rejected(tmp_path: Path):
    source = tmp_path / "guide.csv"
    source.write_text("data", encoding="utf-8")
    try:
        ingest_file(source, Settings(), FakeStore())
    except ValueError as exc:
        assert "Unsupported" in str(exc)
    else:
        raise AssertionError("Expected unsupported file error")

