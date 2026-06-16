from fastapi import APIRouter

from api.models import HealthResponse
from indexing.db import check_postgres
from indexing.es_index import check_elasticsearch
from indexing.qdrant_index import check_qdrant

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    es_ok = check_elasticsearch()
    qdrant_ok = check_qdrant()
    pg_ok = check_postgres()

    all_ok = es_ok and qdrant_ok and pg_ok
    return HealthResponse(
        status="healthy" if all_ok else "degraded",
        elasticsearch=es_ok,
        qdrant=qdrant_ok,
        postgres=pg_ok,
    )
