# FabSight v0.6 knowledge retrieval

## Current knowledge-base 2.0 profile

The deployed portfolio now packages 33 synthetic educational Markdown documents:
the original three references plus 30 detailed investigation guides. The corpus is
split into 156 traceable chunks and covers fab process steps, wafer-map patterns,
equipment and maintenance review, synthetic telemetry scenarios, multimodal evidence
conflicts, human approval, containment, and citation quality. The committed FAISS
index remains small enough for Streamlit while being substantial enough to demonstrate
topic-specific retrieval. A 15-query top-three sanity suite currently produces 15
expected-topic hits; this remains a software retrieval check, not a production-quality
or causal-validity benchmark.

FabSight v0.6 adds a local retrieval foundation. It does not add an autonomous agent,
LLM-generated answer, or case-specific physical conclusion.

## What is RAG?

RAG means Retrieval-Augmented Generation. It normally contains two broad parts:

```text
retrieval + generation
```

FabSight v0.6 implements retrieval. It discovers local references, extracts text,
splits it into passages, creates embeddings, stores them in a local vector index, and
returns passages relevant to a query. A later version may use those passages in a
generation workflow.

## Why retrieve references?

Technical software should consult traceable source material instead of relying only
on a language model's memory. Retrieval lets a user inspect the exact passage,
filename, page where available, source type, and similarity score.

## Embeddings and vector storage

An embedding is a numerical representation of text that places semantically similar
text closer together. FabSight uses the lightweight local
`sentence-transformers/all-MiniLM-L6-v2` model. The first use downloads the model;
later use can load it from `models/embeddings/` without an API key.

A vector database is a searchable store of embeddings. FabSight uses one local FAISS
`IndexFlatIP` index. Text and query vectors are normalized, so inner product behaves
like cosine similarity. A similarity score ranks closeness; it is not a probability
that a passage is correct.

## Document support and provenance

Place `.pdf`, `.txt`, or `.md` files in `data/knowledge/raw/`. PDF pages are extracted
separately so page numbers survive retrieval. A `document_provenance.json` manifest
may label each source as:

- `PUBLIC_REFERENCE`
- `USER_PROVIDED`
- `SYNTHETIC_EDUCATIONAL`

Files absent from the manifest default to `USER_PROVIDED`. Provenance, source
filename, page, document type, and custom metadata remain attached to every chunk.

The included corpus contains synthetic educational references. Each states that it
is not a production SOP. They contain no recipes, doses, private limits, or
company-specific procedures. Run `scripts/generate_synthetic_knowledge.py` to
reproduce the 30-document expansion, then `scripts/build_knowledge_base.py` to rebuild
the chunks, embeddings, index, and evaluation report.

## Chunking

Large documents are split into passages of approximately 1,000 characters with 150
characters of overlap. Overlap keeps information near a chunk boundary from being
lost. These settings are configurable and recorded in index metadata.

## Case retrieval

```text
ManufacturingCase
       ↓
concise technical query
       ↓
KnowledgeRetriever
       ↓
cited potentially relevant passages
```

The query builder uses the process step, risk band, wafer-map class, evidence status,
and generic monitoring concepts. It does not dump the case JSON or assign physical
meaning to anonymous process features.

Retrieval is not a conclusion. A passage about an edge pattern, equipment monitoring,
or etch variation does not prove that topic explains a particular case. Retrieved
document text must also be treated as untrusted data, never as executable instructions
or system commands.

## Basic evaluation

Fifteen educational queries check whether an expected topic appears in the top three
results. This hit rate is a retrieval sanity check, not a production benchmark.

## Architectural progression

```text
v0.1  fab structure
v0.2  process data
v0.3  process ML
v0.4  wafer vision
v0.5  multimodal case integration
v0.6  local knowledge retrieval
```

There is still no agent, autonomous planning, or generated investigation report.
