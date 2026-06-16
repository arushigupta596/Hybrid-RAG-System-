# SEBI/RBI Regulatory Intelligence - Hybrid RAG System

Hybrid RAG system combining BM25 keyword retrieval (Elasticsearch) with dense vector retrieval (Qdrant), fused via Reciprocal Rank Fusion (RRF), re-ranked by a cross-encoder, and answered by an LLM via OpenRouter with source citations.

## Quick Start

```bash
# 1. Start infrastructure
docker compose up -d

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Initialize database
python -m indexing.db

# 4. Copy and configure environment
cp .env.example .env
# Edit .env with your API keys

# 5. Run spiders (data collection)
scrapy crawl sebi_circulars
scrapy crawl sebi_regulations
scrapy crawl rbi_circulars

# 6. Process PDFs into chunks
python -m ingestion.process_all --source all

# 7. Index chunks
python -m indexing.index_all --source all

# 8. Start API
uvicorn api.main:app --reload --port 8000

# 9. Start frontend
cd frontend && npm install && npm run dev
```

## Architecture

- **Elasticsearch**: BM25 keyword search with regulatory synonyms
- **Qdrant**: Dense vector search with BGE-large embeddings
- **RRF Fusion**: Reciprocal Rank Fusion (k=60) to merge sparse and dense results
- **Cross-encoder reranking**: Cohere or local ms-marco model
- **LLM**: Any OpenRouter-compatible model (default: Claude Sonnet 4.6)
- **Frontend**: React + TypeScript + Vite + TailwindCSS
