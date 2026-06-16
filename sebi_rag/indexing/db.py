from loguru import logger
from sqlalchemy import create_engine, text

from api.config import settings

_engine = None


def get_engine():
    global _engine
    if _engine is None:
        url = (
            f"postgresql://{settings.postgres_user}:{settings.postgres_password}"
            f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"
        )
        _engine = create_engine(url, pool_pre_ping=True)
    return _engine


DDL = """
CREATE TABLE IF NOT EXISTS documents (
    doc_id TEXT PRIMARY KEY, source TEXT NOT NULL,
    circular_number TEXT, title TEXT NOT NULL,
    date_issued DATE, addressee TEXT, category TEXT,
    url TEXT NOT NULL, local_pdf_path TEXT,
    page_count INT, file_size_bytes BIGINT,
    scraped_at TIMESTAMPTZ, chunk_count INT DEFAULT 0,
    indexed_es BOOLEAN DEFAULT FALSE, indexed_qdrant BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS chunks (
    chunk_id TEXT PRIMARY KEY, doc_id TEXT REFERENCES documents(doc_id),
    chunk_index INT NOT NULL, section_heading TEXT,
    page_start INT, page_end INT, token_count INT, char_count INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_documents_source   ON documents(source);
CREATE INDEX IF NOT EXISTS idx_documents_date     ON documents(date_issued);
CREATE INDEX IF NOT EXISTS idx_documents_circular ON documents(circular_number);
CREATE INDEX IF NOT EXISTS idx_chunks_doc         ON chunks(doc_id);
"""


def init_db():
    engine = get_engine()
    with engine.begin() as conn:
        for statement in DDL.strip().split(";"):
            statement = statement.strip()
            if statement:
                conn.execute(text(statement))
    logger.info("Database tables created/verified")


def doc_exists(doc_id: str) -> bool:
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT 1 FROM documents WHERE doc_id = :doc_id"),
            {"doc_id": doc_id},
        )
        return result.fetchone() is not None


def insert_document(meta: dict):
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO documents (doc_id, source, circular_number, title, date_issued,
                    addressee, category, url, local_pdf_path, page_count, file_size_bytes, scraped_at)
                VALUES (:doc_id, :source, :circular_number, :title, :date_issued,
                    :addressee, :category, :url, :local_pdf_path, :page_count, :file_size_bytes, :scraped_at)
                ON CONFLICT (doc_id) DO NOTHING
            """),
            meta,
        )


def insert_chunk(chunk: dict):
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO chunks (chunk_id, doc_id, chunk_index, section_heading,
                    page_start, page_end, token_count, char_count)
                VALUES (:chunk_id, :doc_id, :chunk_index, :section_heading,
                    :page_start, :page_end, :token_count, :char_count)
                ON CONFLICT (chunk_id) DO NOTHING
            """),
            chunk,
        )


def update_document_chunk_count(doc_id: str, count: int):
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE documents SET chunk_count = :count WHERE doc_id = :doc_id"),
            {"doc_id": doc_id, "count": count},
        )


def update_index_status(doc_id: str, es: bool = False, qdrant: bool = False):
    engine = get_engine()
    with engine.begin() as conn:
        if es:
            conn.execute(
                text("UPDATE documents SET indexed_es = TRUE WHERE doc_id = :doc_id"),
                {"doc_id": doc_id},
            )
        if qdrant:
            conn.execute(
                text("UPDATE documents SET indexed_qdrant = TRUE WHERE doc_id = :doc_id"),
                {"doc_id": doc_id},
            )


def check_postgres() -> bool:
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


if __name__ == "__main__":
    init_db()
