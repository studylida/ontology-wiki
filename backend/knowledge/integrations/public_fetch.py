"""Bounded public HTTPS fetch, with DNS pinning and validation at every redirect."""
from __future__ import annotations

import asyncio
import hashlib
import ipaddress
import json
import os
import socket
import sys
import tempfile
from pathlib import Path
from time import monotonic
from urllib.parse import urljoin, urlsplit, urlunsplit

import httpx

from knowledge.core.errors import AppError
from knowledge.integrations.bounded_process import BoundedProcessError, run_bounded_python

MAX_BYTES = 5 * 1024 * 1024


def validate_public_target(url: str):
    """Validate the original HTTPS authority before either resolver does I/O."""
    try:
        parsed = urlsplit(url)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.port not in (None, 443):
            raise ValueError()
        hostname = parsed.hostname.encode("idna").decode("ascii")
        try:
            literal = ipaddress.ip_address(hostname)
        except ValueError:
            literal = None
        if literal is not None and not literal.is_global:
            raise ValueError()
        return parsed, hostname, literal
    except (ValueError, UnicodeError) as exc:
        raise AppError(422, "unsafe_source_url", "공개 HTTPS 문헌 주소만 가져올 수 있습니다.") from exc


async def resolve_public_url(url: str):
    parsed, hostname, literal = validate_public_target(url)
    try:
        if literal is not None:
            ips = [str(literal)]
        else:
            addresses = await asyncio.wait_for(asyncio.to_thread(socket.getaddrinfo, hostname, 443, type=socket.SOCK_STREAM), timeout=10)
            ips = sorted({row[4][0] for row in addresses})
        if not ips or any(not ipaddress.ip_address(ip).is_global for ip in ips):
            raise ValueError()
    except (OSError, asyncio.TimeoutError) as exc:
        raise AppError(502, "source_dns_unavailable", "문헌 서버 주소를 확인하지 못했습니다. 잠시 후 다시 시도하세요.", retryable=True) from exc
    except (ValueError, UnicodeError) as exc:
        raise AppError(422, "unsafe_source_url", "공개 HTTPS 문헌 주소만 가져올 수 있습니다.") from exc
    ip = ips[0]
    authority = f"[{ip}]" if ":" in ip else ip
    pinned_url = urlunsplit(("https", authority, parsed.path or "/", parsed.query, ""))
    return pinned_url, hostname


async def fetch_public(url: str, *, transport=None, resolver=resolve_public_url):
    # trust_env=False prevents proxy routing from defeating the public-IP pin.
    async with httpx.AsyncClient(timeout=20, follow_redirects=False, trust_env=False, transport=transport) as client:
        current = url
        for hop in range(4):
            pinned, hostname = await resolver(current)
            try:
                async with client.stream("GET", pinned, headers={"Host": hostname,
                    "User-Agent": "OntologyKnowledge/1.0 (explicit user literature fetch)",
                    "Accept": "text/html,application/pdf,text/plain,text/markdown,application/xml,text/xml,application/jats+xml"},
                    extensions={"sni_hostname": hostname}) as response:
                    if response.status_code in (301, 302, 303, 307, 308):
                        location = response.headers.get("location")
                        if not location or hop == 3:
                            raise AppError(422, "redirect_limit", "문헌 주소의 이동 횟수가 제한을 넘었습니다.")
                        current = urljoin(current, location)
                        continue
                    if response.status_code != 200:
                        raise AppError(502, "source_unavailable", "문헌 본문을 가져오지 못했습니다.",
                                       details={"upstreamStatus": response.status_code})
                    length = response.headers.get("content-length")
                    if length and int(length) > MAX_BYTES:
                        raise AppError(413, "source_too_large", "첫 버전의 문헌 다운로드 한도는 5MB입니다.")
                    media_type = response.headers.get("content-type", "").split(";")[0].lower()
                    if media_type not in ("text/html", "application/pdf", "text/plain", "text/markdown", "application/xhtml+xml", "application/xml", "text/xml", "application/jats+xml"):
                        raise AppError(422, "unsupported_source_type", "HTML·PDF·JATS XML·텍스트 문헌만 가져올 수 있습니다.")
                    body = bytearray()
                    async for chunk in response.aiter_bytes():
                        body.extend(chunk)
                        if len(body) > MAX_BYTES:
                            raise AppError(413, "source_too_large", "문헌이 다운로드 한도를 넘었습니다.")
                    return bytes(body), media_type, current
            except httpx.HTTPError as exc:
                raise AppError(502, "source_connection", "문헌 서버에 연결하지 못했습니다.", retryable=True) from exc
    raise AppError(422, "redirect_limit", "문헌 주소 이동을 완료하지 못했습니다.")


