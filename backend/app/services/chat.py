from datetime import datetime, timezone
from uuid import uuid4

from langchain_ollama import ChatOllama

from ..config import Settings
from ..graph.nodes import WorkflowNodes
from ..graph.workflow import build_workflow
from ..rag.vectorstore import VectorStore


class ChatService:
    def __init__(self, settings: Settings, vectorstore: VectorStore) -> None:
        self.vectorstore = vectorstore
        self.histories: dict[str, list[dict[str, str]]] = {}
        self.llm = ChatOllama(
            model=settings.llm_model,
            base_url=settings.ollama_base_url,
            temperature=0,
            num_predict=96,
            timeout=60,
        )
        self.workflow = build_workflow(WorkflowNodes(vectorstore, self.llm), settings.max_retrieval_retries, settings.max_generation_retries)

    def chat(self, message: str, conversation_id: str | None = None) -> dict:
        conversation_id = conversation_id or str(uuid4())
        history = self.histories.setdefault(conversation_id, [])
        result = self.workflow.invoke({"question": message, "conversation_id": conversation_id, "history": history, "stages": [], "retrieval_attempts": 0, "generation_attempts": 0})
        history.extend([{"role": "user", "content": message, "created_at": datetime.now(timezone.utc).isoformat()}, {"role": "assistant", "content": result["answer"], "created_at": datetime.now(timezone.utc).isoformat()}])
        return {**result, "conversation_id": conversation_id}
