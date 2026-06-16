import json
from pathlib import Path

from loguru import logger
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    HnswConfigDiff,
    PayloadSchemaType,
    PointStruct,
    VectorParams,
)

from api.config import settings
from indexing.embed import get_embedder

_client: QdrantClient | None = None


def get_qdrant_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
    return _client


def create_collection():
    client = get_qdrant_client()
    collection_name = settings.qdrant_collection

    collections = [c.name for c in client.get_collections().collections]
    if collection_name in collections:
        logger.info(f"Qdrant collection already exists: {collection_name}")
        return

    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
        hnsw_config=HnswConfigDiff(m=16, ef_construct=200),
    )

    for field in ["source", "category", "addressee", "date_issued"]:
        client.create_payload_index(
            collection_name=collection_name,
            field_name=field,
            field_schema=PayloadSchemaType.KEYWORD,
        )

    logger.info(f"Created Qdrant collection: {collection_name}")


def index_chunks(chunks: list[dict], batch_size: int = 32):
    client = get_qdrant_client()
    collection_name = settings.qdrant_collection
    embedder = get_embedder()

    texts = [c["text"] for c in chunks]
    logger.info(f"Embedding {len(texts)} chunks...")
    embeddings = embedder.embed_documents(texts, batch_size=batch_size)

    points = []
    for i, chunk in enumerate(chunks):
        payload = {
            "chunk_id": chunk["chunk_id"],
            "doc_id": chunk["doc_id"],
            "chunk_index": chunk.get("chunk_index"),
            "text": chunk["text"],
            "circular_number": chunk.get("circular_number"),
            "title": chunk.get("title", ""),
            "section_heading": chunk.get("section_heading"),
            "source": chunk.get("source", ""),
            "date_issued": chunk.get("date_issued"),
            "addressee": chunk.get("addressee"),
            "category": chunk.get("category"),
            "url": chunk.get("url", ""),
            "page_start": chunk.get("page_start"),
            "page_end": chunk.get("page_end"),
        }
        points.append(
            PointStruct(
                id=i,
                vector=embeddings[i].tolist(),
                payload=payload,
            )
        )

    for i in range(0, len(points), batch_size):
        batch = points[i : i + batch_size]
        client.upsert(collection_name=collection_name, points=batch)
        logger.info(f"Indexed {len(batch)} points to Qdrant (batch {i // batch_size + 1})")

    logger.info(f"Total points indexed to Qdrant: {len(points)}")


def get_point_count() -> int:
    try:
        client = get_qdrant_client()
        info = client.get_collection(settings.qdrant_collection)
        return info.points_count
    except Exception:
        return 0


def check_qdrant() -> bool:
    try:
        client = get_qdrant_client()
        client.get_collections()
        return True
    except Exception:
        return False


def index_all_chunks():
    chunks_dir = Path(settings.processed_data_dir).resolve() / "chunks"
    if not chunks_dir.exists():
        logger.error(f"Chunks directory not found: {chunks_dir}")
        return

    create_collection()

    chunks = []
    for chunk_file in sorted(chunks_dir.glob("*.json")):
        with open(chunk_file) as f:
            chunks.append(json.load(f))

    if chunks:
        index_chunks(chunks)
    else:
        logger.warning("No chunks found to index")
