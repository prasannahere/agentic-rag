import os
from typing import List

from langchain_community.document_loaders import (
    UnstructuredPDFLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredPowerPointLoader,
    TextLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter


class ChromaStorer:
    """Handles storing documents into Chroma with embeddings."""

    def __init__(self, collection, embedder, chunk_size: int = 1000, overlap: int = 200):
        self.collection = collection
        self.embedder = embedder
        self.chunker = LangChunker(chunk_size, overlap)

    def store_file(self, file_path: str):
        docs = FileReader.load(file_path)
        if not docs:
            print(f"[SKIP] No documents extracted from {file_path}")
            return

        chunks = self.chunker.chunk_docs(docs)
        if not chunks:
            print(f"[SKIP] No chunks created from {file_path}")
            return
        
        # Extract text content from Document objects
        chunk_texts = [chunk.page_content for chunk in chunks]
        embeddings = self.embedder.encode(chunk_texts, show_progress_bar=True).tolist()

        ids = [f"{os.path.basename(file_path)}_{i}" for i in range(len(chunks))]
        metas = [{"file": str(file_path), "chunk": i} for i in range(len(chunks))]

        self.collection.add(
            documents=chunk_texts,
            embeddings=embeddings,
            ids=ids,
            metadatas=metas
        )
        print(f"[INFO] Stored {len(chunks)} chunks from {file_path}")


class FileReader:
    """Uses LangChain community loaders to extract Documents from files."""

    @staticmethod
    def load(path: str):
        ext = os.path.splitext(path)[1].lower()

        if ext == ".pdf":
            loader = UnstructuredPDFLoader(path, strategy="auto")  
        elif ext in [".doc", ".docx"]:
            loader = UnstructuredWordDocumentLoader(path, strategy="auto")   
        elif ext in [".ppt", ".pptx"]:
            loader = UnstructuredPowerPointLoader(path, strategy="auto")   
        elif ext in [".txt", ".md"]:
            loader = TextLoader(path, encoding="utf-8")
        else:
            print(f"[SKIP] Unsupported file type: {ext}")
            return []

        try:
            docs = loader.load()
            for d in docs:
                d.metadata["source"] = os.path.basename(path)
            return docs

        except Exception as e:
            print(f"[WARN] Could not load {path}: {e}")
            return []


class LangChunker:
    """Splits LangChain Document objects into chunks."""

    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
        )

    def chunk_docs(self, docs: List) -> List:
        return self.splitter.split_documents(docs)

