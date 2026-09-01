"""Stable citations derived exclusively from retrieved results."""

from __future__ import annotations

import re

from fabsight.knowledge.retriever import RetrievalResult
from fabsight.rag.response_schema import RAGSource

CITATION_PATTERN = re.compile(r"\[S(\d+)\]")
BRACKET_CITATION_PATTERN = re.compile(r"\[((?:S\d+)(?:\s*,\s*S\d+)*)\]")


def build_sources(results: list[RetrievalResult]) -> list[RAGSource]:
    return [RAGSource(f"S{i}", r.source_file, r.page, r.source_type, r.chunk_id) for i, r in enumerate(results, 1)]


def invalid_citations(texts: list[str], sources: list[RAGSource]) -> list[str]:
    allowed = {source.citation_id for source in sources}
    found = {
        citation.strip()
        for text in texts
        for group in BRACKET_CITATION_PATTERN.findall(text)
        for citation in group.split(",")
    }
    return sorted(found - allowed)


def cited_source_ids(texts: list[str]) -> set[str]:
    return {
        citation.strip()
        for text in texts
        for group in BRACKET_CITATION_PATTERN.findall(text)
        for citation in group.split(",")
    }
