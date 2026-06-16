import json
from pathlib import Path

from loguru import logger
from scrapy.exceptions import DropItem

from indexing.db import doc_exists, insert_document


class DeduplicatePipeline:
    def process_item(self, item, spider):
        if doc_exists(item["doc_id"]):
            raise DropItem(f"Duplicate document: {item['doc_id']}")
        return item


class SaveMetaPipeline:
    def process_item(self, item, spider):
        meta = {
            "doc_id": item["doc_id"],
            "source": item["source"],
            "circular_number": item.get("circular_number"),
            "title": item["title"],
            "date_issued": item.get("date_issued"),
            "addressee": item.get("addressee"),
            "category": item.get("category"),
            "url": item["url"],
            "local_pdf_path": item.get("local_pdf_path"),
            "page_count": item.get("page_count", 0),
            "file_size_bytes": item.get("file_size_bytes", 0),
            "scraped_at": item.get("scraped_at"),
        }

        insert_document(meta)

        pdf_path = Path(item.get("local_pdf_path", ""))
        if pdf_path.exists():
            sidecar = pdf_path.with_suffix(".meta.json")
            with open(sidecar, "w") as f:
                json.dump(meta, f, indent=2, default=str)

        logger.info(f"Saved metadata for: {item.get('circular_number') or item['title']}")
        return item
