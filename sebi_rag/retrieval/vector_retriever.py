from loguru import logger
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchAny, MatchValue, Range

from api.config import settings
from indexing.embed import BGEEmbedder


def search(
    qdrant_client: QdrantClient,
    embedder: BGEEmbedder,
    query: str,
    top_k: int = 20,
    filters: dict | None = None,
) -> list[dict]:
    query_vector = embedder.embed_query(query)

    qdrant_filter = None
    if filters:
        conditions = []
        if filters.get("source"):
            sources = filters["source"] if isinstance(filters["source"], list) else [filters["source"]]
            conditions.append(FieldCondition(key="source", match=MatchAny(any=sources)))
        if filters.get("category"):
            categories = filters["category"] if isinstance(filters["category"], list) else [filters["category"]]
            conditions.append(FieldCondition(key="category", match=MatchAny(any=categories)))
        if filters.get("date_from") or filters.get("date_to"):
            range_params = {}
            if filters.get("date_from"):
                range_params["gte"] = filters["date_from"]
            if filters.get("date_to"):
                range_params["lte"] = filters["date_to"]
            conditions.append(FieldCondition(key="date_issued", match=Range(**range_params)))
        if conditions:
            qdrant_filter = Filter(must=conditions)

    try:
        results = qdrant_client.search(
            collection_name=settings.qdrant_collection,
            query_vector=query_vector.tolist(),
            limit=top_k,
            query_filter=qdrant_filter,
            with_payload=True,
        )
    except Exception as e:
        logger.error(f"Vector search error: {e}")
        return []

    output = []
    for rank, scored_point in enumerate(results, start=1):
        doc = scored_point.payload
        doc["vector_rank"] = rank
        doc["vector_score"] = scored_point.score
        output.append(doc)

    return output
