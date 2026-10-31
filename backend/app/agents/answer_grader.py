import json
import re
from typing import Any


class AnswerGrader:
    def __init__(self, llm: Any | None = None) -> None:
        self.llm = llm

    def grade(self, question: str, answer: str, documents: list[dict[str, Any]]) -> dict[str, Any]:
        if not answer.strip():
            return {"supported": False, "reason": "Empty answer.", "confidence": 1.0}
        if documents and "[" in answer and "]" in answer:
            return {"supported": True, "reason": "The answer includes citations to retrieved evidence.", "confidence": 0.8}
        if self.llm is None:
            return {"supported": bool(documents), "reason": "Basic evidence check.", "confidence": 0.5}
        result = self.llm.invoke(f"Check if answer is supported by evidence and answers the question. Return JSON with supported, reason, confidence.\nQuestion: {question}\nAnswer: {answer}\nEvidence: {documents}")
        raw = result.content if hasattr(result, "content") else str(result)
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict) and "supported" in parsed:
                return {"supported": bool(parsed["supported"]), "reason": str(parsed.get("reason", "")), "confidence": float(parsed.get("confidence", 0.5))}
        except (ValueError, TypeError):
            pass
        if re.search(r"\b(not supported|unsupported|incorrect|no)\b", raw, re.I):
            return {"supported": False, "reason": raw.strip(), "confidence": 0.5}
        return {"supported": bool(documents), "reason": raw.strip() or "Evidence was retrieved.", "confidence": 0.5}
