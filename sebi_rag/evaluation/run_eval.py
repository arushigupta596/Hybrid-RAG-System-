import argparse
import json
import time
from datetime import datetime
from pathlib import Path

import numpy as np
from loguru import logger

from api.config import settings
from api.llm import generate_answer
from indexing.embed import get_embedder
from indexing.es_index import get_es_client
from indexing.qdrant_index import get_qdrant_client
from retrieval import bm25_retriever, vector_retriever
from retrieval.reranker import get_reranker
from retrieval.rrf import reciprocal_rank_fusion


def ndcg_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int = 10) -> float:
    dcg = 0.0
    for i, doc_id in enumerate(retrieved_ids[:k]):
        if doc_id in relevant_ids:
            dcg += 1.0 / np.log2(i + 2)
    ideal = sum(1.0 / np.log2(i + 2) for i in range(min(len(relevant_ids), k)))
    return dcg / ideal if ideal > 0 else 0.0


def mrr_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int = 10) -> float:
    for i, doc_id in enumerate(retrieved_ids[:k]):
        if doc_id in relevant_ids:
            return 1.0 / (i + 1)
    return 0.0


def precision_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int = 5) -> float:
    hits = sum(1 for doc_id in retrieved_ids[:k] if doc_id in relevant_ids)
    return hits / k


def recall_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int = 5) -> float:
    if not relevant_ids:
        return 0.0
    hits = sum(1 for doc_id in retrieved_ids[:k] if doc_id in relevant_ids)
    return hits / len(relevant_ids)


def run_query_in_mode(query: str, mode: str, filters=None) -> list[dict]:
    es_client = get_es_client()
    qdrant_client = get_qdrant_client()
    embedder = get_embedder()
    reranker = get_reranker()

    bm25_results = []
    vec_results = []

    if mode in ("sparse", "hybrid"):
        bm25_results = bm25_retriever.search(es_client, query, top_k=settings.bm25_top_k, filters=filters)

    if mode in ("dense", "hybrid"):
        vec_results = vector_retriever.search(qdrant_client, embedder, query, top_k=settings.vector_top_k, filters=filters)

    if mode == "hybrid":
        fused = reciprocal_rank_fusion(bm25_results, vec_results, k=settings.rrf_k, top_k=20)
    elif mode == "sparse":
        fused = bm25_results[:20]
        for doc in fused:
            doc["rrf_score"] = doc.get("bm25_score", 0.0)
    else:
        fused = vec_results[:20]
        for doc in fused:
            doc["rrf_score"] = doc.get("vector_score", 0.0)

    reranked = reranker.rerank(query, fused, top_k=10)
    return reranked


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-set", default="data/evaluation/test_queries.json")
    parser.add_argument("--modes", nargs="+", default=["sparse", "dense", "hybrid"])
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    with open(args.test_set) as f:
        test_queries = json.load(f)

    if args.output is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"data/evaluation/results/run_{timestamp}.json"

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)

    results = []
    for tq in test_queries:
        query = tq["query"]
        relevant_ids = set(tq.get("relevant_chunk_ids", []))
        query_result = {
            "query_id": tq["query_id"],
            "query": query,
            "query_type": tq["query_type"],
            "modes": {},
        }

        for mode in args.modes:
            logger.info(f"Running {tq['query_id']} in {mode} mode")
            t0 = time.perf_counter()
            retrieved = run_query_in_mode(query, mode)
            elapsed_ms = int((time.perf_counter() - t0) * 1000)

            retrieved_ids = [r["chunk_id"] for r in retrieved]

            metrics = {
                "ndcg_at_10": ndcg_at_k(retrieved_ids, relevant_ids, 10),
                "mrr_at_10": mrr_at_k(retrieved_ids, relevant_ids, 10),
                "precision_at_5": precision_at_k(retrieved_ids, relevant_ids, 5),
                "recall_at_5": recall_at_k(retrieved_ids, relevant_ids, 5),
                "latency_ms": elapsed_ms,
                "retrieved_count": len(retrieved_ids),
            }
            query_result["modes"][mode] = metrics

        results.append(query_result)

    summary = {}
    for mode in args.modes:
        mode_metrics = [r["modes"][mode] for r in results if mode in r["modes"]]
        summary[mode] = {
            "ndcg_at_10": np.mean([m["ndcg_at_10"] for m in mode_metrics]),
            "mrr_at_10": np.mean([m["mrr_at_10"] for m in mode_metrics]),
            "precision_at_5": np.mean([m["precision_at_5"] for m in mode_metrics]),
            "recall_at_5": np.mean([m["recall_at_5"] for m in mode_metrics]),
            "avg_latency_ms": np.mean([m["latency_ms"] for m in mode_metrics]),
        }

    output = {
        "timestamp": datetime.now().isoformat(),
        "test_set": args.test_set,
        "num_queries": len(test_queries),
        "summary": summary,
        "per_query": results,
    }

    with open(args.output, "w") as f:
        json.dump(output, f, indent=2, default=float)

    logger.info(f"Results saved to {args.output}")
    logger.info("Summary:")
    for mode, metrics in summary.items():
        logger.info(f"  {mode}: NDCG@10={metrics['ndcg_at_10']:.3f}, MRR@10={metrics['mrr_at_10']:.3f}")


if __name__ == "__main__":
    main()
