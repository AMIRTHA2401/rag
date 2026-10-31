from typing import Any
import re


class AnswerGenerator:
    def __init__(self, llm: Any | None = None) -> None:
        self.llm = llm

    def generate(self, question: str, documents: list[dict[str, Any]], history: list[dict[str, str]] | None = None) -> str:
        if not documents:
            if self.llm is None:
                return "I could not find enough information in the uploaded documents to answer that."
            context = "\n".join(f"{m['role']}: {m['content']}" for m in (history or [])[-4:])
            result = self.llm.invoke(
                "Answer the user conversationally and concisely. Do not claim to have access "
                "to documents or evidence. If the request is unclear, ask a brief clarification.\n"
                f"Conversation:\n{context}\nUser: {question}"
            )
            return (result.content if hasattr(result, "content") else str(result)).strip()
        if re.search(r"\b(exam|exams|schedule|course|subject)\b", question, re.I):
            schedule_rows: list[str] = []
            for document in documents:
                matches = re.findall(
                    r"([A-Z0-9]{4,8})\s+([A-Z][A-Z ]+?)\s+(\d{2}-\d{2}-\d{4})\s+([\d:]+ [AP]M to [\d:]+ [AP]M)",
                    document["content"],
                )
                for code, title, date, time in matches:
                    row = f"- {code} — {title.strip()} — {date}, {time}"
                    if row not in schedule_rows:
                        schedule_rows.append(row)
            if schedule_rows:
                source = documents[0]
                return (
                    "The exam schedule in "
                    f"{source['document_name']} (page {source.get('page_number')}) is:\n"
                    + "\n".join(schedule_rows)
                    + f"\n\nSource: [{source['document_name']}, page {source.get('page_number')}]"
                )
        if self.llm is None:
            return "I could not find enough information in the uploaded documents to answer that."
        evidence = "\n\n".join(f"[{d['document_name']}, page {d.get('page_number')}] {d['content']}" for d in documents)
        prompt = (
            "Answer using only the evidence below. If evidence is insufficient, say so plainly. "
            "Cite sources as [document name, page N]. Never invent a citation.\n"
            f"Question: {question}\nEvidence:\n{evidence}"
        )
        result = self.llm.invoke(prompt)
        return (result.content if hasattr(result, "content") else str(result)).strip()
