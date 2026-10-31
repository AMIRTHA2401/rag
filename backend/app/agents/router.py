import json
import re
from typing import Any


class QueryRouter:
    def __init__(self, llm: Any | None = None) -> None:
        self.llm = llm

    def classify(self, question: str, has_documents: bool = False) -> str:
        if re.search(r"\b(calculate|compute|what is \d|[\d]+\s*[\+\-\*/])", question, re.I):
            return "CALCULATION"
        if self._is_small_talk(question):
            return "GENERAL_QUESTION"
        if has_documents:
            return "DOCUMENT_SEARCH"
        heuristic = self._heuristic_classify(question)
        if self.llm is None or heuristic == "GENERAL_QUESTION":
            return heuristic
        result = self.llm.invoke(f"Classify as DOCUMENT_SEARCH, GENERAL_QUESTION, or CALCULATION. Return JSON only. Question: {question}")
        raw = (result.content if hasattr(result, "content") else str(result)).strip()
        try:
            value = json.loads(raw)
            label = value.get("classification") or value.get("category") or value.get("type")
            if label:
                return self._normalize(label)
        except (ValueError, TypeError):
            pass
        label_match = re.search(r"\b(DOCUMENT_SEARCH|GENERAL_QUESTION|CALCULATION)\b", raw, re.I)
        if label_match:
            return self._normalize(label_match.group(1))
        return self._heuristic_classify(question)

    @staticmethod
    def _normalize(label: str) -> str:
        normalized = str(label).strip().upper().replace(" ", "_")
        if normalized in {"DOCUMENT_SEARCH", "GENERAL_QUESTION", "CALCULATION"}:
            return normalized
        raise ValueError(f"Unsupported query classification: {label}")

    @staticmethod
    def _heuristic_classify(question: str) -> str:
        if re.search(r"\b(document|file|uploaded|according to|page|report|resume|candidate)\b", question, re.I):
            return "DOCUMENT_SEARCH"
        return "GENERAL_QUESTION"

    @staticmethod
    def _is_small_talk(question: str) -> bool:
        normalized = re.sub(r"[^a-z\s']", " ", question.lower())
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return bool(re.fullmatch(
            r"(hi|hello|hey|hi how are you|hello how are you|hey how are you|"
            r"good morning|good afternoon|good evening|how are you|"
            r"how are you doing|thanks|thank you|thank you so much|"
            r"you're welcome|bye|goodbye|who are you|what can you do)[!. ]*",
            normalized,
        ))
