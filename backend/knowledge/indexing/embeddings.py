"""Reusable IndexUnit-to-embedding boundary. No database transaction during I/O."""
import math
from ..core.errors import AppError


def validate_vectors(vectors, count):
    if len(vectors) != count:
        raise AppError(502, 'invalid_embedding', '임베딩 결과와 입력 개수가 다릅니다.')
    for vector in vectors:
        if len(vector) != 1536 or any(type(v) not in (int, float) or not math.isfinite(v) for v in vector) or not any(vector):
            raise AppError(502, 'invalid_embedding', '임베딩 벡터의 차원 또는 값이 유효하지 않습니다.')


async def embed_uncached(client, units, cached):
    missing = {unit.input_hash: unit.text for unit in units if unit.input_hash not in cached}
    if not missing:
        return {}, None
    response = await client.embed(list(missing.values()))
    validate_vectors(response.vectors, len(missing))
    return dict(zip(missing, response.vectors, strict=True)), response.usage
