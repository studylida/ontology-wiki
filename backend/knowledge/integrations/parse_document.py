"""Sandboxable, bounded document parsing subprocess. No network or credentials."""
import io
import json
import resource
import sys

from bs4 import BeautifulSoup
from pypdf import PdfReader


def parse(body, media_type):
    resource.setrlimit(resource.RLIMIT_CPU, (8, 8))
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
    maximum = 80000
    title, metadata, limitations = "", {}, []
    if media_type == "application/pdf":
        reader = PdfReader(io.BytesIO(body))
        if reader.is_encrypted:
            raise ValueError("Encrypted PDF")
        total = len(reader.pages)
        count = min(total, 30)
        content = "\n\n".join(f"## 페이지 {i + 1}\n{reader.pages[i].extract_text() or ''}" for i in range(count))
        scope = "full" if count == total and len(content) <= maximum else "partial"
        if reader.metadata:
            title = str(reader.metadata.title or "")
            metadata["author"] = str(reader.metadata.author) if reader.metadata.author else None
        if scope == "partial":
            limitations.append(f"PDF {total}페이지 중 최대 {count}페이지·{maximum}자만 확인했습니다.")
        if len(content.strip()) < 40:
            limitations.append("텍스트 추출량이 적습니다. 스캔 이미지와 도표는 읽지 못할 수 있습니다.")
            scope = "partial"
    elif media_type in ("text/html", "application/xhtml+xml"):
        soup = BeautifulSoup(body, "html.parser")
        title = soup.title.get_text(" ", strip=True) if soup.title else ""
        for field, names in (("author", ["author", "article:author"]), ("publisher", ["og:site_name"]),
                             ("publishedAt", ["article:published_time", "citation_publication_date"])):
            for name in names:
                tag = soup.find("meta", attrs={"name": name}) or soup.find("meta", attrs={"property": name})
                if tag and tag.get("content"):
                    metadata[field] = tag["content"]
                    break
        for tag in soup.select("script,style,nav,footer,header,noscript,svg,form"):
            tag.decompose()
        main = soup.find("article") or soup.find("main") or soup.body or soup
        content = main.get_text("\n", strip=True)
        scope = "partial"
        limitations.append("공개 HTML에서 추출한 텍스트입니다. 동적 내용·이미지·표의 완전성은 확인하지 못했습니다.")
    else:
        content = body.decode("utf-8", errors="replace")
        scope = "full" if len(content) <= maximum else "partial"
    if len(content) > maximum:
        limitations.append(f"본문을 {maximum}자로 제한했습니다.")
    if not content.strip():
        raise ValueError("No readable text")
    return {"title": title[:500], "content": content[:maximum], "readScope": scope,
            "metadata": metadata, "limitations": limitations}


if __name__ == "__main__":
    result = parse(sys.stdin.buffer.read(5 * 1024 * 1024 + 1), sys.argv[1])
    print(json.dumps(result, ensure_ascii=False))
