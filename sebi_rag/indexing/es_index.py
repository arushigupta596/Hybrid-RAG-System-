import json
from pathlib import Path

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from api.config import settings

_client: Elasticsearch | None = None

INDEX_SETTINGS = {
    "settings": {
        "analysis": {
            "analyzer": {
                "regulatory_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "stop", "regulatory_synonyms"],
                }
            },
            "filter": {
                "regulatory_synonyms": {
                    "type": "synonym",
                    "lenient": True,
                    "synonyms": [
                        "sebi, securities and exchange board of india",
                        "rbi, reserve bank of india",
                        "ipo, initial public offering",
                        "lodr, listing obligations and disclosure requirements",
                        "icdr, issue of capital and disclosure requirements",
                        "sast, substantial acquisition of shares and takeovers",
                        "fpi, foreign portfolio investor",
                        "aif, alternative investment fund",
                        "nse, national stock exchange",
                        "bse, bombay stock exchange",
                    ],
                }
            },
        },
        "number_of_shards": 1,
        "number_of_replicas": 0,
    },
    "mappings": {
        "properties": {
            "chunk_id": {"type": "keyword"},
            "doc_id": {"type": "keyword"},
            "circular_number": {"type": "keyword"},
            "title": {"type": "text", "analyzer": "regulatory_analyzer"},
            "section_heading": {"type": "text", "analyzer": "regulatory_analyzer"},
            "text": {"type": "text", "analyzer": "regulatory_analyzer"},
            "source": {"type": "keyword"},
            "date_issued": {"type": "date", "format": "yyyy-MM-dd"},
            "addressee": {"type": "keyword"},
            "category": {"type": "keyword"},
            "url": {"type": "keyword"},
            "page_start": {"type": "integer"},
            "chunk_index": {"type": "integer"},
        }
    },
}


def get_es_client() -> Elasticsearch:
    global _client
    if _client is None:
        _client = Elasticsearch(settings.es_host)
    return _client


def create_index():
    client = get_es_client()
    index_name = settings.es_index_name
    if not client.indices.exists(index=index_name):
        client.indices.create(
            index=index_name,
            settings=INDEX_SETTINGS["settings"],
            mappings=INDEX_SETTINGS["mappings"],
        )
        logger.info(f"Created ES index: {index_name}")
    else:
        logger.info(f"ES index already exists: {index_name}")


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def bulk_index_chunks(chunks: list[dict], batch_size: int = 100):
    client = get_es_client()
    index_name = settings.es_index_name

    actions = []
    for chunk in chunks:
        doc = {
            "_index": index_name,
            "_id": chunk["chunk_id"],
            "_source": {
                "chunk_id": chunk["chunk_id"],
                "doc_id": chunk["doc_id"],
                "circular_number": chunk.get("circular_number"),
                "title": chunk.get("title", ""),
                "section_heading": chunk.get("section_heading"),
                "text": chunk["text"],
                "source": chunk.get("source", ""),
                "date_issued": chunk.get("date_issued"),
                "addressee": chunk.get("addressee"),
                "category": chunk.get("category"),
                "url": chunk.get("url", ""),
                "page_start": chunk.get("page_start"),
                "chunk_index": chunk.get("chunk_index"),
            },
        }
        actions.append(doc)

    for i in range(0, len(actions), batch_size):
        batch = actions[i : i + batch_size]
        success, errors = bulk(client, batch, raise_on_error=False)
        if errors:
            logger.warning(f"ES bulk indexing errors: {errors}")
        logger.info(f"Indexed {success} chunks to ES (batch {i // batch_size + 1})")


def get_doc_count() -> int:
    client = get_es_client()
    try:
        result = client.count(index=settings.es_index_name)
        return result["count"]
    except Exception:
        return 0


def check_elasticsearch() -> bool:
    try:
        client = get_es_client()
        return client.ping()
    except Exception:
        return False


def index_all_chunks():
    chunks_dir = Path(settings.processed_data_dir).resolve() / "chunks"
    if not chunks_dir.exists():
        logger.error(f"Chunks directory not found: {chunks_dir}")
        return

    create_index()

    chunks = []
    for chunk_file in sorted(chunks_dir.glob("*.json")):
        with open(chunk_file) as f:
            chunks.append(json.load(f))

    if chunks:
        bulk_index_chunks(chunks)
        logger.info(f"Total chunks indexed to ES: {len(chunks)}")
    else:
        logger.warning("No chunks found to index")
