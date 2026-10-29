"""Trusted source loading for document-origin proposals, not employee testimony."""
from ...core.errors import AppError
from ...documents.repository import DocumentRepository, citation_dict


async def document_context(session, principal, revision_id, passage_ids=None, *, current=True):
    repo = DocumentRepository(session)
    revision, document = await repo.revision(principal, revision_id)
    if current and (document.current_revision_id != revision_id or document.active_revision_id != revision_id
                    or revision.index_status != 'ready'):
        raise AppError(409, 'proposal_source_changed', '문헌 판본 또는 검색 상태가 바뀌었습니다. 이전 제안을 반영하지 않습니다.')
    passages = await repo.passages(revision_id)
    chosen, used = [], 0
    requested = set(passage_ids) if passage_ids is not None else None
    for passage in passages:
        if requested is not None and passage.id not in requested:
            continue
        if used + len(passage.text) > 12000:
            continue
        chosen.append({**citation_dict(passage, revision, document), 'text': passage.text})
        used += len(passage.text)
    if not chosen or (requested is not None and requested != {p['passageId'] for p in chosen}):
        raise AppError(409, 'proposal_source_unavailable', '사용 가능한 실제 원문 구간이 없어 제안을 만들 수 없습니다.')
    warnings = list(revision.limitations or [])
    if len(chosen) < len(passages) or revision.read_scope == 'partial':
        warnings.append('문헌의 사용 가능한 일부 구간만 검토했습니다. 검토하지 않은 부분의 완전성을 보장하지 않습니다.')
    return document, revision, chosen, warnings
