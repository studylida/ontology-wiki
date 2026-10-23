"""Public document text extraction and bounded reading; no HTTP or database I/O."""
import asyncio
from hashlib import sha256
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import urljoin, urlsplit


def document_matches(text, title, doi_url):
    words = set(re.findall(r"[a-z0-9]+", title.casefold())) - {"the", "and", "for", "of", "in", "a"}
    found = set(re.findall(r"[a-z0-9]+", text.casefold()))
    return len(words) >= 3 and len(words & found) >= max(3, len(words) * .65)


class ArticleText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hidden = 0
        self.parts, self.abstracts, self.pdfs, self.titles, self.identifiers = [], [], [], [], []
        self.heading = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in {"script", "style", "nav", "footer", "form", "noscript"}:
            self.hidden += 1
        if tag == "meta":
            name = (attrs.get("name") or attrs.get("property") or "").casefold()
            value = attrs.get("content", "")
            if name in {"citation_abstract", "dc.description", "dcterms.abstract"}:
                self.abstracts.append(value)
            if name == "citation_pdf_url":
                self.pdfs.append(value)
            if name in {"citation_title", "dc.title", "dcterms.title"}:
                self.titles.append(value)
            if name in {"citation_doi", "dc.identifier", "dc.identifier.doi", "dcterms.identifier"}:
                self.identifiers.append(value)
        if tag in {"title", "h1"}:
            self.heading = tag
        if tag in {"p", "div", "h1", "h2", "h3", "br", "section", "article"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag == self.heading:
            self.heading = None
        if tag in {"script", "style", "nav", "footer", "form", "noscript"}:
            self.hidden = max(0, self.hidden - 1)
        if tag in {"p", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)
            if self.heading:
                self.titles.append(data)


def html_content(data, url, title, doi_url):
    page = data.decode("utf-8", errors="replace")
    parser = ArticleText()
    parser.feed(page)
    text = "\n".join(re.sub(r"\s+", " ", x).strip() for x in "".join(parser.parts).splitlines())
    text = re.sub(r"\n+", "\n\n", text).strip()
    doi = doi_url.partition("doi.org/")[2].casefold()
    identified = doi and any(value.casefold().removeprefix("https://doi.org/").removeprefix("doi:").strip() == doi for value in parser.identifiers)
    if not identified and not document_matches(" ".join(parser.titles), title, doi_url):
        raise ValueError("document_identity_unverified")
    if parser.abstracts:
        text = "\n\n".join(parser.abstracts) + "\n\n" + text
    if len(text) < 200 or re.search(r"(?i)verify (?:that )?you(?:'re| are) (?:not )?a (?:robot|human)|just a moment|access denied", text[:2000]):
        raise ValueError("technical_content_unavailable")
    pdfs = [urljoin(url, p) for p in parser.pdfs]
    return text[:100000], [p for p in pdfs if urlsplit(p).scheme == "https" and urlsplit(p).hostname and not urlsplit(p).username]


def read_segments(item_id, text, source_url, kind, topic):
    terms = set(re.findall(r"[\w-]+", topic.casefold())) - {"and", "or", "the", "for", "of", "in"}
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    ranked = sorted(enumerate(paragraphs), key=lambda p: sum(t in p[1].casefold() for t in terms), reverse=True)
    selected, size = [], 0
    for index, paragraph in ranked:
        paragraph = paragraph[:6000 - size]
        if not paragraph:
            break
        selected.append((index, paragraph))
        size += len(paragraph)
    return [{"id": item_id + ":" + sha256((source_url + p).encode()).hexdigest()[:12], "text": p,
             "sectionContext": "공개 원문 일부 구간", "sourceUrl": source_url, "contentKind": kind}
            for _, p in sorted(selected)]


async def pdf_content(data, title, doi_url):
    # A worker process bounds PDF parser CPU time and keeps cancellation effective.
    env = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[3]) + os.pathsep + os.environ.get("PYTHONPATH", "")}
    process = await asyncio.create_subprocess_exec(sys.executable, "-m", __name__, "pdf",
        stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL, env=env)
    try:
        stdout, _ = await asyncio.wait_for(process.communicate(data), timeout=10)
        if process.returncode:
            raise ValueError("pdf_text_unavailable")
        text = json.loads(stdout)
        if not document_matches(text[:2000], title, doi_url):
            raise ValueError("document_identity_unverified")
        return text
    finally:
        if process.returncode is None:
            process.kill()
            await process.wait()


if __name__ == "__main__":
    from io import BytesIO
    from pypdf import PdfReader
    import pypdf.filters
    pypdf.filters.ZLIB_MAX_OUTPUT_LENGTH = 8_000_000
    reader = PdfReader(BytesIO(sys.stdin.buffer.read(5_000_001)))
    parts, total = [], 0
    # shortcut: read at most 20 pages/100k characters; OCR and complete reading are separate work.
    for page in reader.pages[:20]:
        content = page.get_contents()
        if content and len(content.get_data()) > 8_000_000:
            raise ValueError("pdf_page_too_large")
        text = page.extract_text() or ""
        parts.append(text)
        total += len(text)
        if total >= 100000:
            break
    text = "\n\n".join(parts)[:100000]
    if len(text.strip()) < 200:
        raise ValueError("pdf_text_unavailable")
    sys.stdout.buffer.write(json.dumps(text, ensure_ascii=True).encode())
