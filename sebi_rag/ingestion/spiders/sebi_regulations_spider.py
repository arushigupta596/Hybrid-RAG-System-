import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

import scrapy
from loguru import logger

from api.config import settings
from ingestion.metadata_extractor import (
    categorize_regulation,
    generate_doc_id,
    sanitize_filename,
)

AJAX_URL = "https://www.sebi.gov.in/sebiweb/ajax/home/getnewslistallinfo.jsp"


class SebiRegulationsSpider(scrapy.Spider):
    name = "sebi_regulations"
    custom_settings = {
        "DOWNLOAD_DELAY": 1.0,
        "CONCURRENT_REQUESTS": 2,
    }

    start_urls = [
        "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListingAll=yes"
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.output_dir = Path(settings.raw_data_dir) / "sebi_regulations"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.page_num = 0
        self.items_scraped = 0

    def parse(self, response):
        rows = response.css("table#sample_1 tbody tr")
        if not rows:
            rows = response.css("table.table-striped tbody tr")
        if not rows:
            rows = response.css("table.table tbody tr")

        found_any = False
        for row in rows:
            cells = row.css("td")
            if len(cells) < 3:
                continue

            doc_type = cells[1].css("::text").get("").strip().lower()
            if "regulation" not in doc_type:
                continue

            found_any = True
            date_text = cells[0].css("::text").get("").strip()
            issued_date = self._parse_date(date_text)

            title = cells[2].css("a::text").get("").strip()
            if not title:
                title = " ".join(cells[2].css("*::text").getall()).strip()
            link = cells[2].css("a::attr(href)").get()
            if not link or not title:
                continue

            detail_url = urljoin(response.url, link)
            doc_id = generate_doc_id("sebi_regulation", detail_url)
            category = categorize_regulation(title)

            yield scrapy.Request(
                url=detail_url,
                callback=self.parse_detail,
                meta={
                    "doc_id": doc_id,
                    "source": "sebi_regulation",
                    "circular_number": None,
                    "title": title,
                    "date_issued": str(issued_date) if issued_date else None,
                    "category": category,
                    "detail_url": detail_url,
                },
            )

        self.page_num += 1
        if self.page_num < 200:
            yield scrapy.FormRequest(
                url=AJAX_URL,
                formdata={
                    "nextValue": str(self.page_num),
                    "next": "next",
                    "search": "",
                    "fromDate": "",
                    "toDate": "",
                    "deptId": "",
                    "sid": "0",
                    "ssid": "0",
                    "smid": "0",
                    "cid": "0",
                },
                callback=self.parse_ajax,
            )

    def parse_ajax(self, response):
        try:
            data = json.loads(response.text)
        except json.JSONDecodeError:
            return

        if not isinstance(data, list) or not data:
            return

        for item in data:
            doc_type = (item.get("type", "") or item.get("category", "")).lower()
            if "regulation" not in doc_type:
                continue

            title = item.get("title", "").strip()
            link = item.get("link", "") or item.get("url", "")
            if not link or not title:
                continue

            date_str = item.get("formattedDate", "") or item.get("date", "")
            issued_date = self._parse_date(date_str)

            detail_url = urljoin(response.url, link)
            doc_id = generate_doc_id("sebi_regulation", detail_url)
            category = categorize_regulation(title)

            yield scrapy.Request(
                url=detail_url,
                callback=self.parse_detail,
                meta={
                    "doc_id": doc_id,
                    "source": "sebi_regulation",
                    "circular_number": None,
                    "title": title,
                    "date_issued": str(issued_date) if issued_date else None,
                    "category": category,
                    "detail_url": detail_url,
                },
            )

        self.page_num += 1
        if self.page_num < 200:
            yield scrapy.FormRequest(
                url=AJAX_URL,
                formdata={
                    "nextValue": str(self.page_num),
                    "next": "next",
                    "search": "",
                    "fromDate": "",
                    "toDate": "",
                    "deptId": "",
                    "sid": "0",
                    "ssid": "0",
                    "smid": "0",
                    "cid": "0",
                },
                callback=self.parse_ajax,
            )

    def parse_detail(self, response):
        meta = response.meta
        pdf_links = response.css("a[href$='.pdf']::attr(href)").getall()
        if not pdf_links:
            pdf_links = response.xpath("//a[contains(@href, '.pdf')]/@href").getall()

        if not pdf_links:
            self.items_scraped += 1
            yield {
                "doc_id": meta["doc_id"],
                "source": meta["source"],
                "circular_number": None,
                "title": meta["title"],
                "date_issued": meta.get("date_issued"),
                "category": meta.get("category"),
                "url": meta["detail_url"],
                "local_pdf_path": "",
                "page_count": 0,
                "file_size_bytes": 0,
                "scraped_at": datetime.utcnow().isoformat(),
            }
            return

        pdf_url = urljoin(response.url, pdf_links[0])
        filename = sanitize_filename(meta["title"][:80]) + ".pdf"
        local_path = str(self.output_dir / filename)

        yield scrapy.Request(
            url=pdf_url,
            callback=self.save_pdf,
            meta={
                **meta,
                "url": pdf_url,
                "local_pdf_path": local_path,
            },
        )

    def save_pdf(self, response):
        meta = response.meta
        local_path = meta["local_pdf_path"]
        Path(local_path).parent.mkdir(parents=True, exist_ok=True)

        with open(local_path, "wb") as f:
            f.write(response.body)

        file_size = len(response.body)
        import fitz
        try:
            doc = fitz.open(local_path)
            page_count = len(doc)
            doc.close()
        except Exception:
            page_count = 0

        self.items_scraped += 1
        yield {
            "doc_id": meta["doc_id"],
            "source": meta["source"],
            "circular_number": None,
            "title": meta["title"],
            "date_issued": meta.get("date_issued"),
            "category": meta.get("category"),
            "url": meta["url"],
            "local_pdf_path": local_path,
            "page_count": page_count,
            "file_size_bytes": file_size,
            "scraped_at": datetime.utcnow().isoformat(),
        }

    def _parse_date(self, text: str):
        if not text:
            return None
        text = text.strip().rstrip(".")
        for fmt in ("%b %d, %Y", "%d-%b-%Y", "%d %b %Y", "%d/%m/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                continue
        return None
