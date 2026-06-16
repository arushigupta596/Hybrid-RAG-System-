import re

import fitz
from loguru import logger

HEADER_FOOTER_RE = re.compile(r'^(Page \d+|SEBI|Securities and Exchange Board)', re.IGNORECASE)


def parse_pdf(pdf_path: str) -> list[dict]:
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        logger.error(f"Failed to open PDF {pdf_path}: {e}")
        return []

    pages = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()

        if len(text.strip()) < 50:
            logger.warning(f"Scanned/empty page detected: {pdf_path} page {page_num + 1}, skipping")
            continue

        lines = text.split("\n")
        filtered_lines = [
            line for line in lines
            if not HEADER_FOOTER_RE.match(line.strip())
        ]
        cleaned_text = "\n".join(filtered_lines).strip()

        blocks = page.get_text("dict").get("blocks", [])
        font_sizes = []
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        font_sizes.append(span["size"])

        has_table = bool(page.find_tables())

        pages.append({
            "page_num": page_num + 1,
            "text": cleaned_text,
            "font_sizes": font_sizes,
            "has_table": has_table,
            "blocks": blocks,
        })

    doc.close()
    return pages
