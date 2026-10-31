import json
import re
from typing import Any

_STOPWORDS = {"what", "which", "where", "when", "does", "the", "is", "are", "in", "of", "a", "an", "uploaded", "document"}


class RelevanceGrader:
    def __init__(self, llm: Any | None = None) -> None:
        self.llm = llm

    def grade(self, question: str, documents: list[dict[str, Any]]) -> dict[str, Any]:
        if not documents:
            return {"relevant": False, "reason": "No documents were retrieved.", "confidence": 1.0}
        question_terms = {term for term in re.findall(r"[a-z0-9]+", question.lower()) if term not in _STOPWORDS and len(term) > 2}
        evidence = " ".join(str(item.get("content", "")) for item in documents).lower()
        if question_terms and any(term in evidence for term in question_terms):
            return {"relevant": True, "reason": "Retrieved evidence shares terms with the question.", "confidence": 0.8}
        if self.llm is None:
            return {"relevant": True, "reason": "Retrieved document evidence is available.", "confidence": 0.5}
        result = self.llm.invoke(f"Grade evidence relevance. Return JSON with relevant, reason, confidence.\nQuestion: {question}\nEvidence: {documents}")
        raw = result.content if hasattr(result, "content") else str(result)
        try:
            fenced = re.search(r"```(?:json)?\s*(.*?)\s*```", raw, re.S)
            parsed = json.loads(fenced.group(1) if fenced else raw)
            if isinstance(parsed, dict) and "relevant" in parsed:
                return {"relevant": bool(parsed["relevant"]), "reason": str(parsed.get("reason", "")), "confidence": float(parsed.get("confidence", 0.5))}
            evidence = parsed.get("evidence") if isinstance(parsed, dict) else None
            if isinstance(evidence, list) and evidence:
                relevant = [item for item in evidence if isinstance(item, dict) and item.get("relevant") is True]
                return {"relevant": bool(relevant), "reason": str(relevant[0].get("reason", "")) if relevant else "No relevant evidence was identified.", "confidence": max((float(item.get("confidence", 0.5)) for item in relevant), default=0.5)}
        except (ValueError, TypeError):
            pass
        if re.search(r"\b(not relevant|irrelevant|unrelated|no)\b", raw, re.I):
            return {"relevant": False, "reason": raw.strip(), "confidence": 0.5}
        return {"relevant": True, "reason": raw.strip() or "Retrieved evidence is available.", "confidence": 0.5}
