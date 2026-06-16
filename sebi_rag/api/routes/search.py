import time

from fastapi import APIRouter

from api.config import settings
from api.models import ChunkResult, QueryRequest, SearchResponse
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


@router.post("/search", response_model=SearchResponse)
async def search_regulations(req: QueryRequest):
    latency = {}
    results = []

    if req.mode in ("sparse", "hybrid"):
        t0 = time.perf_counter()
        bm25_results = bm25_retriever.search(
            get_es_client(), req.query, top_k=settings.bm25_top_k, filters=req.filters
        )
        latency["bm25"] = int((time.perf_counter() - t0) * 1000)
    else:
        bm25_results = []

    if req.mode in ("dense", "hybrid"):
        t0 = time.perf_counter()
        vec_results = vector_retriever.search(
            get_qdrant_client(), get_embedder(), req.query,
            top_k=settings.vector_top_k, filters=req.filters,
        )
        latency["vector"] = int((time.perf_counter() - t0) * 1000)
    else:
        vec_results = []

    if req.mode == "hybrid":
        fused = reciprocal_rank_fusion(bm25_results, vec_results, k=settings.rrf_k, top_k=20)
        t0 = time.perf_counter()
        reranker = get_reranker()
        results = reranker.rerank(req.query, fused, top_k=req.top_k)
        latency["rerank"] = int((time.perf_counter() - t0) * 1000)
    elif req.mode == "sparse":
        for doc in bm25_results:
            doc["rrf_score"] = doc.get("bm25_score", 0.0)
        results = bm25_results[: req.top_k]
    else:
        for doc in vec_results:
            doc["rrf_score"] = doc.get("vector_score", 0.0)
        results = vec_results[: req.top_k]

    latency["total"] = sum(latency.values())

    return SearchResponse(
        query=req.query,
        mode=req.mode,
        results=[_to_chunk_result(r) for r in results],
        latency_ms=latency,
    )
