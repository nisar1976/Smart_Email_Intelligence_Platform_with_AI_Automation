"""FAISS indexer for creating and managing vector search index."""

import os
import pickle
from pathlib import Path
from typing import Optional
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from .loader import DocumentLoader


class FAISSIndexer:
    """Creates and loads FAISS index for OHM documents."""

    def __init__(self, project_root: str = None, index_dir: str = "rag_index"):
        """Initialize indexer.

        Args:
            project_root: Path to project root
            index_dir: Directory to store FAISS index (relative to project_root)
        """
        if project_root is None:
            # Find project root
            current = Path(__file__).parent
            while current != current.parent:
                if (current / "CLAUDE.md").exists():
                    project_root = str(current)
                    break
                current = current.parent

        self.project_root = Path(project_root)
        self.index_dir = self.project_root / index_dir
        self.index_dir.mkdir(exist_ok=True)

    def build_index(self, documents: Optional[list] = None, force_rebuild: bool = False) -> FAISS:
        """Build or rebuild FAISS index from documents.

        Args:
            documents: List of LangChain Documents to index
            force_rebuild: Force rebuild even if index exists

        Returns:
            FAISS vector store instance
        """
        index_path = self.index_dir / "index.faiss"
        docstore_path = self.index_dir / "docstore.pkl"

        # If index exists and not forcing rebuild, load it
        if index_path.exists() and docstore_path.exists() and not force_rebuild:
            print("Loading existing FAISS index...")
            return self.load_index()

        # Load documents if not provided
        if documents is None:
            loader = DocumentLoader(str(self.project_root))
            documents = loader.load_all_documents()

        if not documents:
            raise ValueError("No documents to index")

        print(f"Building FAISS index from {len(documents)} document chunks...")

        # Create embeddings
        embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=os.environ.get("OPENAI_API_KEY")
        )

        # Create FAISS index
        vector_store = FAISS.from_documents(
            documents=documents,
            embedding=embeddings
        )

        # Save index
        vector_store.save_local(str(self.index_dir / "index"))
        print(f"FAISS index saved to {self.index_dir}")

        return vector_store

    def load_index(self) -> FAISS:
        """Load existing FAISS index.

        Returns:
            FAISS vector store instance
        """
        embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=os.environ.get("OPENAI_API_KEY")
        )

        vector_store = FAISS.load_local(
            str(self.index_dir / "index"),
            embeddings,
            allow_dangerous_deserialization=True
        )

        return vector_store

    def load_or_build_index(self, force_rebuild: bool = False) -> FAISS:
        """Load existing index or build new one if not found.

        Args:
            force_rebuild: Force rebuild even if index exists

        Returns:
            FAISS vector store instance
        """
        index_path = self.index_dir / "index.faiss"

        if index_path.exists() and not force_rebuild:
            try:
                print("Loading existing FAISS index...")
                return self.load_index()
            except Exception as e:
                print(f"Error loading index, rebuilding: {e}")
                return self.build_index(force_rebuild=True)

        return self.build_index(force_rebuild=True)
