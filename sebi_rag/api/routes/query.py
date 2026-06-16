import asyncio
import time

from fastapi import APIRouter
from loguru import logger

from api.config import settings
from api.llm import generate_answer
from api.models import ChunkResult, QueryRequest, QueryResponse
from indexing.embed import get_embedder
from indexing.es_index import get_es_client
from indexing.qdrant_index import get_qdrant_client
from retrieval import bm25_retriever, vector_retriever
from retrieval.reranker import get_reranker
from retrieval.rrf import reciprocal_rank_fusion

router = APIRouter()


def _to_chunk_result(doc: dict) -> ChunkResult:
    return ChunkResult(
        chunk_id=doc.get("chunk_id", ""),
        doc_id=doc.get("doc_id", ""),
        text=doc.get("text", ""),
        circular_number=doc.get("circular_number"),
        title=doc.get("title", ""),
        section_heading=doc.get("section_heading"),
        source=doc.get("source", ""),
        date_issued=doc.get("date_issued"),
        url=doc.get("url", ""),
        bm25_rank=doc.get("bm25_rank"),
        vector_rank=doc.get("vector_rank"),
        rrf_score=doc.get("rrf_score", 0.0),
        rerank_score=doc.get("rerank_score"),
    )


@router.post("/query", response_model=QueryResponse)
async def query_regulations(req: QueryRequest):
    latency = {}
    total_start = time.perf_counter()

    bm25_results = []
    vec_results = []

    if req.mode == "hybrid":
        t0 = time.perf_counter()
        bm25_results = bm25_retriever.search(
            get_es_client(), req.query, top_k=settings.bm25_top_k, filters=req.filters
        )
        latency["bm25"] = int((time.perf_counter() - t0) * 1000)

        t0 = time.perf_counter()
        vec_results = vector_retriever.search(
            get_qdrant_client(), get_embedder(), req.query,
            top_k=settings.vector_top_k, filters=req.filters,
        )
        latency["vector"] = int((time.perf_counter() - t0) * 1000)
    elif req.mode == "sparse":
        t0 = time.perf_counter()
        bm25_results = bm25_retriever.search(
            get_es_client(), req.query, top_k=settings.bm25_top_k, filters=req.filters
        )
        latency["bm25"] = int((time.perf_counter() - t0) * 1000)
    else:
        t0 = time.perf_counter()
        vec_results = vector_retriever.search(
            get_qdrant_client(), get_embedder(), req.query,
            top_k=settings.vector_top_k, filters=req.filters,
        )
        latency["vector"] = int((time.perf_counter() - t0) * 1000)

    if req.mode == "hybrid":
        fused = reciprocal_rank_fusion(bm25_results, vec_results, k=settings.rrf_k, top_k=20)
    elif req.mode == "sparse":
        fused = bm25_results[:20]
        for doc in fused:
            doc["rrf_score"] = doc.get("bm25_score", 0.0)
    else:
        fused = vec_results[:20]
        for doc in fused:
            doc["rrf_score"] = doc.get("vector_score", 0.0)

    t0 = time.perf_counter()
    reranker = get_reranker()
    reranked = reranker.rerank(req.query, fused, top_k=settings.rerank_top_k)
    latency["rerank"] = int((time.perf_counter() - t0) * 1000)

    top_chunks = reranked[: settings.llm_context_chunks]

    t0 = time.perf_counter()
    answer = generate_answer(req.query, top_chunks)
    latency["llm"] = int((time.perf_counter() - t0) * 1000)

    latency["total"] = int((time.perf_counter() - total_start) * 1000)

    return QueryResponse(
        query=req.query,
        mode=req.mode,
        answer=answer,
        chunks_used=[_to_chunk_result(c) for c in top_chunks],
        all_retrieved=[_to_chunk_result(c) for c in fused],
        latency_ms=latency,
    )
