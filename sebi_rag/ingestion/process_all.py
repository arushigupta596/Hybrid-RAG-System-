import argparse
import json
from pathlib import Path

from loguru import logger

from api.config import settings
from indexing.db import init_db, insert_chunk, update_document_chunk_count
from ingestion.chunker import chunk_document, save_chunks
from ingestion.html_parser import parse_html_file
from ingestion.pdf_parser import parse_pdf


def process_source(source_dir: Path, source_name: str):
    if not source_dir.exists():
        logger.warning(f"Source directory not found: {source_dir}")
        return 0

    total_chunks = 0
    pdf_files = list(source_dir.glob("*.pdf"))
    logger.info(f"Processing {len(pdf_files)} PDFs from {source_name}")

    for pdf_path in pdf_files:
        meta_path = pdf_path.with_suffix(".meta.json")
        if not meta_path.exists():
            logger.warning(f"No metadata sidecar for {pdf_path}, skipping")
            continue

        with open(meta_path) as f:
            meta = json.load(f)

        pages = parse_pdf(str(pdf_path))
        if not pages:
            pages = parse_html_file(str(pdf_path))
        if not pages:
            logger.warning(f"No extractable content from {pdf_path}")
            continue

        chunks = chunk_document(pages, meta)
        if not chunks:
            logger.warning(f"No chunks produced from {pdf_path}")
            continue

        for chunk in chunks:
            insert_chunk({
                "chunk_id": chunk["chunk_id"],
                "doc_id": chunk["doc_id"],
                "chunk_index": chunk["chunk_index"],
                "section_heading": chunk.get("section_heading"),
                "page_start": chunk.get("page_start"),
                "page_end": chunk.get("page_end"),
                "token_count": len(chunk["text"].split()),
                "char_count": len(chunk["text"]),
            })

        save_chunks(chunks)
        update_document_chunk_count(meta["doc_id"], len(chunks))
        total_chunks += len(chunks)
        logger.info(f"  {pdf_path.name}: {len(chunks)} chunks")

    return total_chunks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="all", choices=["all", "sebi_circulars", "sebi_regulations", "rbi_circulars"])
    args = parser.parse_args()

    init_db()

    raw_dir = Path(settings.raw_data_dir).resolve()
    sources = {
        "sebi_circulars": ("sebi_circulars", "sebi_circular"),
        "sebi_regulations": ("sebi_regulations", "sebi_regulation"),
        "rbi_circulars": ("rbi_circulars", "rbi_circular"),
    }

    total = 0
    if args.source == "all":
        for dir_name, source_name in sources.values():
            total += process_source(raw_dir / dir_name, source_name)
    else:
        dir_name, source_name = sources[args.source]
        total += process_source(raw_dir / dir_name, source_name)

    logger.info(f"Total chunks processed: {total}")


if __name__ == "__main__":
    main()
