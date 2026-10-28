"""Local file conversion, independent from URL discovery/fetching.

The existing bounded PDF/JATS converters, conversion cache and quality gate are
reused here. Missing Docling configuration is a failure, never a fallback.
"""
from __future__ import annotations
import asyncio
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from time import monotonic
from ..core.errors import AppError
from .bounded_process import BoundedProcessError, run_bounded_python

MAX_BYTES = 5 * 1024 * 1024


def _parser_environment():
    env = {key: value for key, value in os.environ.items()
           if key.upper() in {'PATH','SYSTEMROOT','WINDIR','TEMP','TMP','LANG','LC_ALL'}}
    env.update(PYTHONPATH=str(Path(__file__).resolve().parents[2]), PYTHONUTF8='1',
               PYTHONNOUSERSITE='1', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
               HF_HUB_DISABLE_IMPLICIT_TOKEN='1', HF_HUB_DISABLE_TELEMETRY='1')
    return env


async def parse_file(body: bytes, media_type: str, *, parser='legacy', python_executable=None,
                     artifacts_path=None, storage_path=None, max_pages=100,
                     max_characters=500000, timeout_seconds=None, ocr=False):
    started = monotonic()
    use_jats = media_type in {'application/xml','text/xml','application/jats+xml'}
    use_docling = parser == 'docling' and (media_type == 'application/pdf' or use_jats)
    if parser not in {'legacy','docling'}:
        raise AppError(503, 'parser_configuration', '문헌 해석기 설정이 올바르지 않습니다.')
    if use_jats and (parser != 'docling' or ocr):
        raise AppError(503, 'parser_configuration', 'JATS XML에는 OCR을 끈 Docling 설정이 필요합니다.')
    if not body or len(body) > (20 * 1024 * 1024 if use_docling and not use_jats else MAX_BYTES):
        raise AppError(413, 'source_too_large', '문헌 해석 입력의 크기 한도를 확인해 주세요.')
    if use_jats and re.search(br'<!\s*ENTITY', body, re.I):
        raise AppError(422, 'unsafe_xml', '엔티티 선언을 포함한 XML은 처리하지 않습니다.')
    # Ordinary publisher DOCTYPEs are allowed. normalize_jats also checks the
    # parsed DTD (including UTF-16), disables entity expansion and all network I/O.
    if use_docling and (not python_executable or not artifacts_path):
        raise AppError(503, 'parser_configuration', 'Docling 실행 환경과 모델 경로를 설정해 주세요.')
    if use_docling:
        from .docling_artifacts import conversion_key, load_conversion, model_fingerprint, preserve_conversion
        try:
            model_hash = await asyncio.to_thread(model_fingerprint, artifacts_path)
            legacy_key = conversion_key(body, max_pages=max_pages, max_characters=max_characters,
                                        ocr=ocr, model_artifacts_hash=model_hash)
            key = hashlib.sha256((('runtime-quality-v12:jats:' if use_jats else 'runtime-quality-v3:pdf:') + legacy_key).encode()).hexdigest()
            cached = load_conversion(storage_path, key, body) if storage_path else None
        except (OSError, KeyError, TypeError, ValueError) as exc:
            raise AppError(503, 'parser_artifact_invalid', 'Docling 모델과 변환 보존 파일을 확인해 주세요.') from exc
        if cached is not None:
            processing = cached['metadata']['processing']
            processing.update(originalElapsedMs=processing['elapsedMs'], cacheHit=True,
                              elapsedMs=round((monotonic() - started) * 1000, 2))
            return cached
        module = 'knowledge.integrations.docling_jats' if use_jats else 'knowledge.integrations.docling_parser'
        executable = python_executable
        args = ([str(Path(artifacts_path).resolve()), '--max-characters', str(max_characters)] if use_jats else
                ['--artifacts-path', str(Path(artifacts_path).resolve()), '--max-pages', str(max_pages),
                 '--max-characters', str(max_characters)] + (['--ocr'] if ocr else []))
    else:
        module, executable, args = 'knowledge.integrations.parse_document', sys.executable, [media_type]
    try:
        with tempfile.TemporaryDirectory(prefix='ontology-parser-') as parser_home:
            env = _parser_environment()
            env.update(HOME=parser_home, USERPROFILE=parser_home, HF_HOME=str(Path(parser_home) / 'huggingface'))
            stdout = await run_bounded_python(executable, module, args, input_bytes=body, env=env,
                timeout_seconds=timeout_seconds or (480 if use_docling else 12),
                cpu_seconds=600 if use_docling else 8,
                memory_bytes=(8 * 1024 if use_docling else 512) * 1024 * 1024,
                max_output_bytes=(32 if use_docling else 2) * 1024 * 1024)
    except TimeoutError as exc:
        raise AppError(422, 'source_parse_timeout', '문헌 해석 시간이 제한을 넘었습니다.') from exc
    except BoundedProcessError as exc:
        raise AppError(422, 'source_parse_failed', '문헌 본문을 추출하지 못했습니다.',
                       details={'parserFailure': exc.code}) from exc
    try:
        result = json.loads(stdout)
        if not isinstance(result['content'], str) or not result['content'].strip() or '\x00' in result['content']:
            raise ValueError('Invalid extraction')
        if use_docling:
            if result['metadata']['parserProfile']['version'] != '2.143.0':
                raise ValueError('Unexpected parser version')
            result['metadata']['parserProfile']['modelArtifactsHash'] = model_hash
            result['metadata']['processing'] = {'elapsedMs': round((monotonic() - started) * 1000, 2),
                                               'cacheHit': False, 'execution': 'local_cpu'}
            from ..documents.runtime_preprocessing import prepare_conversion
            result = prepare_conversion(result, body, jats=use_jats)
            if storage_path:
                preserve_conversion(storage_path, key, body, result)
        elif media_type == 'application/pdf':
            if not re.sub(r'(?m)^## 페이지 \d+\s*$', '', result['content']).strip():
                raise ValueError('PDF contains no extracted text')
            result['metadata']['parserProfile'] = {'engine': 'pypdf', 'mode': 'text_only'}
            result['readScope'] = 'partial'
            result['limitations'].append('PDF 텍스트 추출입니다. 이미지·표 구조·수식의 완전성을 보장하지 않습니다.')
        return result
    except (KeyError, TypeError, ValueError) as exc:
        raise AppError(422, 'source_parse_contract', '문헌 해석 결과의 형식을 확인할 수 없습니다.') from exc
