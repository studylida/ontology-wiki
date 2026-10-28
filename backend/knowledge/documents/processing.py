"""Turn preserved file bytes into existing source-preserving passages."""
from dataclasses import dataclass
import re
from .parsing import ParsedPassage, declared_document_form, prepared_passages, segment
from ..core.errors import AppError
from ..integrations.document_parser import parse_file


@dataclass(frozen=True)
class PreparedDocument:
    content: str
    passages: list[ParsedPassage]
    source_map: list[dict]
    metadata: dict
    read_scope: str
    limitations: list[str]


async def prepare_file(raw, media_type, title, settings):
    if media_type in ('text/plain','text/markdown'):
        try:
            content = raw.decode('utf-8-sig', errors='strict')
        except UnicodeDecodeError as exc:
            raise AppError(422, 'source_encoding', '텍스트와 Markdown은 UTF-8 형식이어야 합니다.') from exc
        if '\x00' in content or not content.strip():
            raise AppError(422, 'source_parse_failed', '비어 있거나 텍스트로 읽을 수 없는 파일입니다.')
        if len(content) > settings.docling_max_characters:
            raise AppError(413, 'source_too_large', '텍스트 본문이 설정된 문자 수 한도를 넘었습니다.')
        passages = segment(content, title)
        metadata = {'parserProfile': {'engine': 'markdown_blocks', 'version': 1},
                    'documentForm': declared_document_form(content) or 'original'}
        sources = [{'startOffset': p.start_offset, 'endOffset': p.end_offset,
                    'locator': p.locator} for p in passages]
        result = PreparedDocument(content, passages, sources, metadata, 'full', [])
    else:
        conversion = await parse_file(raw, media_type, parser=settings.pdf_parser,
            python_executable=settings.docling_python_path, artifacts_path=settings.docling_artifacts_path,
            storage_path=settings.storage_path, max_pages=settings.docling_max_pages,
            max_characters=settings.docling_max_characters, timeout_seconds=settings.docling_timeout_seconds
            if settings.pdf_parser == 'docling' else 12, ocr=settings.docling_ocr)
        content = conversion['content']
        records = conversion.get('preparedPassages')
        passages = prepared_passages(content, records) if records is not None else segment(content, title)
        sources = conversion.get('sourceMap') or [
            {'startOffset': p.start_offset, 'endOffset': p.end_offset, 'locator': p.locator,
             'pageNumbers': [int(n) for n in re.findall(r'페이지 (\d+)', p.locator)]} for p in passages]
        if len(sources) != len(passages):
            raise AppError(422, 'source_parse_contract', '본문 구간과 원문 위치가 대응하지 않습니다.')
        result = PreparedDocument(content, passages, sources, conversion.get('metadata', {}),
                                  conversion.get('readScope','partial'), conversion.get('limitations', []))
    if not result.passages:
        raise AppError(422, 'no_indexable_passages', '검색에 사용할 수 있는 본문 구간이 없습니다.')
    return result
