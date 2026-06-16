import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

import scrapy
from loguru import logger

from api.config import settings
from ingestion.metadata_extractor import (
    extract_circular_number,
    generate_doc_id,
    sanitize_filename,
)

AJAX_URL = "https://www.sebi.gov.in/sebiweb/ajax/home/getnewslistallinfo.jsp"


class SebiCircularsSpider(scrapy.Spider):
    name = "sebi_circulars"
    custom_settings = {
        "DOWNLOAD_DELAY": 1.0,
        "CONCURRENT_REQUESTS": 2,
    }

    start_urls = [
        "https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListingAll=yes"
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cutoff_date = datetime.strptime(settings.cutoff_date, "%Y-%m-%d").date()
        self.output_dir = Path(settings.raw_data_dir) / "sebi_circulars"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.page_num = 0
        self.items_scraped = 0

    def parse(self, response):
        rows = response.css("table#sample_1 tbody tr")
        if not rows:
            rows = response.css("table.table-striped tbody tr")
        if not rows:
            rows = response.css("table.table tbody tr")

        hit_cutoff = False
        for row in rows:
            cells = row.css("td")
            if len(cells) < 3:
                continue

            date_text = cells[0].css("::text").get("").strip()
            issued_date = self._parse_date(date_text)
            if not issued_date:
                continue

            if issued_date < self.cutoff_date:
                hit_cutoff = True
                continue

            doc_type = cells[1].css("::text").get("").strip()
            if doc_type.lower() not in ("circulars", "circular", "guidelines", "directions", "notifications", "notification"):
                continue

            title = cells[2].css("a::text").get("").strip()
            if not title:
                title = " ".join(cells[2].css("*::text").getall()).strip()
            link = cells[2].css("a::attr(href)").get()
            if not link or not title:
                continue

            detail_url = urljoin(response.url, link)
            circular_number = extract_circular_number(title)
            doc_id = generate_doc_id("sebi_circular", detail_url)

            yield scrapy.Request(
                url=detail_url,
                callback=self.parse_detail,
                meta={
                    "doc_id": doc_id,
                    "source": "sebi_circular",
                    "circular_number": circular_number,
                    "title": title,
                    "date_issued": str(issued_date),
                    "detail_url": detail_url,
                },
                dont_filter=False,
            )

        if not hit_cutoff:
            self.page_num += 1
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
            rows = response.css("tr")
            if not rows:
                logger.info(f"No more pages at page {self.page_num}")
                return
            yield from self._process_rows(rows, response)
            return

        if isinstance(data, list):
            hit_cutoff = False
            for item in data:
                date_str = item.get("formattedDate", "") or item.get("date", "")
                issued_date = self._parse_date(date_str)
                if not issued_date:
                    continue
                if issued_date < self.cutoff_date:
                    hit_cutoff = True
                    continue

                title = item.get("title", "").strip()
                link = item.get("link", "") or item.get("url", "")
                if not link or not title:
                    continue

                detail_url = urljoin(response.url, link)
                circular_number = extract_circular_number(title)
                doc_id = generate_doc_id("sebi_circular", detail_url)

                yield scrapy.Request(
                    url=detail_url,
                    callback=self.parse_detail,
                    meta={
                        "doc_id": doc_id,
                        "source": "sebi_circular",
                        "circular_number": circular_number,
                        "title": title,
                        "date_issued": str(issued_date),
                        "detail_url": detail_url,
                    },
                )

            if not hit_cutoff and data:
                self.page_num += 1
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

    def _process_rows(self, rows, response):
        hit_cutoff = False
        for row in rows:
            cells = row.css("td")
            if len(cells) < 3:
                continue

            date_text = cells[0].css("::text").get("").strip()
            issued_date = self._parse_date(date_text)
            if not issued_date:
                continue
            if issued_date < self.cutoff_date:
                hit_cutoff = True
                continue

            title = cells[2].css("a::text").get("").strip()
            if not title:
                title = " ".join(cells[2].css("*::text").getall()).strip()
            link = cells[2].css("a::attr(href)").get()
            if not link or not title:
                continue

            detail_url = urljoin(response.url, link)
            circular_number = extract_circular_number(title)
            doc_id = generate_doc_id("sebi_circular", detail_url)

            yield scrapy.Request(
                url=detail_url,
                callback=self.parse_detail,
                meta={
                    "doc_id": doc_id,
                    "source": "sebi_circular",
                    "circular_number": circular_number,
                    "title": title,
                    "date_issued": str(issued_date),
                    "detail_url": detail_url,
                },
            )

        if not hit_cutoff:
            self.page_num += 1
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
            pdf_links = response.css("a[href*='.pdf']::attr(href)").getall()
        if not pdf_links:
            pdf_links = response.xpath("//a[contains(@href, '.pdf')]/@href").getall()

        if not pdf_links:
            self.items_scraped += 1
            yield {
                "doc_id": meta["doc_id"],
                "source": meta["source"],
                "circular_number": meta["circular_number"],
                "title": meta["title"],
                "date_issued": meta["date_issued"],
                "url": meta["detail_url"],
                "local_pdf_path": "",
                "page_count": 0,
                "file_size_bytes": 0,
                "scraped_at": datetime.utcnow().isoformat(),
            }
            return

        pdf_url = urljoin(response.url, pdf_links[0])
        cn = meta["circular_number"]
        filename = sanitize_filename(cn or meta["title"][:60]) + ".pdf"
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
            "circular_number": meta["circular_number"],
            "title": meta["title"],
            "date_issued": meta["date_issued"],
            "url": meta["url"],
            "local_pdf_path": local_path,
            "page_count": page_count,
            "file_size_bytes": file_size,
            "scraped_at": datetime.utcnow().isoformat(),
        }

    def _parse_date(self, text: str):
        text = text.strip().rstrip(".")
        for fmt in ("%b %d, %Y", "%d-%b-%Y", "%d %b %Y", "%d/%m/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                continue
        return None
