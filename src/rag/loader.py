"""Document loader for OHM brand and specification documents."""

import os
from pathlib import Path
from typing import List, Dict, Tuple
from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
)
import yaml


class DocumentLoader:
    """Loads OHM documents from various formats (PDF, TXT, YAML, MD)."""

    # Mapping of display names to (file_path, file_type)
    SOURCES = {
        "OHM Brand Voice Guide": ("OHM BRAND VOICE AI TRAINING GUIDE.pdf", "pdf"),
        "Signature Service Knowledge Base": ("OHM Signature Service Knowledge Base.pdf", "pdf"),
        "Full Brand Knowledge Framework": ("OHM — Full Brand Knowledge & Messaging Framework.txt", "txt"),
        "Email Sequences Specification": ("SPECIFICATION.md", "md"),
        "Project Requirements": ("requirement.txt", "txt"),
        "Prompt Guardrails": ("src/prompts/guardrails.yaml", "yaml"),
        "Email Sequence Templates": ("src/prompts/email_sequences.yaml", "yaml"),
    }

    def __init__(self, project_root: str = None):
        """Initialize loader with project root path."""
        if project_root is None:
            # Find project root (where CLAUDE.md exists)
            current = Path(__file__).parent
            while current != current.parent:
                if (current / "CLAUDE.md").exists():
                    project_root = str(current)
                    break
                current = current.parent
            if project_root is None:
                raise ValueError("Could not find project root with CLAUDE.md")

        self.project_root = Path(project_root)

    def load_all_documents(self) -> List[Document]:
        """Load all OHM documents and return as LangChain Document objects."""
        documents = []

        for display_name, (relative_path, file_type) in self.SOURCES.items():
            file_path = self.project_root / relative_path

            # Skip if file doesn't exist
            if not file_path.exists():
                print(f"Warning: Document not found: {file_path}")
                continue

            try:
                if file_type == "pdf":
                    docs = self._load_pdf(str(file_path), display_name)
                elif file_type == "txt":
                    docs = self._load_text(str(file_path), display_name)
                elif file_type == "md":
                    docs = self._load_text(str(file_path), display_name)
                elif file_type == "yaml":
                    docs = self._load_yaml(str(file_path), display_name)
                else:
                    print(f"Unsupported file type: {file_type}")
                    continue

                documents.extend(docs)
                print(f"Loaded {len(docs)} chunks from {display_name}")

            except Exception as e:
                print(f"Error loading {display_name}: {e}")
                continue

        return documents

    def _load_pdf(self, file_path: str, source_name: str) -> List[Document]:
        """Load PDF file using PyPDFLoader."""
        loader = PyPDFLoader(file_path)
        pages = loader.load()

        # Add metadata to each page
        for page in pages:
            page.metadata["source_name"] = source_name
            page.metadata["source_path"] = file_path
            page.metadata["file_type"] = "pdf"

        return pages

    def _load_text(self, file_path: str, source_name: str) -> List[Document]:
        """Load TXT/MD file and split into chunks."""
        loader = TextLoader(file_path)
        docs = loader.load()

        # Add metadata
        for doc in docs:
            doc.metadata["source_name"] = source_name
            doc.metadata["source_path"] = file_path
            doc.metadata["file_type"] = "text"

        # Split large documents into chunks
        return self._chunk_documents(docs, source_name, file_path)

    def _load_yaml(self, file_path: str, source_name: str) -> List[Document]:
        """Load YAML file and convert to text documents."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = yaml.safe_load(f)

        # Convert YAML to readable text
        text_content = yaml.dump(content, default_flow_style=False)

        doc = Document(
            page_content=text_content,
            metadata={
                "source_name": source_name,
                "source_path": file_path,
                "file_type": "yaml"
            }
        )

        # Chunk the document
        return self._chunk_documents([doc], source_name, file_path)

    def _chunk_documents(
        self,
        documents: List[Document],
        source_name: str,
        source_path: str,
        chunk_size: int = 500,
        overlap: int = 50
    ) -> List[Document]:
        """Split documents into overlapping chunks."""
        chunked = []

        for doc in documents:
            text = doc.page_content

            # Simple chunking strategy
            for i in range(0, len(text), chunk_size - overlap):
                chunk_text = text[i:i + chunk_size]
                if len(chunk_text.strip()) > 50:  # Only keep meaningful chunks
                    chunked.append(
                        Document(
                            page_content=chunk_text,
                            metadata={
                                "source_name": source_name,
                                "source_path": source_path,
                                "file_type": doc.metadata.get("file_type", "text"),
                                "chunk_start": i
                            }
                        )
                    )

        return chunked
