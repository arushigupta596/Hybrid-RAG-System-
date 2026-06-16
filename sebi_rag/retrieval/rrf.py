def reciprocal_rank_fusion(
    bm25_results: list[dict],
    vector_results: list[dict],
    k: int = 60,
    top_k: int = 20,
) -> list[dict]:
    scores: dict[str, float] = {}
    docs: dict[str, dict] = {}

    for result in bm25_results:
        chunk_id = result["chunk_id"]
        rank = result.get("bm25_rank", len(bm25_results))
        scores[chunk_id] = scores.get(chunk_id, 0) + 1.0 / (k + rank)
        if chunk_id not in docs:
            docs[chunk_id] = {**result}
            docs[chunk_id].pop("bm25_score", None)

    for result in vector_results:
        chunk_id = result["chunk_id"]
        rank = result.get("vector_rank", len(vector_results))
        scores[chunk_id] = scores.get(chunk_id, 0) + 1.0 / (k + rank)
        if chunk_id not in docs:
            docs[chunk_id] = {**result}
            docs[chunk_id].pop("vector_score", None)
        else:
            if "vector_rank" in result:
                docs[chunk_id]["vector_rank"] = result["vector_rank"]

    bm25_ids = {r["chunk_id"] for r in bm25_results}
    vector_ids = {r["chunk_id"] for r in vector_results}

    merged = []
    for chunk_id, score in scores.items():
        doc = docs[chunk_id]
        doc["rrf_score"] = score
        if chunk_id not in bm25_ids:
            doc["bm25_rank"] = None
        if chunk_id not in vector_ids:
            doc["vector_rank"] = None
        merged.append(doc)

    merged.sort(key=lambda x: x["rrf_score"], reverse=True)
    return merged[:top_k]
