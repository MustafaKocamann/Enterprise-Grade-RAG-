<div align="center">
  <img src="./docs/assets/readme-hero.svg" alt="Enterprise Agentic RAG animated architecture banner" width="100%" />
</div>

<div align="center">

[![Python 3.13](https://img.shields.io/badge/Python-3.13-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.143+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agentic_Workflow-1C3C3C?style=for-the-badge)](https://langchain-ai.github.io/langgraph/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.65+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Neon](https://img.shields.io/badge/Neon-Serverless_Postgres-00E699?style=for-the-badge&logo=postgresql&logoColor=07111F)](https://neon.com/)
[![Qdrant](https://img.shields.io/badge/Qdrant-Vector_Search-DC244C?style=for-the-badge)](https://qdrant.tech/)

**A production-oriented, source-grounded knowledge assistant with agentic routing, hybrid resilience, durable memory, guardrails, observability, and measurable RAG quality.**

[Overview](#overview) · [Architecture](#architecture) · [Quick Start](#quick-start) · [Configuration](#configuration) · [API](#api-reference) · [Evaluation](#evaluation) · [Operations](#operations)

</div>

---

## Overview

Enterprise Agentic RAG turns heterogeneous technical documentation into a conversational knowledge system. A LangGraph workflow classifies each request, retrieves and reranks relevant context when needed, synthesizes a grounded answer through an LLM gateway, and persists conversation state in Neon Postgres.

The repository contains the complete application lifecycle:

- **Ingestion** for PDF, HTML, TXT, DOCX, and PPTX documents.
- **Agentic orchestration** with conversational and retrieval-aware routes.
- **Vector retrieval** through Qdrant with semantic reranking.
- **Durable memory** through LangGraph checkpoints stored in Neon Postgres.
- **Safety controls** through NeMo Guardrails, bearer authentication, and rate limiting.
- **Observability** through Logfire, LangSmith-compatible tracing, and Prometheus metrics.
- **Evaluation** through a golden dataset, RAGAS metrics, and tool-selection correctness.
- **User experience** through a responsive, enterprise-style Streamlit workspace.

> [!IMPORTANT]
> This project integrates multiple managed services. A successful local start requires valid LLM, Qdrant, and embedding credentials. Neon, Upstash, tracing, and managed reranking can degrade to documented fallbacks where supported.

## Key Capabilities

| Area | Capability | Implementation |
|---|---|---|
| Orchestration | Intent-aware routing and stateful execution | LangGraph planner → retriever → responder |
| Retrieval | Semantic vector search with retry behavior | Qdrant `query_points` |
| Ranking | Top-k semantic reranking | Jina Reranker API with original-order fallback |
| Embeddings | Managed embeddings with local resilience | Jina Embeddings v3 → local `mxbai-embed-large-v1` |
| Memory | Durable per-thread checkpoints | Neon Postgres + `PostgresSaver` |
| Generation | Gateway-routed LLM inference and cache metadata | Portkey |
| Safety | Input policy enforcement | NeMo Guardrails |
| API protection | Optional bearer token and request throttling | FastAPI security + SlowAPI |
| Observability | Traces, structured events, and metrics | Logfire, LangSmith, Prometheus |
| Quality | Six offline/online evaluation dimensions | RAGAS + deterministic tool correctness |

## Architecture

```mermaid
flowchart LR
    U[User] --> UI[Streamlit Workspace]
    UI -->|POST /query| API[FastAPI Service]

    API --> G{NeMo Guardrails}
    G -->|Blocked| SAFE[Policy Response]
    G -->|Allowed| P[LangGraph Planner]

    P -->|Conversational| R[Responder]
    P -->|Technical| E[Query Embedding]
    E --> Q[(Qdrant)]
    Q --> RR[Jina Reranker]
    RR --> R

    R --> GW[Portkey Gateway]
    GW --> LLM[LLM Provider]
    R --> API

    API <--> N[(Neon Postgres<br/>Checkpoints)]
    API -. traces .-> LF[Logfire / LangSmith]
    API -. metrics .-> PM[Prometheus]

    SAFE --> API
    API --> UI
```

### Request Lifecycle

1. The Streamlit client submits a question with a persistent `thread_id`.
2. FastAPI applies authentication and rate-limit policies.
3. NeMo Guardrails evaluates the request before any retrieval or generation work.
4. The planner chooses a conversational response or creates a refined search query.
5. Technical queries retrieve candidates from Qdrant and rerank the best context.
6. The responder builds a grounded prompt and calls the model through Portkey.
7. LangGraph stores state in Neon Postgres and returns the answer, steps, status, and sources.
8. The UI presents the answer with expandable processing details and evidence.

## Technology Stack

| Layer | Technology |
|---|---|
| Web API | FastAPI, Uvicorn, Pydantic Settings |
| Web UI | Streamlit |
| Agent runtime | LangGraph, LangChain |
| LLM gateway | Portkey |
| Guardrails | NVIDIA NeMo Guardrails |
| Vector database | Qdrant |
| Embeddings | Jina Embeddings v3, Sentence Transformers fallback |
| Reranking | Jina Reranker v3.5 |
| State persistence | Neon Serverless Postgres, Psycopg 3 |
| Rate limiting | Upstash Redis or in-memory fallback |
| Observability | Logfire, LangSmith, Prometheus |
| Evaluation | RAGAS, golden datasets, Streamlit evaluation console |
| Backend resources | Neon Auth, Object Storage, Functions |

## Repository Structure

```text
.
├── app/
│   ├── agents/                  # LangGraph state, graph, and agent nodes
│   ├── gateway/                 # Portkey-backed model access
│   ├── guardrails/              # NeMo rails and policy definitions
│   ├── ingestion/               # Loaders, chunking, embedding, and indexing
│   ├── services/
│   │   ├── health/              # External dependency checks
│   │   └── retrieval/           # Embeddings, Qdrant, and reranking
│   ├── config.py                # Centralized environment validation
│   ├── health.py                # Health and readiness routes
│   └── main.py                  # FastAPI entry point
├── ui/app.py                    # Production chat workspace
├── evals/                       # Golden dataset pipeline and RAGAS console
├── data/                        # Source documents grouped by trust profile
├── processed_data/              # Parsed and chunked document artifacts
├── docs/assets/                 # README visual assets
├── neon.ts                      # Declarative Neon backend resources
├── hello.ts                     # Example Neon Function
├── package.json                 # Neon configuration tooling
└── pyproject.toml               # Python package and dependency definition
```

## Quick Start

### Prerequisites

- **Python 3.13 or newer**
- **uv** for Python dependency and environment management
- **Node.js and npm** only when managing Neon resources
- A reachable **Qdrant** deployment
- Credentials for the configured LLM and embedding providers
- A **Neon Postgres** connection for durable production memory

### 1. Install Dependencies

```bash
uv sync
```

For Neon configuration tooling:

```bash
npm ci
```

### 2. Configure the Environment

Create `.env` in the repository root. Keep secrets out of source control.

```dotenv
# Required by the current Settings model
GOOGLE_API_KEY=replace-me
EVREN_API_KEY=replace-me
GOOGLE_FALLBACK_API_KEY=replace-me

# Agent generation and guardrails
PORTKEY_API_KEY=replace-me
PORTKEY_PRIMARY_CONFIG_ID=pc-replace-me
GROQ_SLUG=rag
GROQ_API_KEY=replace-me

# Vector search
QDRANT_CLUSTER_ENDPOINT=https://your-cluster.qdrant.io
QDRANT_API_KEY=replace-me
QDRANT_COLLECTION=enterprise_rag

# Managed embeddings and reranking; optional local embedding fallback is available
JINA_API_KEY=replace-me

# Durable LangGraph memory
DATABASE_URL=postgresql://user:password@host/neondb?sslmode=require

# Optional API security
RAG_API_KEY=replace-with-a-long-random-value
RATE_LIMIT_PER_MINUTE=20
STRICT_STARTUP=false

# Optional observability
LOGFIRE_TOKEN=replace-me
LANGSMITH_API_KEY=replace-me
LANGSMITH_PROJECT=enterprise-rag
```

See [Configuration](#configuration) for optional Neon, Redis, and tracing settings.

### 3. Provision Neon Resources

The declarative configuration in `neon.ts` defines Neon Auth, a private `assets` bucket, an example Function, and branch lifecycle behavior.

```bash
# Authenticate once if the CLI requests it
npx neon@latest login

# Link or initialize the repository when needed
npx neon@latest init

# Review and deploy the declared resources
npm run build
npx neon@latest deploy
```

`neon deploy` can synchronize generated service variables into `.env.local`. The Python settings layer reads both `.env` and `.env.local`.

### 4. Ingest Documents

Ingest the trusted sample corpus and create the Qdrant collection when it does not exist:

```bash
uv run python -m app.ingestion.processor data/true_data true
```

To recreate the collection before indexing:

```bash
uv run python -m app.ingestion.processor data/true_data true --wipe
```

> [!CAUTION]
> `--wipe` deletes the configured Qdrant collection before rebuilding it. Use it only when a full re-index is intended.

### 5. Start the API

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Verify the service:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "healthy",
  "service": "enterprise-agentic-rag"
}
```

### 6. Start the Workspace

In a second terminal:

```bash
uv run streamlit run ui/app.py --server.port 8501
```

Open [http://localhost:8501](http://localhost:8501).

The UI uses `http://localhost:8000` by default. Override it when the API runs elsewhere:

```dotenv
BACKEND_URL=https://api.example.com
```

## Configuration

### Core Runtime

| Variable | Required | Purpose |
|---|:---:|---|
| `PORTKEY_API_KEY` | Runtime | Authenticates planner and responder requests through Portkey |
| `PORTKEY_PRIMARY_CONFIG_ID` | Recommended | Uses a saved Portkey routing configuration |
| `GROQ_SLUG` | No | Portkey virtual key slug; defaults to `rag` |
| `GROQ_API_KEY` | Runtime | Runs the NeMo Guardrails classification model |
| `QDRANT_CLUSTER_ENDPOINT` or `QDRANT_URL` | Yes | Qdrant endpoint |
| `QDRANT_API_KEY` | Cloud only | Qdrant Cloud authentication |
| `QDRANT_COLLECTION` | No | Collection name; defaults to `enterprise_rag` |
| `JINA_API_KEY` | Recommended | Enables managed embeddings and semantic reranking |
| `GOOGLE_API_KEY` | Settings | Validated by the current settings model |
| `EVREN_API_KEY` | Settings | Validated by the current settings model |
| `GOOGLE_FALLBACK_API_KEY` | Settings | Validated by the current settings model |

### Persistence and Security

| Variable | Required | Purpose |
|---|:---:|---|
| `DATABASE_URL` or `NEON_DB_URL` | Production | Neon Postgres connection for LangGraph checkpoints |
| `RAG_API_KEY` | No | Enables bearer authentication for protected routes |
| `RATE_LIMIT_PER_MINUTE` | No | Per-client request limit; defaults to `20` |
| `STRICT_STARTUP` | No | Fails startup when dependency checks fail |
| `NEON_AUTH_REQUIRED` | No | Replaces static API-key validation with Neon Auth JWT validation |
| `NEON_AUTH_BASE_URL` | With Neon Auth | Expected token issuer |
| `NEON_AUTH_JWKS_URL` | With Neon Auth | Public signing-key endpoint |

### Resilience and Observability

| Variable | Required | Purpose |
|---|:---:|---|
| `UPSTASH_REDIS_REST_URL` | No | Redis host used for distributed rate limiting |
| `UPSTASH_REDIS_REST_TOKEN` | No | Redis credential |
| `LOGFIRE_TOKEN` | No | Distributed traces and structured application events |
| `LOGFIRE_BASE_URL` | No | Custom or regional Logfire endpoint |
| `LANGSMITH_API_KEY` | No | LangChain/LangGraph tracing |
| `LANGSMITH_PROJECT` | No | Trace project name |
| `BACKEND_URL` | UI only | FastAPI base URL used by Streamlit |

## API Reference

Interactive OpenAPI documentation is available at [http://localhost:8000/docs](http://localhost:8000/docs) while the API is running.

| Method | Endpoint | Description | Authentication |
|---|---|---|---|
| `GET` | `/` | Service identity | Public |
| `GET` | `/health` | Basic health response | Public |
| `GET` | `/healthz` | Liveness response | Public |
| `GET` | `/readyz` | Readiness response | Public |
| `GET` | `/graph` | Rendered LangGraph workflow | Configurable |
| `POST` | `/query` | Execute the guarded RAG workflow | Configurable |
| `GET` | `/metrics` | Prometheus metrics | Public by default |

### Query Example

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $RAG_API_KEY" \
  -d '{
    "q": "How does Kubernetes horizontal pod autoscaling work?",
    "thread_id": "engineering-session-001"
  }'
```

If `RAG_API_KEY` and Neon Auth are both disabled, omit the `Authorization` header.

### Response Contract

```json
{
  "question": "How does Kubernetes horizontal pod autoscaling work?",
  "answer": "...",
  "thought_process": [
    "Intent: Technical",
    "Search Term: Kubernetes horizontal pod autoscaling",
    "Context Retrieved"
  ],
  "status": "Response generated.",
  "sources": [
    "CONTENT: ..."
  ]
}
```

Guardrail blocks use the same response shape with `status` set to `Blocked by guardrails.` and an empty `sources` list.

## Document Ingestion

The ingestion pipeline follows a deterministic sequence:

```mermaid
flowchart LR
    F[PDF / HTML / TXT / DOCX / PPTX] --> X[Text Extraction]
    X --> C[Semantic Chunking]
    C --> J[Processed JSON]
    C --> E[1024-d Embeddings]
    E --> Q[(Qdrant Collection)]
```

- Parsed artifacts are written under `processed_data/<source_type>/`.
- The source filename and trust profile are stored in each Qdrant payload.
- Jina embeddings are processed in batches of 64.
- If Jina is unavailable, the application loads a local Sentence Transformers model.
- Collection distance is cosine similarity with 1024-dimensional vectors.

## Evaluation

The evaluation console runs the live API against `evals/golden_dataset.json` and calculates six dimensions:

| Metric | Question Answered |
|---|---|
| Faithfulness | Is the answer supported by retrieved context? |
| Answer Relevancy | Does the answer address the user question? |
| Context Precision | Are retrieved chunks relevant and focused? |
| Context Recall | Did retrieval find the expected evidence? |
| Answer Correctness | Does the answer match the reference answer? |
| Tool Correctness | Did the planner choose the expected execution path? |

Start the API first, then launch the evaluation console on a separate port:

```bash
uv run streamlit run evals/app.py --server.port 8502
```

Open [http://localhost:8502](http://localhost:8502).

> [!NOTE]
> The evaluation pipeline currently calls `http://localhost:8000/query` without an authorization header. Run local evaluations with `RAG_API_KEY` and Neon Auth disabled, or extend `evals/pipeline.py` to send the configured token.

## Operations

### Health, Readiness, and Metrics

```bash
curl http://localhost:8000/health
curl http://localhost:8000/healthz
curl http://localhost:8000/readyz
curl http://localhost:8000/metrics
```

At startup, the API also probes configured external dependencies. Set `STRICT_STARTUP=true` when deployment should fail instead of running with degraded integrations.

### Resilience Model

| Failure | Runtime Behavior |
|---|---|
| Neon Postgres unavailable | Falls back to in-memory LangGraph checkpoints; state is lost on restart |
| Upstash Redis unavailable | Uses process-local rate limiting |
| Jina Embeddings unavailable | Loads local `mxbai-embed-large-v1` embeddings |
| Jina reranking unavailable | Preserves the original Qdrant ranking |
| Qdrant search repeatedly fails | Returns an empty retrieval set and logs the failure |
| Transient model/retrieval errors | Retries with exponential backoff where configured |
| Guardrail policy match | Skips the graph and immediately returns the policy response |

### Production Checklist

- [ ] Use a pooled Neon connection string with `sslmode=require`.
- [ ] Set `STRICT_STARTUP=true` after all managed dependencies are configured.
- [ ] Enable Neon Auth or set a strong `RAG_API_KEY`.
- [ ] Protect `/metrics` and documentation routes at the ingress layer.
- [ ] Configure Upstash Redis for distributed rate limits across replicas.
- [ ] Configure Logfire and/or LangSmith tracing with appropriate data-retention policies.
- [ ] Run ingestion before serving technical queries.
- [ ] Run the golden-dataset evaluation after model, prompt, or retrieval changes.
- [ ] Store all credentials in a managed secret store; never commit `.env` files.

## Neon Backend

`neon.ts` is the declarative source of truth for branch-scoped Neon resources:

- **Postgres** supplies durable LangGraph checkpoints through `DATABASE_URL`.
- **Auth** can validate JWT bearer tokens when `NEON_AUTH_REQUIRED=true`.
- **Object Storage** declares a private `assets` bucket.
- **Functions** deploys the example `hello.ts` function.
- **Branch policy** gives new non-default branches a seven-day TTL.

Validate the Neon plan without deploying:

```bash
npm run build
```

Deploy the configuration:

```bash
npx neon@latest deploy
```

## Troubleshooting

<details>
<summary><strong>The API fails during settings initialization</strong></summary>

The current `Settings` model validates `GOOGLE_API_KEY`, `EVREN_API_KEY`, `GOOGLE_FALLBACK_API_KEY`, and the Qdrant endpoint at import time. Ensure they are present in `.env` or `.env.local`, even when the active request path uses Portkey.

</details>

<details>
<summary><strong>The Streamlit UI reports that the API is offline</strong></summary>

Confirm that FastAPI is listening on port `8000`, then verify `BACKEND_URL`. When UI and API run on different hosts, `BACKEND_URL` must be reachable from the Streamlit process.

</details>

<details>
<summary><strong>Technical questions return no supporting context</strong></summary>

Verify the configured collection name, run the ingestion command, and inspect Qdrant for indexed points. The application defaults to the `enterprise_rag` collection.

</details>

<details>
<summary><strong>Conversation memory disappears after restart</strong></summary>

The API could not initialize the Neon-backed checkpointer and fell back to `MemorySaver`. Validate `DATABASE_URL`, TLS parameters, network access, and the startup logs.

</details>

<details>
<summary><strong>The first embedding request is slow</strong></summary>

When `JINA_API_KEY` is absent or unreachable, the local fallback model is downloaded and initialized on first use. Subsequent requests reuse the loaded model.

</details>

## Engineering Notes

- Conversation continuity is keyed by `thread_id`; clients should reuse it across related requests.
- Neon checkpoint migrations run through a separate autocommit connection because they include concurrent index creation.
- Retrieved context is bounded before generation to reduce model token pressure.
- The responder surfaces Portkey cache hits in the workflow status when the gateway reports them.
- Prometheus includes application-specific request, latency, and guardrail counters in addition to HTTP instrumentation.

---

<div align="center">
  <strong>Built for traceable answers, resilient retrieval, and measurable enterprise AI quality.</strong>
  <br />
  <sub>FastAPI · LangGraph · Qdrant · Neon · Streamlit</sub>
</div>
