"""Source byte access. Content-addressed writes reuse the existing atomic writer."""
import hashlib
from pathlib import Path
from ..core.errors import AppError
from .parsing import save_raw


def read_raw(storage_path: str, relative_path: str, expected_hash: str) -> bytes:
    root = Path(storage_path).resolve()
    path = (root / relative_path).resolve()
    if not path.is_relative_to(root) or path.suffix != '.bin' or path.stem != expected_hash:
        raise AppError(409, 'source_integrity', '원문 저장 경로의 무결성을 확인할 수 없습니다.')
    try:
        body = path.read_bytes()
    except OSError as exc:
        raise AppError(409, 'source_unavailable', '보존 원문을 읽을 수 없습니다.') from exc
    if hashlib.sha256(body).hexdigest() != expected_hash:
        raise AppError(409, 'source_integrity', '보존 원문의 해시가 일치하지 않습니다.')
    return body
