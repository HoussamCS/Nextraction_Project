# NEXTRACION – Nextraction 2

**Web-based Retrieval-Augmented Generation (RAG) Pipeline for Evidence-First Insights**

## Overview

NEXTRACION is a FastAPI microservice that extracts high-signal insights from public web sources using a production-grade RAG pipeline. The system crawls web pages, indexes content in a vector database, and answers user questions with **mandatory citations, confidence levels, and explicit refusal when evidence is insufficient**.

**Core Guarantee:** The system never hallucinates or fabricates information. Every factual claim is grounded in retrieved evidence.

## Key Features

 **Domain-controlled web crawling** – Fetches only from whitelisted domains  
 **Bounded ingestion** – Enforces max pages and max crawl depth  
 **Content cleaning** – Removes navigation, boilerplate, and noise  
 **Vector embeddings** – OpenAI-powered semantic search  
 **Anti-hallucination** – Strict grounding with citations  
 **Confidence estimation** – Explicit confidence levels (high/medium/low)  
 **Background jobs** – Async ingestion with real-time progress tracking  
 **Docker-ready** – One-command startup with docker-compose  

## Technical Stack

- **Backend:** FastAPI (Python 3.11+)
- **Embeddings:** OpenAI (text-embedding-3-small)
- **LLM:** GPT-4 Turbo
- **Vector Store:** Chroma (DuckDB + Parquet)
- **HTML Parsing:** BeautifulSoup4
- **Containerization:** Docker + docker-compose

## Installation

### Prerequisites

- Python 3.11+
- OpenAI API key
- Docker & docker-compose (optional)

### 1. Clone and Setup

```bash
git clone <repo>
cd Nextraction_Project
```

### 2. Create Environment File

```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:

```
OPENAI_API_KEY=sk-...your-key...
OPENAI_CHAT_MODEL=gpt-4-turbo
CHROMA_DB_PATH=./data/chroma_db
DEFAULT_MAX_PAGES=20
DEFAULT_MAX_DEPTH=2
TOP_K_CHUNKS=5
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Running the Service

### Option A: Local Development

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

Service runs at: `http://localhost:8000`

### Option B: Docker Compose (Recommended)

```bash
docker-compose up -d
```

Service runs at: `http://localhost:8000`

**View logs:**
```bash
docker-compose logs -f nextracion
```

**Stop service:**
```bash
docker-compose down
```

## API Endpoints

### 1. POST `/ingest` – Start Ingestion Job

**Request:**
```json
{
  "seed_urls": [
    "https://example.com/blog",
    "https://example.com/docs"
  ],
  "domain_allowlist": ["example.com"],
  "max_pages": 20,
  "max_depth": 2,
  "user_notes": "Quarterly company announcements"
}
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "accepted_pages": 2
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "seed_urls": ["https://openai.com/blog"],
    "domain_allowlist": ["openai.com"],
    "max_pages": 10,
    "max_depth": 1
  }'
```

---

### 2. GET `/status/{job_id}` – Check Progress

**Response:**
```json
{
  "state": "running",
  "pages_fetched": 5,
  "pages_indexed": 12,
  "errors": ["Timeout fetching https://example.com/page3"]
}
```

**cURL Example:**
```bash
curl http://localhost:8000/status/550e8400-e29b-41d4-a716-446655440000
```

**States:**
- `queued` – Waiting to start
- `running` – Actively crawling/indexing
- `done` – Complete, ready for queries
- `failed` – Failed with errors

---

### 3. POST `/ask` – Answer Question

**Request:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "question": "What are the latest company announcements?"
}
```

**Response:**
```json
{
  "answer": "According to OpenAI's recent announcements, GPT-4 Turbo was released with improved reasoning [Chunk 0] and lower latency [Chunk 1].",
  "citations": [
    {
      "url": "https://openai.com/blog/gpt-4-turbo",
      "title": "Introducing GPT-4 Turbo",
      "chunk_id": "abc123def456",
      "quote": "GPT-4 Turbo offers improved reasoning and lower latency...",
      "score": 0.92
    }
  ],
  "confidence": "high",
  "grounding_notes": "Answer supported by 1 relevant source with high confidence (avg similarity: 0.92)."
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "question": "What are the latest announcements?"
  }'
```

**Confidence Levels:**
- `high` – Answer well-supported (avg similarity > 0.6, multiple sources)
- `medium` – Partially supported (similarity 0.4-0.6 or single source)
- `low` – Weak support (similarity < 0.4, insufficient evidence)

---

### 4. GET `/health` – Health Check

**Response:**
```json
{
  "status": "healthy",
  "version": "2.0"
}
```

**cURL Example:**
```bash
curl http://localhost:8000/health
```

---

## Configuration

All settings via environment variables (see `.env`):

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | (required) | OpenAI API key |
| `OPENAI_MODEL` | text-embedding-3-small | Embedding model |
| `OPENAI_CHAT_MODEL` | gpt-4-turbo | Chat/generation model |
| `CHROMA_DB_PATH` | ./data/chroma_db | Vector store location |
| `DEFAULT_MAX_PAGES` | 20 | Default max pages per crawl |
| `DEFAULT_MAX_DEPTH` | 2 | Default max crawl depth |
| `TOP_K_CHUNKS` | 5 | Chunks to retrieve for answering |
| `MIN_SIMILARITY_SCORE` | 0.3 | Minimum relevance threshold |
| `JOB_TIMEOUT` | 300 | Job timeout (seconds) |

## Testing

Run tests with pytest:

```bash
pytest tests/ -v
```

**Test coverage includes:**
- API endpoint validation
- Domain allowlist enforcement
- Max pages/depth constraints
- Job state transitions
- Error handling
- Citation extraction

## Example Workflow

### 1. Ingest Content

```bash
JOB_ID=$(curl -s -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "seed_urls": ["https://github.com/openai/release-notes"],
    "domain_allowlist": ["github.com"],
    "max_pages": 5,
    "max_depth": 1
  }' | jq -r '.job_id')

