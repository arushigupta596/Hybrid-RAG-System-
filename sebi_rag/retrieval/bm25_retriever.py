from elasticsearch import Elasticsearch
from loguru import logger

from api.config import settings


def search(
    es_client: Elasticsearch,
    query: str,
    top_k: int = 20,
    filters: dict | None = None,
) -> list[dict]:
    must_clauses = [
        {
            "multi_match": {
                "query": query,
                "fields": [
                    "circular_number^3",
                    "title^2",
                    "section_heading^1.5",
                    "text",
                ],
                "type": "best_fields",
            }
        }
    ]

    filter_clauses = []
    if filters:
        if filters.get("source"):
            sources = filters["source"] if isinstance(filters["source"], list) else [filters["source"]]
            filter_clauses.append({"terms": {"source": sources}})
        if filters.get("category"):
            categories = filters["category"] if isinstance(filters["category"], list) else [filters["category"]]
            filter_clauses.append({"terms": {"category": categories}})
        if filters.get("date_from") or filters.get("date_to"):
            date_range = {}
            if filters.get("date_from"):
                date_range["gte"] = filters["date_from"]
            if filters.get("date_to"):
                date_range["lte"] = filters["date_to"]
            filter_clauses.append({"range": {"date_issued": date_range}})

    body = {
        "query": {
            "bool": {
                "must": must_clauses,
                "filter": filter_clauses,
            }
        },
        "size": top_k,
    }

    try:
        response = es_client.search(index=settings.es_index_name, body=body)
    except Exception as e:
        logger.error(f"BM25 search error: {e}")
        return []

    results = []
    for rank, hit in enumerate(response["hits"]["hits"], start=1):
        doc = hit["_source"]
        doc["bm25_rank"] = rank
        doc["bm25_score"] = hit["_score"]
        results.append(doc)

    return results
