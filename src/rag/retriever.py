"""RAG retriever for querying indexed documents and formatting citations."""

from typing import List, Dict, Optional
from langchain_community.vectorstores import FAISS
from .indexer import FAISSIndexer


class RAGRetriever:
    """Retrieves relevant document chunks from FAISS index."""

    def __init__(self, project_root: str = None):
        """Initialize retriever with FAISS index.

        Args:
            project_root: Path to project root
        """
        self.indexer = FAISSIndexer(project_root)
        self.vector_store: Optional[FAISS] = None

    def initialize(self, force_rebuild: bool = False) -> None:
        """Initialize the FAISS index.

        Args:
            force_rebuild: Force rebuild of index
        """
        self.vector_store = self.indexer.load_or_build_index(force_rebuild=force_rebuild)

    def retrieve(self, query: str, k: int = 3) -> List[Dict[str, str]]:
        """Retrieve relevant document chunks for a query.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            List of dicts with keys: text, source_name, source_path
        """
        if self.vector_store is None:
            raise RuntimeError("RAG retriever not initialized. Call initialize() first.")

        # Search similar documents
        results = self.vector_store.similarity_search(query, k=k)

        # Format results with source metadata
        formatted_results = []
        for doc in results:
            formatted_results.append({
                "text": doc.page_content,
                "source_name": doc.metadata.get("source_name", "Unknown Source"),
                "source_path": doc.metadata.get("source_path", ""),
            })

        return formatted_results

    def retrieve_with_scores(self, query: str, k: int = 3) -> List[Dict]:
        """Retrieve with relevance scores.

        Args:
            query: Search query
            k: Number of results

        Returns:
            List of dicts with text, source_name, source_path, score
        """
        if self.vector_store is None:
            raise RuntimeError("RAG retriever not initialized. Call initialize() first.")

        # Search with scores
        results = self.vector_store.similarity_search_with_score(query, k=k)

        formatted_results = []
        for doc, score in results:
            formatted_results.append({
                "text": doc.page_content,
                "source_name": doc.metadata.get("source_name", "Unknown Source"),
                "source_path": doc.metadata.get("source_path", ""),
                "score": float(score),
            })

        return formatted_results

    @staticmethod
    def format_citations_markdown(chunks: List[Dict[str, str]]) -> str:
        """Format chunks as markdown with inline citation links.

        Each citation is formatted as: [Source Name](file:///path/to/file)
        The URL is invisible in display, only the source name shows.

        Args:
            chunks: List of retrieved chunks with source metadata

        Returns:
            Markdown-formatted citations
        """
        citations = []
        seen = set()  # Avoid duplicate citations

        for chunk in chunks:
            source_name = chunk.get("source_name", "Unknown Source")
            source_path = chunk.get("source_path", "")

            key = (source_name, source_path)
            if key not in seen and source_path:
                seen.add(key)
                # Convert Windows path to file:// URL if needed
                file_url = source_path.replace("\\", "/")
                if not file_url.startswith("file:///"):
                    # Add file:// protocol
                    if file_url.startswith("/"):
                        file_url = f"file://{file_url}"
                    else:
                        file_url = f"file:///{file_url}"

                citations.append(f"- [{source_name}]({file_url})")

        return "\n".join(citations) if citations else "No sources found"

    @staticmethod
    def format_answer_with_citations(
        answer: str,
        chunks: List[Dict[str, str]]
    ) -> Dict[str, any]:
        """Format answer with inline citations.

        Args:
            answer: The generated answer/response
            chunks: Retrieved document chunks

        Returns:
            Dict with answer and citations
        """
        citations_markdown = RAGRetriever.format_citations_markdown(chunks)

        return {
            "answer": answer,
            "citations": citations_markdown,
            "source_count": len(set(
                (c.get("source_name"), c.get("source_path"))
                for c in chunks
            ))
        }

    def query(
        self,
        question: str,
        k: int = 3,
        include_scores: bool = False
    ) -> Dict:
        """Query the RAG system.

        Args:
            question: User's question
            k: Number of document chunks to retrieve
            include_scores: Include relevance scores in response

        Returns:
            Dict with query, retrieved_chunks, and sources
        """
        if self.vector_store is None:
            raise RuntimeError("RAG retriever not initialized. Call initialize() first.")

        # Retrieve relevant chunks
        if include_scores:
            chunks = self.retrieve_with_scores(question, k=k)
        else:
            chunks = self.retrieve(question, k=k)

        # Format citations
        citations = self.format_citations_markdown(chunks)

        return {
            "query": question,
            "retrieved_chunks": chunks,
            "citations": citations,
            "chunk_count": len(chunks)
        }
