from langchain_core.tools import tool

from ..rag.vectorstore import VectorStore


def make_document_summary_tool(vectorstore: VectorStore):
    @tool
    def document_summary_tool(document_name: str) -> str:
        """Retrieve chunks from a named uploaded document for summarization."""
        docs = vectorstore.search(document_name)
        matching = [d for d in docs if d.metadata.get("document_name") == document_name]
        return "\n\n".join(d.page_content for d in matching)
    return document_summary_tool

