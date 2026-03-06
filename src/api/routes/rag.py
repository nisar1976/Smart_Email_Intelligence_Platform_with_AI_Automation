"""RAG (Retrieval-Augmented Generation) endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()


class RAGQueryRequest(BaseModel):
    """RAG query request model."""
    query: str
    k: int = 3  # Number of results


class Citation(BaseModel):
    """Citation model."""
    source_name: str
    source_path: str
    excerpt: str


class RAGQueryResponse(BaseModel):
    """RAG query response model."""
    query: str
    retrieved_chunks: int
    citations: str
    details: List[dict]


@router.post("/query", response_model=RAGQueryResponse)
async def rag_query(request: RAGQueryRequest):
    """Query OHM documents using RAG.

    Args:
        request: RAG query request with search query and number of results

    Returns:
        Retrieved document chunks with citations
    """
    try:
        from src.rag.retriever import RAGRetriever

        # Initialize RAG retriever
        rag = RAGRetriever()
        rag.initialize()

        # Perform query
        results = rag.query(request.query, k=request.k)

        # Format response
        details = []
        for chunk in results.get("retrieved_chunks", []):
            details.append({
                "source_name": chunk.get("source_name", "Unknown"),
                "source_path": chunk.get("source_path", ""),
                "excerpt": chunk.get("text", "")[:300],  # First 300 chars
                "relevance_score": chunk.get("score", 0)
            })

        return RAGQueryResponse(
            query=request.query,
            retrieved_chunks=results.get("chunk_count", 0),
            citations=results.get("citations", ""),
            details=details
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG query failed: {str(e)}")


@router.get("/rebuild-index")
async def rebuild_rag_index():
    """Rebuild the FAISS index from scratch.

    Returns:
        Rebuild status
    """
    try:
        from src.rag.indexer import FAISSIndexer

        indexer = FAISSIndexer()
        indexer.build_index(force_rebuild=True)

        return {
            "message": "FAISS index rebuilt successfully",
            "status": "complete"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Index rebuild failed: {str(e)}")


@router.get("/index-status")
async def get_index_status():
    """Get status of RAG index.

    Returns:
        Index status and statistics
    """
    try:
        from pathlib import Path

        index_dir = Path("rag_index")
        index_file = index_dir / "index.faiss"

        if index_file.exists():
            return {
                "status": "ready",
                "indexed": True,
                "index_path": str(index_dir),
                "index_size_mb": round(index_file.stat().st_size / (1024 * 1024), 2)
            }
        else:
            return {
                "status": "not_indexed",
                "indexed": False,
                "message": "Index not found. Run POST /api/rag/rebuild-index to create it."
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get index status: {str(e)}")
