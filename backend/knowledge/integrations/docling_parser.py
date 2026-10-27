"""Local PDF conversion with persistent structure and exact text provenance."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from importlib.metadata import version
from pathlib import Path


def assemble_blocks(blocks: list[dict], maximum: int) -> tuple[str, list[dict], bool]:
    """Keep whole tables/captions and map canonical text offsets to source items."""
    pieces, source_map = [], []
    length, current_page, truncated = 0, None, False
    for block in blocks:
        text = block["text"].strip()
        if not text:
            continue
        pages = sorted({p["page_no"] for p in block["provenance"]})
        page = pages[0] if pages else None
        prefix = "\n\n" if pieces else ""
        if page is not None and page != current_page:
            prefix += f"## 페이지 {page}\n\n"
        if length + len(prefix) + len(text) > maximum:
            truncated = True
            break
        pieces.extend([prefix, text])
        start = length + len(prefix)
        length = start + len(text)
        current_page = page
        source_map.append({
            "startOffset": start, "endOffset": length,
            "label": block["label"], "locator": block["locator"],
            "documentRefs": block["documentRefs"], "pageNumbers": pages,
            "provenance": block["provenance"],
        })
    content = "".join(pieces)
    if not content.strip():
        raise ValueError("No readable text within the configured limit")
    return content, source_map, truncated


def document_blocks(document, artifacts: Path, title: str) -> list[dict]:
    """Use native structural/token-aware chunking, retaining original item refs."""
    import tiktoken
    from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
    from docling_core.transforms.chunker.hierarchical_chunker import ChunkingDocSerializer, ChunkingSerializerProvider
    from docling_core.transforms.chunker.tokenizer.openai import OpenAITokenizer
    from docling_core.transforms.serializer.markdown import MarkdownTableSerializer

    class TablePreservingSerializer(ChunkingSerializerProvider):
        def get_serializer(self, doc):
            return ChunkingDocSerializer(doc=doc, table_serializer=MarkdownTableSerializer())

    # tiktoken otherwise downloads a missing/corrupt encoding. Fail closed first.
    url = "https://openaipublic.blob.core.windows.net/encodings/cl100k_base.tiktoken"
    cache = artifacts / "tokenizer"
    encoding = cache / hashlib.sha1(url.encode()).hexdigest()
    if hashlib.sha256(encoding.read_bytes()).hexdigest() != "223921b76ee99bde995b7ff738513eef100fb51d18c93597a113bcffe865b2a7":
        raise ValueError("Prefetched tokenizer hash mismatch")
    os.environ["TIKTOKEN_CACHE_DIR"] = str(cache)
    chunker = HybridChunker(tokenizer=OpenAITokenizer(tokenizer=tiktoken.get_encoding("cl100k_base"),
                            max_tokens=768), repeat_table_header=True, merge_peers=True,
                            serializer_provider=TablePreservingSerializer())
    blocks = []
    for chunk in chunker.chunk(dl_doc=document):
        if not chunk.text.strip():
            continue
        items = chunk.meta.doc_items
        refs = [item.self_ref for item in items]
        provenance = [p.model_dump(mode="json") for item in items for p in getattr(item, "prov", [])]
        for item in items:
            for caption_ref in getattr(item, "captions", []):
                refs.append(caption_ref.cref)
                provenance.extend(p.model_dump(mode="json") for p in caption_ref.resolve(document).prov)
        page_numbers = sorted({p["page_no"] for p in provenance})
        page_label = ", ".join(str(p) for p in page_numbers) or "미확인"
        labels = list(dict.fromkeys(item.label.value for item in items))
        table_refs = [item.self_ref for item in items if item.label.value == "table"]
        locator = f"페이지 {page_label}" + (" · 표 " + ", ".join(str(int(ref.rsplit('/', 1)[1]) + 1) for ref in table_refs)
                                               if table_refs else " · 본문")
        context = chunker.contextualize(chunk=chunk)
        # Headings/captions often carry the experiment condition: keep them in cited text too.
        blocks.append({"text": context, "label": ",".join(labels), "locator": locator,
                       "documentRefs": refs, "provenance": provenance,
                       "embeddingText": f"{title}\n\n{context}" if title else context})
    return blocks


def parse_pdf(body: bytes, *, artifacts_path: str, max_pages: int = 100,
              max_characters: int = 500000, ocr: bool = False) -> dict:
    from docling.datamodel.base_models import DocumentStream, InputFormat
    from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
    from docling.datamodel.pipeline_options import AcceleratorDevice, AcceleratorOptions, OcrMode, PdfPipelineOptions, RapidOcrOptions, TableStructureOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from pypdf import PdfReader

    artifacts = Path(artifacts_path).resolve(strict=True)
    if not artifacts.is_dir() or not 1 <= max_pages <= 1000 or not 1000 <= max_characters <= 2000000:
        raise ValueError("Invalid parser configuration")
    reader = PdfReader(io.BytesIO(body))
    if reader.is_encrypted:
        raise ValueError("Encrypted PDF")
    total_pages = len(reader.pages)
    pages_read = min(total_pages, max_pages)
    options = PdfPipelineOptions(
        artifacts_path=artifacts, enable_remote_services=False, do_ocr=ocr,
        do_table_structure=True, table_structure_options=TableStructureOptions(do_cell_matching=True),
        force_backend_text=False, generate_page_images=False,
        generate_picture_images=False, do_picture_classification=False,
        do_picture_description=False, accelerator_options=AcceleratorOptions(
            device=AcceleratorDevice.CPU, num_threads=4),
    )
    if ocr:
        options.ocr_options = RapidOcrOptions(backend="torch", lang=["en"], mode=OcrMode.FULL_PAGE)
    converter = DocumentConverter(allowed_formats=[InputFormat.PDF],
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options, backend=PyPdfiumDocumentBackend)})
    source_hash = hashlib.sha256(body).hexdigest()
    converted = converter.convert(DocumentStream(name=source_hash + ".pdf", stream=io.BytesIO(body)),
        page_range=(1, pages_read), max_file_size=20 * 1024 * 1024, raises_on_error=True)
    document = converted.document
    pdf_metadata = reader.metadata
    title = str(pdf_metadata.title or "")[:500] if pdf_metadata else ""
    if not title:
        title = next((i.text for i in document.texts if i.label.value == "title"), "")[:500]
    blocks = document_blocks(document, artifacts, title)
    content, source_map, truncated = assemble_blocks(blocks, max_characters)
    prepared = []
    for source, block in zip(source_map, blocks):
        text = content[source["startOffset"]:source["endOffset"]]
        embedding_text = block["embeddingText"]
        prepared.append({"text": text, "locator": source["locator"],
                         "start_offset": source["startOffset"], "end_offset": source["endOffset"],
                         "embedding_text": embedding_text,
                         "input_hash": hashlib.sha256(embedding_text.encode("utf-8")).hexdigest()})
    status = str(getattr(converted.status, "value", converted.status))
    represented_pages = {p for source in source_map for p in source["pageNumbers"]}
    unrepresented_pages = sorted(set(range(1, pages_read + 1)) - represented_pages)
    partial = pages_read < total_pages or truncated or status != "success" or bool(unrepresented_pages)
    limitations = ["그림 내부의 그래프 수치·기작은 해석하지 않았습니다. 본문·표·그림 캡션과 원문 위치를 추출했습니다."]
    if not ocr:
        limitations.append("OCR을 사용하지 않았습니다. 스캔된 글자와 이미지 속 글자는 추출 범위에 포함되지 않습니다.")
    if pages_read < total_pages:
        limitations.append(f"전체 {total_pages}페이지 중 처음 {pages_read}페이지를 읽었습니다.")
    if truncated:
        limitations.append(f"본문 한도 {max_characters}자에 맞춰 완전한 문서 요소까지 보존했습니다.")
    if unrepresented_pages:
        limitations.append("검색 가능한 본문을 확보하지 못한 페이지: " + ", ".join(map(str, unrepresented_pages)))
    if status != "success":
        limitations.append("일부 문서 요소의 변환이 완료되지 않았습니다.")
    profile = {"engine": "docling", "version": version("docling"),
               "coreVersion": version("docling-core"), "layoutModelsVersion": version("docling-ibm-models"),
               "pdfBackend": "pypdfium2", "pdfBackendVersion": version("pypdfium2"), "serialization": "hybrid-markdown-v3",
               "chunker": "HybridChunker", "maxTokens": 768, "tokenizer": "cl100k_base",
               "tokenizerVersion": version("tiktoken"), "repeatTableHeader": True, "mergePeers": True,
               "ocr": ocr, "ocrEngine": "rapidocr-torch-en-full-page" if ocr else None,
               "tableStructure": True, "maxPages": max_pages,
               "maxCharacters": max_characters}
    return {"title": title, "content": content, "readScope": "partial" if partial else "full",
            "metadata": {"author": str(pdf_metadata.author)[:500] if pdf_metadata and pdf_metadata.author else None,
                         "documentForm": "text_extraction", "sourceSha256": source_hash,
                         "parserProfile": profile, "totalPages": total_pages, "pagesRead": pages_read,
                         "pagesWithoutExtractedText": unrepresented_pages,
                         "conversionStatus": status, "tableCount": len(document.tables),
                         "pictureCount": len(document.pictures)},
            "limitations": limitations, "structuredDocument": document.export_to_dict(),
            "sourceMap": source_map, "preparedPassages": prepared}


if __name__ == "__main__":
    import sys
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts-path", required=True)
    parser.add_argument("--max-pages", type=int, default=100)
    parser.add_argument("--max-characters", type=int, default=500000)
    parser.add_argument("--ocr", action="store_true")
    args = parser.parse_args()
    raw = sys.stdin.buffer.read(20 * 1024 * 1024 + 1)
    if len(raw) > 20 * 1024 * 1024:
        raise ValueError("Input exceeds 20 MB")
    result = parse_pdf(raw, artifacts_path=args.artifacts_path, max_pages=args.max_pages,
                       max_characters=args.max_characters, ocr=args.ocr)
    print(json.dumps(result, ensure_ascii=False))
