import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

import scrapy
from loguru import logger

from api.config import settings
from ingestion.metadata_extractor import (
    generate_doc_id,
    sanitize_filename,
)

RBI_REF_RE = re.compile(r'RBI/\S+/\d{4}-\d{2,4}/\d+', re.IGNORECASE)
RBI_SHORT_RE = re.compile(r'RBI/\d{4}-\d{2}/\d+', re.IGNORECASE)


class RbiCircularsSpider(scrapy.Spider):
    name = "rbi_circulars"
    custom_settings = {
        "DOWNLOAD_DELAY": 1.5,
        "CONCURRENT_REQUESTS": 1,
    }

    BASE_URL = "https://www.rbi.org.in/Scripts/BS_CircularIndexDisplay.aspx"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.output_dir = Path(settings.raw_data_dir) / "rbi_circulars"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cutoff_year = int(settings.cutoff_date.split("-")[0])
        self.items_scraped = 0

    def start_requests(self):
        yield scrapy.Request(url=self.BASE_URL, callback=self.parse_first_page)

    def parse_first_page(self, response):
        yield from self._extract_rows(response)

        viewstate = response.css("input#__VIEWSTATE::attr(value)").get("")
        validation = response.css("input#__EVENTVALIDATION::attr(value)").get("")
        viewstategen = response.css("input#__VIEWSTATEGENERATOR::attr(value)").get("")

        current_year = datetime.now().year
        for year in range(current_year, self.cutoff_year - 1, -1):
            for month in range(1, 13):
                yield scrapy.FormRequest(
                    url=self.BASE_URL,
                    formdata={
                        "__VIEWSTATE": viewstate,
                        "__EVENTVALIDATION": validation,
                        "__VIEWSTATEGENERATOR": viewstategen,
                        "__EVENTTARGET": "",
                        "__EVENTARGUMENT": "",
                        "hdnYear": str(year),
                        "hdnMonth": str(month),
                    },
                    callback=self.parse_month,
                    meta={"year": year, "month": month},
                    dont_filter=True,
                )

    def parse_month(self, response):
        yield from self._extract_rows(response)

    def _extract_rows(self, response):
        rows = response.css("table.tablebg tr")
        if not rows:
            rows = response.css("table tr")

        for row in rows:
            cells = row.css("td")
            if len(cells) < 4:
                continue

            circ_cell = cells[0]
            circ_text = " ".join(circ_cell.css("*::text").getall()).strip()
            circ_link = circ_cell.css("a::attr(href)").get()

            ref_number = None
            for pattern in [RBI_SHORT_RE, RBI_REF_RE]:
                match = pattern.search(circ_text)
                if match:
                    ref_number = match.group(0).strip()
                    break
            if not ref_number:
                ref_number = circ_text.split("\n")[0].strip()[:80] if circ_text else None

            date_text = cells[1].css("::text").get("").strip()
            issued_date = self._parse_date(date_text)
            if not issued_date:
                continue

            title_cell = cells[3] if len(cells) > 3 else cells[2]
            title = " ".join(title_cell.css("*::text").getall()).strip()
            if not title:
                title = circ_text[:100] if circ_text else "Untitled"

            detail_link = circ_link
            if not detail_link:
                for cell in cells:
                    detail_link = cell.css("a::attr(href)").get()
                    if detail_link:
                        break
            if not detail_link:
                continue

            detail_url = urljoin(response.url, detail_link)
            doc_id = generate_doc_id("rbi_circular", detail_url)

            yield scrapy.Request(
                url=detail_url,
                callback=self.parse_detail,
                meta={
                    "doc_id": doc_id,
                    "source": "rbi_circular",
                    "circular_number": ref_number,
                    "title": title,
                    "date_issued": str(issued_date),
                    "detail_url": detail_url,
                },
                dont_filter=False,
            )

    def parse_detail(self, response):
        meta = response.meta

        pdf_links = response.css("a[href$='.pdf']::attr(href)").getall()
        if not pdf_links:
            pdf_links = response.css("a[href$='.PDF']::attr(href)").getall()
        if not pdf_links:
            pdf_links = response.xpath("//a[contains(@href, '.pdf') or contains(@href, '.PDF')]/@href").getall()

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
        if not text:
            return None
        text = text.strip()
        for fmt in ("%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y", "%b %d, %Y", "%d %b %Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                continue
        parts = text.split(".")
        if len(parts) == 3:
            try:
                d, m, y = int(parts[0]), int(parts[1]), int(parts[2])
                return datetime(y, m, d).date()
            except (ValueError, TypeError):
                pass
        return None
