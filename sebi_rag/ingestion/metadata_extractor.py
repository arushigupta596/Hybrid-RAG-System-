import hashlib
import re
from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class DocumentMeta:
    doc_id: str
    source: str
    circular_number: Optional[str]
    title: str
    date_issued: Optional[date]
    addressee: Optional[str]
    category: Optional[str]
    url: str
    local_pdf_path: str
    page_count: int
    file_size_bytes: int
    scraped_at: str
    chunk_ids: list[str] = field(default_factory=list)


CIRCULAR_NUM_RE = re.compile(
    r'(SEBI|CIR)[\s/][A-Z]+[\s/][A-Z0-9]+[\s/][A-Z0-9]*[\s/][\d]+[\s/][\d]{4}',
    re.IGNORECASE,
)

RBI_REF_RE = re.compile(
    r'RBI/\d{4}-\d{2}/\d+',
    re.IGNORECASE,
)

REGULATION_CATEGORIES = {
    "LODR": "LODR",
    "Listing Obligations": "LODR",
    "ICDR": "ICDR",
    "Issue of Capital": "ICDR",
    "SAST": "SAST",
    "Substantial Acquisition": "SAST",
    "Mutual Fund": "Mutual Funds",
    "Alternative Investment": "AIF",
    "AIF": "AIF",
    "Foreign Portfolio": "FPI",
    "FPI": "FPI",
    "Portfolio Managers": "PMS",
    "PMS": "PMS",
    "Buyback": "Buyback",
    "Insider Trading": "Insider Trading",
    "Depositories": "Depositories",
    "Credit Rating": "Credit Rating",
}


def generate_doc_id(source: str, url: str) -> str:
    return hashlib.sha256(f"{source}:{url}".encode()).hexdigest()


def extract_circular_number(text: str) -> Optional[str]:
    match = CIRCULAR_NUM_RE.search(text)
    if match:
        return match.group(0).strip()
    match = RBI_REF_RE.search(text)
    if match:
        return match.group(0).strip()
    return None


def categorize_regulation(title: str) -> Optional[str]:
    for keyword, category in REGULATION_CATEGORIES.items():
        if keyword.lower() in title.lower():
            return category
    return None


def sanitize_filename(name: str) -> str:
    return re.sub(r'[/\\:*?"<>|]', '_', name).strip()
