import hashlib
import re
from pathlib import Path
from typing import Any

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from docx import Document as DocxDocument

from ..config import Settings
from .vectorstore import VectorStore

SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".docx"}


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def extract_pages(path: Path) -> list[tuple[str, int | None]]:
    if path.suffix.lower() == ".pdf":
        return [(clean_text(page.extract_text() or ""), number) for number, page in enumerate(PdfReader(str(path)).pages, 1)]
    if path.suffix.lower() == ".docx":
        text = clean_text("\n".join(paragraph.text for paragraph in DocxDocument(str(path)).paragraphs))
        return [(text, None)]
    return [(clean_text(path.read_text(encoding="utf-8", errors="replace")), None)]


def ingest_file(path: Path, settings: Settings, vectorstore: VectorStore) -> dict[str, Any]:
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {path.suffix}")
    document_id = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    pages = extract_pages(path)
    splitter = RecursiveCharacterTextSplitter(chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap)
    chunks: list[Document] = []
    ids: list[str] = []
    for page_text, page_number in pages:
        if not page_text:
            continue
        for index, chunk in enumerate(splitter.split_text(page_text)):
            chunk_id = f"{document_id}-{len(chunks)}"
            chunks.append(Document(page_content=chunk, metadata={
                "document_id": document_id, "document_name": path.name,
                "page_number": page_number, "chunk_id": chunk_id, "source_path": str(path),
            }))
            ids.append(chunk_id)
    if not chunks:
        raise ValueError("The document contains no extractable text")
    vectorstore.delete_document(document_id)
    vectorstore.add_documents(chunks, ids)
    return {"id": document_id, "name": path.name, "size": path.stat().st_size, "chunks": len(chunks)}

