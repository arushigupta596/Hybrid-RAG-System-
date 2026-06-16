import hashlib
import json
import re
from pathlib import Path

from loguru import logger

from api.config import settings

SEBI_HEADING_PATTERNS = [
    re.compile(r'^\d+\.\s+[A-Z]'),
    re.compile(r'^\d+\.\d+\s+[A-Z]'),
    re.compile(r'^[A-Z][A-Z\s]{4,}:?\s*$'),
    re.compile(r'^Para\s+\d+', re.IGNORECASE),
    re.compile(r'^Schedule\s+[IVX\d]', re.IGNORECASE),
    re.compile(r'^Annexure\s+[A-Z\d]', re.IGNORECASE),
    re.compile(r'^CHAPTER\s+[IVX\d]', re.IGNORECASE),
]

RBI_HEADING_PATTERNS = [
    re.compile(r'^[A-Z]\.\s+[A-Z]'),
    re.compile(r'^\d+\.\s+[A-Z]'),
    re.compile(r'^Part\s+[IVX\d]', re.IGNORECASE),
    re.compile(r'^Annex(ure)?\s+[A-Z\d]', re.IGNORECASE),
]

MAX_CHUNK_TOKENS = 1500
MIN_CHUNK_TOKENS = 200
MAX_CHUNK_CHARS = 7000
MIN_CHUNK_CHARS = 100


def _estimate_tokens(text: str) -> int:
    return len(text.split())


def _is_heading(line: str, source: str) -> bool:
    patterns = SEBI_HEADING_PATTERNS if "sebi" in source.lower() else RBI_HEADING_PATTERNS
    stripped = line.strip()
    if not stripped:
        return False
    for pattern in patterns:
        if pattern.match(stripped):
            return True
    return False


def _split_on_headings(text: str, source: str) -> list[tuple[str | None, str]]:
    lines = text.split("\n")
    sections: list[tuple[str | None, str]] = []
    current_heading = None
    current_lines: list[str] = []

    for line in lines:
        if _is_heading(line, source):
            if current_lines:
                sections.append((current_heading, "\n".join(current_lines).strip()))
            current_heading = line.strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_heading, "\n".join(current_lines).strip()))

    return sections


def _split_large_chunk(text: str) -> list[str]:
    paragraphs = text.split("\n\n")
    sub_chunks = []
    current = []
    current_tokens = 0

    for para in paragraphs:
        para_tokens = _estimate_tokens(para)
        if current_tokens + para_tokens > MAX_CHUNK_TOKENS and current:
            sub_chunks.append("\n\n".join(current))
            current = [para]
            current_tokens = para_tokens
        else:
            current.append(para)
            current_tokens += para_tokens

    if current:
        sub_chunks.append("\n\n".join(current))

    return [c for c in sub_chunks if _estimate_tokens(c) >= MIN_CHUNK_TOKENS]


def chunk_document(pages: list[dict], meta: dict) -> list[dict]:
    full_text = "\n\n".join(p["text"] for p in pages if p.get("text"))
    if not full_text.strip():
        return []

    source = meta.get("source", "")
    sections = _split_on_headings(full_text, source)

    raw_chunks = []
    for heading, text in sections:
        tokens = _estimate_tokens(text)
        if tokens > MAX_CHUNK_TOKENS:
            sub_chunks = _split_large_chunk(text)
            for i, sc in enumerate(sub_chunks):
                raw_chunks.append((heading if i == 0 else None, sc))
        else:
            raw_chunks.append((heading, text))

    merged_chunks = []
    for heading, text in raw_chunks:
        if _estimate_tokens(text) < MIN_CHUNK_TOKENS and merged_chunks:
            prev_heading, prev_text = merged_chunks[-1]
            merged_chunks[-1] = (prev_heading, prev_text + "\n\n" + text)
        else:
            merged_chunks.append((heading, text))

    page_map = {}
    for p in pages:
        page_map[p["page_num"]] = p["text"]

    doc_id = meta["doc_id"]
    identifier = meta.get("circular_number") or meta.get("title", "")
    date_str = str(meta.get("date_issued", "")) if meta.get("date_issued") else None

    chunks = []
    for idx, (heading, text) in enumerate(merged_chunks):
        if idx == 0:
            text = f"[{identifier} | {date_str or 'N/A'}]\n\n{text}"

        chunk_id = hashlib.sha256(f"{doc_id}:{idx}".encode()).hexdigest()

        page_start = 1
        page_end = len(pages) if pages else 1
        for p in pages:
            if text[:100] in p.get("text", ""):
                page_start = p["page_num"]
                break
        for p in reversed(pages):
            if text[-100:] in p.get("text", ""):
                page_end = p["page_num"]
                break

        chunk = {
            "chunk_id": chunk_id,
            "doc_id": doc_id,
            "chunk_index": idx,
            "text": text,
            "section_heading": heading,
            "page_start": page_start,
            "page_end": page_end,
            "source": meta.get("source", ""),
            "circular_number": meta.get("circular_number"),
            "title": meta.get("title", ""),
            "date_issued": date_str,
            "addressee": meta.get("addressee"),
            "category": meta.get("category"),
            "url": meta.get("url", ""),
        }
        chunks.append(chunk)

    return chunks


def save_chunks(chunks: list[dict]):
    chunks_dir = Path(settings.processed_data_dir).resolve() / "chunks"
    chunks_dir.mkdir(parents=True, exist_ok=True)

    for chunk in chunks:
        out_path = chunks_dir / f"{chunk['chunk_id']}.json"
        with open(out_path, "w") as f:
            json.dump(chunk, f, indent=2, default=str)

    logger.info(f"Saved {len(chunks)} chunks to {chunks_dir}")
