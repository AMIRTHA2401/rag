from typing import Any

from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    id: str
    name: str
    size: int
    chunks: int


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: str | None = None


class SourceCitation(BaseModel):
    document_name: str
    page_number: int | None = None
    chunk_id: str
    source_path: str
    content: str


class ChatResponse(BaseModel):
    answer: str
    conversation_id: str
    classification: str
    sources: list[SourceCitation] = []
    stages: list[str] = []
    tool_activity: list[str] = []


class HistoryMessage(BaseModel):
    role: str
    content: str
    created_at: str


class HealthResponse(BaseModel):
    status: str
    ollama_configured: bool

