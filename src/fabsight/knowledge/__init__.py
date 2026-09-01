"""Local retrieval foundation for FabSight v0.6."""

from .query_builder import build_case_query
from .retriever import KnowledgeRetriever, RetrievalResult

__all__ = ["KnowledgeRetriever", "RetrievalResult", "build_case_query"]
