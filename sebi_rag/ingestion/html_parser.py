import re
from html.parser import HTMLParser

from loguru import logger


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._text_parts: list[str] = []
        self._skip = False
        self._skip_tags = {"script", "style", "noscript", "head"}

    def handle_starttag(self, tag, attrs):
        if tag in self._skip_tags:
            self._skip = True
        if tag in ("br", "p", "div", "tr", "li", "h1", "h2", "h3", "h4", "h5", "h6"):
            self._text_parts.append("\n")
        if tag == "td":
            self._text_parts.append("\t")

    def handle_endtag(self, tag):
        if tag in self._skip_tags:
            self._skip = False
        if tag in ("p", "div", "table", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6"):
            self._text_parts.append("\n")

    def handle_data(self, data):
        if not self._skip:
            self._text_parts.append(data)

    def get_text(self) -> str:
        raw = "".join(self._text_parts)
        raw = re.sub(r"\t+", " | ", raw)
        raw = re.sub(r" +", " ", raw)
        raw = re.sub(r"\n{3,}", "\n\n", raw)
        return raw.strip()


def parse_html_file(file_path: str) -> list[dict]:
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            html_content = f.read()
    except Exception as e:
        logger.error(f"Failed to read HTML file {file_path}: {e}")
        return []

    extractor = _TextExtractor()
    try:
        extractor.feed(html_content)
    except Exception as e:
        logger.error(f"Failed to parse HTML {file_path}: {e}")
        return []

    text = extractor.get_text()
    if len(text.strip()) < 50:
        logger.warning(f"HTML file has insufficient text: {file_path}")
        return []

    return [{"page_num": 1, "text": text, "font_sizes": [], "has_table": False, "blocks": []}]
