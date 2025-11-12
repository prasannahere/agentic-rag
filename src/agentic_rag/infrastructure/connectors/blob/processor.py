import os
from pathlib import Path
import chromadb
from sentence_transformers import SentenceTransformer

from agentic_rag.domain.utils import PathConfig
from agentic_rag.infrastructure.persistence.indexer import ChromaStorer

class Processor:
    """Custom file processor that reads, chunks, and stores files in Chroma."""

    def __init__(self, db_path: str = None,
                 collection_name: str = "my_files",
                 chunk_size: int = 1000,
                 overlap: int = 200):
        # Use PathConfig default if not provided
        db_path = db_path or str(PathConfig.get_db_path())
        
        # Setup Chroma client and collection
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(collection_name)

        # Setup embedder
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

        # Setup ChromaStorer
        self.storer = ChromaStorer(
            collection=self.collection,
            embedder=self.embedder,
            chunk_size=chunk_size,
            overlap=overlap
        )

    def process_file(self, file_path: str):
        """Process a file and store it in Chroma."""
        if not os.path.exists(file_path):
            print(f"[Processor] File not found: {file_path}")
            return

        print(f"[Processor] Processing file: {file_path}")
        self.storer.store_file(file_path)

