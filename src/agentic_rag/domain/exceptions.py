"""Custom exceptions for the Agentic RAG system"""


class AgenticRAGException(Exception):
    """Base exception for Agentic RAG system"""
    pass


class ConfigurationError(AgenticRAGException):
    """Raised when there's a configuration error"""
    pass


class RetrievalError(AgenticRAGException):
    """Raised when document retrieval fails"""
    pass


class ProcessingError(AgenticRAGException):
    """Raised when document processing fails"""
    pass


class LLMError(AgenticRAGException):
    """Raised when LLM operations fail"""
    pass


class ConnectorError(AgenticRAGException):
    """Raised when connector operations fail"""
    pass

