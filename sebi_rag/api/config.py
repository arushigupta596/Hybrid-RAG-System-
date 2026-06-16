from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # OpenRouter
    openrouter_api_key: str = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    llm_model: str = "anthropic/claude-sonnet-4-6"
    app_site_url: str = "http://localhost:5173"
    app_title: str = "SEBI RBI Regulatory Intelligence"
    # Cohere (optional)
    cohere_api_key: str = ""
    # Elasticsearch
    es_host: str = "http://localhost:9200"
    es_index_name: str = "sebi_rbi_chunks"
    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection: str = "sebi_rbi_vectors"
    # PostgreSQL
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "sebi_rag"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    # Embeddings
    embedding_model: str = "BAAI/bge-large-en-v1.5"
    embedding_dim: int = 1024
    embedding_batch_size: int = 32
    # Retrieval
    bm25_top_k: int = 20
    vector_top_k: int = 20
    rrf_k: int = 60
    rerank_top_k: int = 5
    llm_context_chunks: int = 5
    # Paths
    raw_data_dir: str = "data/raw"
    processed_data_dir: str = "data/processed"
    cutoff_date: str = "2015-01-01"

    class Config:
        env_file = ".env"


settings = Settings()