def _parser_environment():
    env = {key: value for key, value in os.environ.items()
           if key.upper() in {"PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "LANG", "LC_ALL"}}
    env.update(PYTHONPATH=str(Path(__file__).resolve().parents[2]), PYTHONUTF8="1",
               PYTHONNOUSERSITE="1", HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1",
               HF_HUB_DISABLE_IMPLICIT_TOKEN="1", HF_HUB_DISABLE_TELEMETRY="1")
    return env


async def parse_download(body: bytes, media_type: str, *, parser="legacy", python_executable=None,
                         artifacts_path=None, storage_path=None, max_pages=100,
                         max_characters=500000, timeout_seconds=None, ocr=False):
    started = monotonic()
    use_jats = media_type in {"application/xml", "text/xml", "application/jats+xml"}
    use_docling = parser == "docling" and (media_type == "application/pdf" or use_jats)
    if parser not in {"legacy", "docling"}:
        raise AppError(500, "parser_configuration", "문헌 해석기 설정이 올바르지 않습니다.")
    if use_jats and parser != "docling":
        raise AppError(503, "parser_configuration", "JATS XML에는 Docling 설정이 필요합니다.")
    if use_jats and ocr:
        raise AppError(422, "parser_configuration", "JATS XML에는 OCR을 적용할 수 없습니다.")
    if not body or len(body) > (20 * 1024 * 1024 if use_docling and not use_jats else MAX_BYTES):
        raise AppError(413, "source_too_large", "문헌 해석 입력의 크기 한도를 확인해 주세요.")
    if use_docling and (not python_executable or not artifacts_path):
        raise AppError(503, "parser_configuration", "Docling 실행 환경과 모델 경로를 설정해 주세요.")
    if use_docling:
        from knowledge.integrations.docling_artifacts import conversion_key, load_conversion, model_fingerprint, preserve_conversion
        try:
            model_hash = await asyncio.to_thread(model_fingerprint, artifacts_path)
            legacy_key = conversion_key(body, max_pages=max_pages, max_characters=max_characters, ocr=ocr,
                                        model_artifacts_hash=model_hash)
            key = hashlib.sha256((("runtime-quality-v4:jats:" if use_jats else "runtime-quality-v3:pdf:") + legacy_key).encode()).hexdigest()
            cached = load_conversion(storage_path, key, body) if storage_path else None
        except (OSError, KeyError, TypeError, ValueError) as exc:
            raise AppError(503, "parser_artifact_invalid", "Docling 모델과 변환 보존 파일을 확인해 주세요.") from exc
        if cached is not None:
            processing = cached["metadata"]["processing"]
            processing.update(originalElapsedMs=processing["elapsedMs"], cacheHit=True,
                              elapsedMs=round((monotonic() - started) * 1000, 2))
            return cached
        try:
            legacy = load_conversion(storage_path, legacy_key, body) if storage_path and not use_jats else None
        except (OSError, KeyError, TypeError, ValueError) as exc:
            raise AppError(503, "parser_artifact_invalid", "Docling 모델과 변환 보존 파일을 확인해 주세요.") from exc
        if legacy is not None:
            from knowledge.documents.runtime_preprocessing import prepare_conversion
            result = prepare_conversion(legacy, body)
            processing = result["metadata"]["processing"]
            processing.update(originalElapsedMs=processing["elapsedMs"], cacheHit=True,
                              elapsedMs=round((monotonic() - started) * 1000, 2))
            preserve_conversion(storage_path, key, body, result)
            return result
        module, executable = ("knowledge.integrations.docling_jats" if use_jats else "knowledge.integrations.docling_parser"), python_executable
        args = ([str(Path(artifacts_path).resolve()), "--max-characters", str(max_characters)] if use_jats else
                ["--artifacts-path", str(Path(artifacts_path).resolve()), "--max-pages", str(max_pages),
                 "--max-characters", str(max_characters)] + (["--ocr"] if ocr else []))
    else:
        module, executable, args = "knowledge.integrations.parse_document", sys.executable, [media_type]
    try:
        with tempfile.TemporaryDirectory(prefix="ontology-parser-") as parser_home:
            env = _parser_environment()
            # Libraries need a home directory, but must not discover the user's saved tokens.
            env.update(USERPROFILE=parser_home, HF_HOME=str(Path(parser_home) / "huggingface"))
            stdout = await run_bounded_python(executable, module, args, input_bytes=body, env=env,
                timeout_seconds=timeout_seconds or (480 if use_docling else 12),
                cpu_seconds=600 if use_docling else 8, memory_bytes=(8 * 1024 if use_docling else 512) * 1024 * 1024,
                max_output_bytes=(32 if use_docling else 2) * 1024 * 1024)
    except TimeoutError as exc:
        raise AppError(422, "source_parse_timeout", "문헌 해석 시간이 제한을 넘었습니다.") from exc
    except BoundedProcessError as exc:
        raise AppError(422, "source_parse_failed", "문헌 본문을 추출하지 못했습니다.",
                       details={"parserFailure": exc.code}) from exc
    try:
        result = json.loads(stdout)
        if not isinstance(result["content"], str) or not result["content"].strip():
            raise ValueError("Empty extraction")
        if use_docling:
            if result["metadata"]["parserProfile"]["version"] != "2.143.0":
                raise ValueError("Unexpected parser version")
            result["metadata"]["parserProfile"]["modelArtifactsHash"] = model_hash
            result["metadata"]["processing"] = {"elapsedMs": round((monotonic() - started) * 1000, 2),
                                                   "cacheHit": False, "execution": "local_cpu"}
            from knowledge.documents.runtime_preprocessing import prepare_conversion
            result = prepare_conversion(result, body, jats=use_jats)
            if storage_path:
                preserve_conversion(storage_path, key, body, result)
        return result
    except (KeyError, TypeError, ValueError) as exc:
        raise AppError(422, "source_parse_contract", "문헌 해석 결과의 형식을 확인할 수 없습니다.") from exc
