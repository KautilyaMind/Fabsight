# FabSight v0.7 — Grounded RAG Generation

FabSight is an educational portfolio project. It uses public, synthetic, and user-provided educational material—not proprietary process data, confidential procedures, recipes, or equipment configurations.

## What full RAG means

Retrieval-Augmented Generation is `retrieval + generation`. v0.6 stopped after finding relevant passages. v0.7 passes those passages to a configured text LLM and asks it to produce a grounded, cited explanation.

```text
Question / ManufacturingCase
           ↓
      Query Builder
           ↓
 KnowledgeRetriever
           ↓
  Relevant Chunks
           ↓
     Context Builder
           ↓
          LLM
           ↓
  Grounded RAG Response
           ↓
       Citations
```

Embeddings are not the LLM. FAISS is not the LLM. The retriever is not the LLM, and the LLM does not search FAISS. Python embeds the query, searches the vector index, and assembles context; only then is that bounded context sent to the LLM.

## Configuration

Copy `.env.example` to `.env` and supply credentials. `.env` is ignored by Git. v0.7 initially supports the Google Gemini Developer API through a small `LLMClient` interface. The model is always read from `LLM_MODEL`; the application never silently substitutes another model. `LLM_API_KEY` is portable, while the existing `GOOGLE_API_KEY` name is also accepted for Google.

The example uses the stable `gemini-3.5-flash-lite` model, which Google currently lists with a free tier. Availability, quota, and pricing are controlled by Google and can change. Set `RAG_TOP_K`, `RAG_MAX_CONTEXT_CHARS`, and `RAG_MAX_CHUNK_CHARS` to control retrieval and prompt size.

Without credentials, local retrieval still succeeds and generation reports a clear configuration error.

## Grounding and citations

Each retrieved chunk receives a stable identifier such as `[S1]`. The model may cite only those identifiers, and the post-generation validator rejects invented citation IDs. Source filename, page (for PDFs), source type, and chunk ID are retained in `RAGResponse`.

The context includes compact model outputs, not all anonymous SECOM values. Anonymous variables remain anonymous and cannot be mapped to temperature, pressure, or other physical concepts. Case linkage remains synthetic.

Grounding means the answer is based on supplied evidence. Hallucination is plausible-sounding content unsupported by that evidence. Retrieval-before-generation and visible citations make support inspectable, though they cannot guarantee correctness.

Retrieved text is bounded by `BEGIN/END UNTRUSTED DOCUMENT CONTENT`. The system prompt says document instructions must not change behavior, reveal secrets, execute code, or invoke commands. The application itself never executes retrieved text.

## Validation and limitations

The LLM returns JSON matching a response schema. Malformed output gets one controlled retry, then fails clearly. A lightweight validator flags anonymous-feature physical mappings and phrases such as “confirmed root cause” or “definitely caused.” These checks are guardrails, not a perfect truth evaluator.

The case response separates observations, investigation areas, missing evidence, limitations, and sources. It never contains a confirmed-root-cause section. FabSight is not a replacement for qualified process engineers.

## Fixed RAG chain versus an agent

v0.7 follows one predetermined route: case → retrieve → generate → answer. It does not choose tools, loop, plan root-cause analysis, maintain chat memory, or autonomously request evidence. A future agent could decide what it needs and repeat tool use; v0.7 does none of that.

## Commands

```powershell
python scripts/ask_fabsight.py --question "What is CMP?"
python scripts/explain_case.py --case CASE-00042
python scripts/evaluate_rag.py
```

Evaluation covers roughly ten curated questions at two layers: expected-topic retrieval and simple generation checks for structured output, real citations, sources, and guardrail patterns. Results go to `reports/rag/rag_evaluation.json`; this is a transparent sanity check, not an automatic scientific truth evaluator.
