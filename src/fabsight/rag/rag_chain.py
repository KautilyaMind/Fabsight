"""Fixed retrieve, contextualize, generate, validate pipeline."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from fabsight.integration.case_schema import ManufacturingCase
from fabsight.knowledge.query_builder import build_case_query
from fabsight.knowledge.retriever import KnowledgeRetriever
from fabsight.rag.citations import build_sources, cited_source_ids, invalid_citations
from fabsight.rag.config import LLMSettings
from fabsight.rag.context_builder import build_rag_context
from fabsight.rag.guardrails import find_guardrail_flags
from fabsight.rag.llm_client import GoogleLLMClient, LLMClient, LLMConfigurationError
from fabsight.rag.prompts import CASE_INSTRUCTION, GENERAL_INSTRUCTION, RETRY_INSTRUCTION, SYSTEM_PROMPT
from fabsight.rag.response_schema import LLM_RESPONSE_SCHEMA, RAGResponse

LOGGER = logging.getLogger(__name__)


class RAGChain:
    def __init__(self, retriever: KnowledgeRetriever, llm: LLMClient | None = None, settings: LLMSettings | None = None) -> None:
        self.retriever = retriever
        self.settings = settings or LLMSettings.from_env()
        self.llm = llm

    def _client(self) -> LLMClient:
        if self.llm is not None:
            return self.llm
        return GoogleLLMClient(self.settings)

    def _run(self, query: str, mode: str, case: ManufacturingCase | None = None) -> RAGResponse:
        results = self.retriever.search(query, top_k=self.settings.top_k)
        context = build_rag_context(results, case=case, max_context_chars=self.settings.max_context_chars, max_chunk_chars=self.settings.max_chunk_chars)
        sources = build_sources(context.results)
        instruction = CASE_INSTRUCTION if case else GENERAL_INSTRUCTION
        prompt = f"{instruction}\n\nQUESTION OR TASK\n{query}\n\n{context.text}"
        client = self._client()
        started = time.perf_counter()
        data: dict[str, Any] | None = None
        for attempt in range(2):
            raw = client.generate(SYSTEM_PROMPT, prompt if attempt == 0 else f"{RETRY_INSTRUCTION}\n\n{prompt}", LLM_RESPONSE_SCHEMA)
            try:
                candidate = json.loads(raw)
                required = set(LLM_RESPONSE_SCHEMA["required"])
                if not isinstance(candidate, dict) or not required.issubset(candidate):
                    raise ValueError("missing fields")
                if any(not isinstance(candidate[name], list) for name in required - {"answer"}) or not isinstance(candidate["answer"], str):
                    raise ValueError("wrong field types")
                data = candidate
                break
            except (json.JSONDecodeError, ValueError, TypeError):
                continue
        if data is None:
            raise RuntimeError("LLM returned invalid structured output after retry.")
        text_fields = [data["answer"], *data["observations"], *data["investigation_areas"], *data["additional_evidence"], *data["limitations"]]
        bad_citations = invalid_citations(text_fields, sources)
        if bad_citations:
            raise RuntimeError("LLM cited references that were not retrieved: " + ", ".join(bad_citations))
        cited_ids = cited_source_ids(text_fields)
        if not cited_ids:
            raise RuntimeError("LLM response did not cite any retrieved reference.")
        cited_sources = [source for source in sources if source.citation_id in cited_ids]
        flags = find_guardrail_flags("\n".join(text_fields))
        LOGGER.info("rag mode=%s case_id=%s chunks=%d sources=%s model=%s latency_ms=%.0f truncated=%s", mode, case.case_id if case else None, len(context.results), [s.source_file for s in sources], client.model_name, (time.perf_counter()-started)*1000, context.truncated)
        return RAGResponse(mode, data["answer"], cited_sources, query, [r.to_dict() for r in context.results], data["limitations"], case.case_id if case else None, data["observations"], data["investigation_areas"], data["additional_evidence"], flags, context.truncated)

    def ask(self, question: str) -> RAGResponse:
        question = question.strip()
        if not question:
            raise ValueError("Question cannot be empty.")
        return self._run(question, "general")

    def explain_case(self, case: ManufacturingCase) -> RAGResponse:
        return self._run(build_case_query(case), "case", case)
