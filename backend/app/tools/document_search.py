from langchain_core.tools import tool

from ..rag.vectorstore import VectorStore


def make_document_search_tool(vectorstore: VectorStore):
    @tool
    def document_search_tool(query: str) -> str:
        """Search uploaded documents and return evidence with metadata."""
        docs = vectorstore.search(query)
        return "\n\n".join(f"[{d.metadata.get('document_name')} p.{d.metadata.get('page_number')}] {d.page_content}" for d in docs)
    return document_search_tool

