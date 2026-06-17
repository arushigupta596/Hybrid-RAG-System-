import asyncio
import concurrent.futures
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

_thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=4)


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


def _run_bm25(query: str, filters: dict | None) -> tuple[list[dict], int]:
    t0 = time.perf_counter()
    results = bm25_retriever.search(
        get_es_client(), query, top_k=settings.bm25_top_k, filters=filters
    )
    return results, int((time.perf_counter() - t0) * 1000)


def _run_vector(query: str, filters: dict | None) -> tuple[list[dict], int]:
    t0 = time.perf_counter()
    results = vector_retriever.search(
        get_qdrant_client(), get_embedder(), query,
        top_k=settings.vector_top_k, filters=filters,
    )
    return results, int((time.perf_counter() - t0) * 1000)


@router.post("/query", response_model=QueryResponse)
async def query_regulations(req: QueryRequest):
    latency = {}
    total_start = time.perf_counter()
    loop = asyncio.get_event_loop()

    bm25_results = []
    vec_results = []

    if req.mode == "hybrid":
        bm25_future = loop.run_in_executor(_thread_pool, _run_bm25, req.query, req.filters)
        vec_future = loop.run_in_executor(_thread_pool, _run_vector, req.query, req.filters)
        bm25_results, latency["bm25"] = await bm25_future
        vec_results, latency["vector"] = await vec_future
    elif req.mode == "sparse":
        bm25_results, latency["bm25"] = await loop.run_in_executor(
            _thread_pool, _run_bm25, req.query, req.filters
        )
    else:
        vec_results, latency["vector"] = await loop.run_in_executor(
            _thread_pool, _run_vector, req.query, req.filters
        )

    if req.mode == "hybrid":
        fused = reciprocal_rank_fusion(bm25_results, vec_results, k=settings.rrf_k, top_k=10)
    elif req.mode == "sparse":
        fused = bm25_results[:10]
        for doc in fused:
            doc["rrf_score"] = doc.get("bm25_score", 0.0)
    else:
        fused = vec_results[:10]
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
