from typing import Any


class QueryRewriter:
    def __init__(self, llm: Any | None = None) -> None:
        self.llm = llm

    def rewrite(self, question: str, history: list[dict[str, str]] | None = None) -> str:
        if self.llm is None or (not history and len(question.split()) >= 5 and "?" in question):
            return question.strip()
        context = "\n".join(f"{m['role']}: {m['content']}" for m in (history or [])[-4:])
        result = self.llm.invoke(f"Rewrite this into a precise document search query, preserving intent. Return only the query.\n{context}\nQuestion: {question}")
        return (result.content if hasattr(result, "content") else str(result)).strip()
