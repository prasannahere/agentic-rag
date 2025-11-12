"""State management for RAG pipeline"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel


class QueryState(BaseModel):
    """State for query processing"""
    original_query: str
    expanded_queries: List[str] = []
    selected_query: Optional[str] = None
    retrieved_documents: List[str] = []
    metadata: List[Dict[str, Any]] = []
    scores: List[float] = []
    best_score: float = 0.0
    context: str = ""
    answer: str = ""
    sources: List[Dict[str, Any]] = []


class DocumentState(BaseModel):
    """State for document processing"""
    file_path: str
    file_name: str
    chunks: List[str] = []
    embeddings: List[List[float]] = []
    metadata: List[Dict[str, Any]] = []
    processing_status: str = "pending"  # pending, processing, completed, failed
    error: Optional[str] = None

