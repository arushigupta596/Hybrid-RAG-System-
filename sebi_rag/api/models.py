from typing import Literal, Optional

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=500)
    mode: Literal["sparse", "dense", "hybrid"] = "hybrid"
    top_k: int = Field(default=5, ge=1, le=20)
    filters: Optional[dict] = None


class ChunkResult(BaseModel):
    chunk_id: str
    doc_id: str
    text: str
    circular_number: Optional[str] = None
    title: str
    section_heading: Optional[str] = None
    source: str
    date_issued: Optional[str] = None
    url: str
    bm25_rank: Optional[int] = None
    vector_rank: Optional[int] = None
    rrf_score: float
    rerank_score: Optional[float] = None


class QueryResponse(BaseModel):
    query: str
    mode: str
    answer: str
    chunks_used: list[ChunkResult]
    all_retrieved: list[ChunkResult]
    latency_ms: dict


class SearchResponse(BaseModel):
    query: str
    mode: str
    results: list[ChunkResult]
    latency_ms: dict


class HealthResponse(BaseModel):
    status: str
    elasticsearch: bool
    qdrant: bool
    postgres: bool
    version: str = "1.0.0"
