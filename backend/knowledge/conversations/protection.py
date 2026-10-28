"""One display/history policy for stored messages, run detail and replay."""
from knowledge.documents.repository import DocumentRepository
from .dto import MessageView


async def source_state(session, principal, revision_ids):
    ids = set(revision_ids or [])
    if not ids:
        return 'current'
    repository = DocumentRepository(session)
    if not await repository.ensure_readable(principal, ids):
        return 'unavailable'
    active = set(await repository.resolve_snapshot(principal, list(ids)))
    return 'current' if active == ids else 'historical'


async def visible_message(session, principal, message):
    view = MessageView.model_validate(message)
    state = await source_state(session, principal, message.source_revision_ids)
    if state == 'unavailable':
        view.content, view.citations = '', []
        view.source_unavailable = True
        view.warnings = ['이 답변의 근거가 비활성화되어 본문과 인용을 표시하지 않습니다.']
    elif state == 'historical':
        view.historical_sources = True
        view.warnings = list(dict.fromkeys([*view.warnings, '이 답변에는 현재 활성 판본이 아닌 과거 자료가 사용되었습니다. 새 질문은 현재 자료에서 검색합니다.']))
    return view
