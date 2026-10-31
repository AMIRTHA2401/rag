from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .rag.ingestion import SUPPORTED_EXTENSIONS, ingest_file
from .rag.vectorstore import VectorStore
from .schemas.api import ChatRequest, ChatResponse, DocumentResponse, HealthResponse, HistoryMessage, SourceCitation
from .services.chat import ChatService

settings = get_settings()
vectorstore = VectorStore(settings)
chat_service = ChatService(settings, vectorstore)
documents: dict[str, DocumentResponse] = {
    item["id"]: DocumentResponse(**item) for item in vectorstore.list_documents()
}

app = FastAPI(title="Agentic RAG API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])


@app.get("/api/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", ollama_configured=bool(settings.ollama_base_url))


@app.post("/api/documents/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile = File(...)) -> DocumentResponse:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(status_code=415, detail="Only PDF, TXT, and DOCX files are supported")
    path = Path(settings.data_directory) / (file.filename or "upload")
    try:
        path.write_bytes(await file.read())
        result = ingest_file(path, settings, vectorstore)
        response = DocumentResponse(**result)
        documents[response.id] = response
        return response
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Document ingestion failed") from exc


@app.get("/api/documents", response_model=list[DocumentResponse])
def list_documents() -> list[DocumentResponse]:
    return list(documents.values())


@app.delete("/api/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: str) -> None:
    if document_id not in documents:
        raise HTTPException(status_code=404, detail="Document not found")
    vectorstore.delete_document(document_id)
    documents.pop(document_id)


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        result = chat_service.chat(request.message, request.conversation_id)
        sources = [SourceCitation(**source) for source in result.get("documents", [])]
        return ChatResponse(answer=result["answer"], conversation_id=result["conversation_id"], classification=result.get("classification", "GENERAL_QUESTION"), sources=sources, stages=result.get("stages", []), tool_activity=result.get("tool_activity", []))
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Chat service is unavailable") from exc


@app.get("/api/chat/history", response_model=list[HistoryMessage])
def chat_history(conversation_id: str) -> list[HistoryMessage]:
    return [HistoryMessage(**message) for message in chat_service.histories.get(conversation_id, [])]
