from typing import Any, Literal, TypedDict


Classification = Literal["DOCUMENT_SEARCH", "GENERAL_QUESTION", "CALCULATION"]


class AgentState(TypedDict, total=False):
    question: str
    conversation_id: str
    history: list[dict[str, str]]
    classification: Classification
    rewritten_query: str
    documents: list[dict[str, Any]]
    relevance: dict[str, Any]
    answer: str
    answer_grade: dict[str, Any]
    retrieval_attempts: int
    generation_attempts: int
    stages: list[str]
    tool_activity: list[str]
    error: str