echo "Job ID: $JOB_ID"
```

### 2. Monitor Progress

```bash
curl http://localhost:8000/status/$JOB_ID | jq '.'
```

Wait for `state` to be `"done"`.

### 3. Ask Questions

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d "{
    \"job_id\": \"$JOB_ID\",
    \"question\": \"What improvements were made?\"
  }" | jq '.'
```

## Pipeline Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    INGESTION PIPELINE                    │
├──────────────────────────────────────────────────────────┤
│ 1. Crawl    │ 2. Clean    │ 3. Chunk   │ 4. Embed   │ 5. Index  │
│ (WebScraper)│ (BeautifulSoup) │ (Sliding)│ (OpenAI)│ (Chroma)  │
└──────────────────────────────────────────────────────────┘
                              ↓
                    ┌─────────────────┐
                    │  Vector Store   │
                    │    (Chroma)     │
                    └─────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────┐
│                   GENERATION PIPELINE                    │
├──────────────────────────────────────────────────────────┤
│ 1. Retrieve │ 2. Ground  │ 3. Generate │ 4. Extract  │ 5. Format │
│ (Semantic)  │ (Evidence) │ (LLM)      │ (Citations) │ (Response)│
└──────────────────────────────────────────────────────────┘
```

## Anti-Hallucination Safeguards

1. **Mandatory Grounding:** Every claim in answer must reference at least one chunk
2. **Evidence Refusal:** Explicitly refuses when evidence is insufficient
3. **Confidence Estimation:** Returns confidence based on evidence quality
4. **Citation Quality:** Short quotes + relevance scores
5. **Post-generation Checks:** Identifies and removes unsupported claims
6. **System Prompt:** LLM explicitly instructed to refuse speculative answers

## Design Trade-offs

### 1. In-Memory Job Queue vs. External Task Queue
**Choice:** In-memory (FastAPI `BackgroundTasks`)  
**Trade-off:** Simpler for MVP, but jobs lost on restart. Production would use Redis/Celery.

### 2. Local Chroma vs. Remote Vector Store
**Choice:** Local persistent (DuckDB+Parquet)  
**Trade-off:** Suitable for dev/testing. Production would use cloud Chroma or Pinecone.

### 3. Top-K Retrieval vs. Threshold-Based
**Choice:** Top-K (5 chunks)  
**Trade-off:** Consistent context, but may include weak sources. Mitigated by confidence scoring.

### 4. Synchronous Crawling vs. Async
**Choice:** Synchronous with polite delays  
**Trade-off:** Slower crawling, but respects server norms and reduces load.

## Security Considerations

 **Current Implementation (Development):**
- No authentication on API endpoints
- Environment variables control sensitive config
- No rate limiting implemented

**Production Recommendations:**
- Add API key authentication
- Implement rate limiting (e.g., FastAPI SlowAPI)
- Use secrets management (AWS Secrets Manager, HashiCorp Vault)
- Validate and sanitize user inputs
- Run in authenticated VPC
- Enable HTTPS/TLS

## Logging

Logs are output to console for easy debugging:

```
2024-01-15 14:23:45 - src.services.web_scraper - INFO - Fetched page 1/20: https://example.com
2024-01-15 14:23:50 - src.services.embeddings - INFO - Stored chunk abc123 from https://example.com
```

## Performance Characteristics

- **Embedding generation:** ~0.5s per chunk (OpenAI API)
- **Vector search:** <100ms for 10k chunks (Chroma)
- **LLM generation:** 2-5s per answer (GPT-4 Turbo)
- **Crawling:** ~1s per page (polite delays)

## Troubleshooting

### OpenAI API Errors
```
Error: "Invalid API key"
→ Check OPENAI_API_KEY in .env
→ Ensure sufficient quota in OpenAI account
```

### Chroma Connection Issues
```
Error: "Failed to get/create collection"
→ Check CHROMA_DB_PATH is writable
→ Ensure DuckDB is installed
```

### Job Stuck in "running"
```
→ Check logs: docker-compose logs nextracion
→ Verify internet connection
→ Check constraints (max_pages, max_depth)
```

## References

- [OpenAI API Docs](https://platform.openai.com/docs)
- [Chroma Docs](https://docs.trychroma.com/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [BeautifulSoup Docs](https://www.crummy.com/software/BeautifulSoup/)

## License

Proprietary – NEXTRACION 2024


4. Configure environment variables:
   - Copy `.env.example` to `.env` and fill in the necessary values.

## Running the Application
To start the FastAPI application, run:
```
uvicorn src.main:app --reload
```

## API Endpoints
- **Ingest Data**: `POST /ingest`
- **Check Status**: `GET /status/{job_id}`
- **Ask a Question**: `POST /ask`
- **Health Check**: `GET /health`

## Example Curl Commands
1. Ingest data:
   ```
   curl -X POST "http://localhost:8000/ingest" -H "Content-Type: application/json" -d '{"url": "http://example.com"}'
   ```

2. Ask a question:
   ```
   curl -X POST "http://localhost:8000/ask" -H "Content-Type: application/json" -d '{"question": "What is the insight?"}'
   ```

## License
This project is licensed under the MIT License. See the LICENSE file for more details.