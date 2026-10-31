from typing import Any
import re

from ..agents.answer_grader import AnswerGrader
from ..agents.generator import AnswerGenerator
from ..agents.query_rewriter import QueryRewriter
from ..agents.relevance_grader import RelevanceGrader
from ..agents.router import QueryRouter
from ..graph.state import AgentState
from ..rag.vectorstore import VectorStore
from ..tools.calculator import calculator_tool


def _stage(state: AgentState, name: str) -> list[str]:
    return [*state.get("stages", []), name]


class WorkflowNodes:
    def __init__(self, vectorstore: VectorStore, llm: Any | None = None) -> None:
        self.vectorstore = vectorstore
        self.router = QueryRouter(llm)
        self.rewriter = QueryRewriter(llm)
        self.relevance = RelevanceGrader(llm)
        self.generator = AnswerGenerator(llm)
        self.answer_grader = AnswerGrader(llm)

    def analyze(self, state: AgentState) -> AgentState:
        return {
            **state,
            "classification": self.router.classify(
                state["question"], has_documents=self.vectorstore.has_documents()
            ),
            "stages": _stage(state, "Analyzing question"),
        }

    def rewrite(self, state: AgentState) -> AgentState:
        return {**state, "rewritten_query": self.rewriter.rewrite(state["question"], state.get("history")), "stages": _stage(state, "Rewriting query")}

    def retrieve(self, state: AgentState) -> AgentState:
        query = state.get("rewritten_query", state["question"])
        docs = self.vectorstore.search(query)
        serialized = [{"document_name": d.metadata.get("document_name", "unknown"), "page_number": d.metadata.get("page_number"), "chunk_id": d.metadata.get("chunk_id", ""), "source_path": d.metadata.get("source_path", ""), "content": d.page_content} for d in docs]
        return {**state, "documents": serialized, "retrieval_attempts": state.get("retrieval_attempts", 0) + 1, "stages": _stage(state, "Retrieving documents")}

    def grade_relevance(self, state: AgentState) -> AgentState:
        return {**state, "relevance": self.relevance.grade(state["question"], state.get("documents", [])), "stages": _stage(state, "Evaluating relevance")}

    def generate(self, state: AgentState) -> AgentState:
        answer = self.generator.generate(state["question"], state.get("documents", []), state.get("history"))
        return {**state, "answer": answer, "generation_attempts": state.get("generation_attempts", 0) + 1, "stages": _stage(state, "Generating answer")}

    def grade_answer(self, state: AgentState) -> AgentState:
        return {**state, "answer_grade": self.answer_grader.grade(state["question"], state.get("answer", ""), state.get("documents", [])), "stages": _stage(state, "Verifying answer")}

    def direct(self, state: AgentState) -> AgentState:
        if state["classification"] == "CALCULATION":
            try:
                expression_match = re.search(r"(?<!\w)(\d+(?:\.\d+)?(?:\s*[\+\-\*/%]\s*\d+(?:\.\d+)?)+)", state["question"])
                expression = expression_match.group(1) if expression_match else re.sub(r"^\s*(calculate|compute)\s+", "", state["question"], flags=re.I)
                answer = calculator_tool.invoke(expression)
            except (ValueError, SyntaxError, TypeError, ZeroDivisionError) as exc:
                return {**state, "answer": f"I could not safely calculate that: {exc}", "stages": _stage(state, "Returning safe fallback"), "answer_grade": {"supported": False}}
            return {**state, "answer": answer, "stages": _stage(state, "Generating answer"), "answer_grade": {"supported": True}}
        answer = self.generator.generate(state["question"], [], state.get("history"))
        return {**state, "answer": answer, "stages": _stage(state, "Generating answer"), "answer_grade": {"supported": True}}

    def fallback(self, state: AgentState) -> AgentState:
        return {**state, "answer": "I’m sorry, but the uploaded documents do not contain enough information to answer that reliably.", "stages": _stage(state, "Returning safe fallback")}
