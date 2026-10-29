"""Read-only contextual notices. GET never starts or retries a paid task."""
from sqlalchemy.exc import SQLAlchemyError
from ...core.errors import AppError
from ...documents.repository import DocumentRepository
from ..policy import require_read
from ..proposals.service import summary
from .repository import DocumentWikiRepository


class DocumentWikiService:
    def __init__(self, sessions, settings):
        self.sessions, self.settings = sessions, settings

    async def notice(self, principal, document_id):
        require_read(principal)
        try:
            async with self.sessions() as session:
                doc = await DocumentRepository(session).get(document_id)
                if doc.withdrawn:
                    raise AppError(404, 'source_not_found', '비활성화된 문헌의 제안을 표시하지 않습니다.')
                repo = DocumentWikiRepository(session)
                job = await repo.for_revision(doc.current_revision_id)
                items = await repo.proposals(doc.current_revision_id)
                state = job.status if job else ('waiting' if self.settings.wiki_auto_proposals_enabled else 'disabled')
                if not job and self.settings.wiki_auto_proposals_enabled and doc.current_revision_id:
                    revision, _ = await DocumentRepository(session).revision(principal, doc.current_revision_id)
                    if revision.created_at < await repo.cutoff():
                        state = 'not_scheduled'
                if job and state == 'pending':
                    if not self.settings.wiki_auto_proposals_enabled:
                        state = 'paused'
                    elif await repo.daily_used() >= self.settings.wiki_auto_daily_documents:
                        state = 'budget_wait'
                return {'documentId': doc.id, 'revisionId': doc.current_revision_id,
                    'enabled': self.settings.wiki_auto_proposals_enabled, 'status': state,
                    'result': job.result if job else {}, 'error': job.error if job else None,
                    'items': [summary(p) for p in items]}
        except SQLAlchemyError as exc:
            raise AppError(503, 'wiki_suggestions_unavailable',
                '위키 제안 상태만 확인하지 못했습니다. 문헌 검색과 편집은 계속 사용할 수 있습니다.', retryable=True) from exc
