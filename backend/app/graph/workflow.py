from typing import Any

from langgraph.graph import END, START, StateGraph

from .nodes import WorkflowNodes
from .state import AgentState


def build_workflow(nodes: WorkflowNodes, max_retrieval_retries: int = 2, max_generation_retries: int = 2):
    graph = StateGraph(AgentState)
    graph.add_node("analyze", nodes.analyze)
    graph.add_node("rewrite", nodes.rewrite)
    graph.add_node("retrieve", nodes.retrieve)
    graph.add_node("relevance", nodes.grade_relevance)
    graph.add_node("generate", nodes.generate)
    graph.add_node("answer_grade", nodes.grade_answer)
    graph.add_node("direct", nodes.direct)
    graph.add_node("fallback", nodes.fallback)
    graph.add_edge(START, "analyze")
    graph.add_conditional_edges("analyze", lambda s: s["classification"], {"DOCUMENT_SEARCH": "rewrite", "GENERAL_QUESTION": "direct", "CALCULATION": "direct"})
    graph.add_edge("rewrite", "retrieve")
    graph.add_edge("retrieve", "relevance")
    graph.add_conditional_edges("relevance", lambda s: "generate" if s.get("relevance", {}).get("relevant") else ("rewrite" if s.get("retrieval_attempts", 0) < max_retrieval_retries else "fallback"))
    graph.add_edge("generate", "answer_grade")
    graph.add_conditional_edges("answer_grade", lambda s: "end" if s.get("answer_grade", {}).get("supported") or s.get("generation_attempts", 0) >= max_generation_retries else "generate", {"end": END, "generate": "generate"})
    graph.add_edge("direct", END)
    graph.add_edge("fallback", END)
    return graph.compile()

