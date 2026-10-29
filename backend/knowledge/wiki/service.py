"""One owner for shared wiki editing, protection, version checks and replay policy."""
import difflib
import hashlib
import json
from sqlalchemy.exc import SQLAlchemyError
from ..core.errors import AppError
from .dto import (AuthorView, MutationResult, PageDetail, PageList, PageView,
                  RevisionComparison, RevisionList, RevisionSummary, RevisionView)
from .repository import WikiRepository
from .policy import can_edit, can_protect, require_edit, require_protect, require_read, require_version


def revision_view(revision, editor, *, summary=False):
    data = dict(id=revision.id, page_id=revision.page_id, number=revision.number, title=revision.title,
        change_summary=revision.change_summary, editor=AuthorView(id=editor.id, username=editor.username),
        created_at=revision.created_at, restored_from_id=revision.restored_from_id)
    return RevisionSummary(**data) if summary else RevisionView(**data, markdown=revision.markdown, source_note=revision.source_note,
        aliases=revision.aliases, meaning=revision.meaning)


def page_view(row, principal, *, detail=False):
    page, revision, creator, editor = row
    data = dict(id=page.id, title=revision.title, aliases=revision.aliases, meaning=revision.meaning, current_revision_id=revision.id,
        revision_number=revision.number, version=page.version, locked=page.is_locked,
        can_edit=can_edit(principal, page), can_protect=can_protect(principal),
        creator=AuthorView(id=creator.id, username=creator.username),
        editor=AuthorView(id=editor.id, username=editor.username), created_at=page.created_at, updated_at=page.updated_at)
    return PageDetail(**data, revision=revision_view(revision, editor)) if detail else PageView(**data)


def compare_revisions(before, after):
    changes = []
    for label, field in [('제목', 'title'), ('본문', 'markdown'), ('근거·업무 맥락', 'source_note'), ('뜻·구분', 'meaning')]:
        old, new = getattr(before, field), getattr(after, field)
        lines = list(difflib.unified_diff(old.splitlines(), new.splitlines(),
            fromfile=f'v{before.number} {label}', tofile=f'v{after.number} {label}', lineterm=''))
        if old != new and not lines:
            lines = [f'{label}: 개행 형식 또는 마지막 개행이 변경되었습니다. 각 판본의 원문을 확인하세요.']
        changes.extend(lines)
    if before.aliases != after.aliases:
        changes.extend(['별칭: ' + ', '.join(before.aliases), '→ ' + ', '.join(after.aliases)])
    return '\n'.join(changes)


class WikiService:
    def __init__(self, sessions):
        self.sessions = sessions

    async def list(self, principal, query='', limit=30, offset=0):
        require_read(principal)
        if '\x00' in query:
            raise AppError(422, 'invalid_wiki_query', '검색어를 확인해 주세요.')
        async with self.sessions() as session:
            rows, total = await WikiRepository(session).list(query, limit, offset)
            return PageList(items=[page_view(row, principal) for row in rows], total=total, limit=limit, offset=offset)

    async def get(self, principal, page_id):
        require_read(principal)
        async with self.sessions() as session:
            return page_view(await WikiRepository(session).detail(page_id), principal, detail=True)

    async def history(self, principal, page_id, limit=30, offset=0):
        require_read(principal)
        async with self.sessions() as session:
            rows, total = await WikiRepository(session).history(page_id, limit, offset)
            return RevisionList(items=[revision_view(r, u, summary=True) for r, u in rows], total=total, limit=limit, offset=offset)

    async def revision(self, principal, page_id, revision_id):
        require_read(principal)
        async with self.sessions() as session:
            return revision_view(*(await WikiRepository(session).revision(page_id, revision_id)))

    async def compare(self, principal, page_id, before_id, after_id):
        require_read(principal)
        async with self.sessions() as session:
            repo = WikiRepository(session)
            before = revision_view(*(await repo.revision(page_id, before_id)))
            after = revision_view(*(await repo.revision(page_id, after_id)))
            return RevisionComparison(before=before, after=after, diff=compare_revisions(before, after))

    async def mutate(self, principal, operation, body, page_id=None):
        require_read(principal)
        if operation in ('protect', 'deactivate'):
            require_protect(principal)
        content = body.model_dump(mode='json', exclude={'request_id'})
        # Preserve receipts for unchanged Stage-1 commands across the additive upgrade.
        # Empty optional name fields have the same meaning as their absence.
        for key in ('aliases', 'meaning'):
            if key in content and not content[key]:
                content.pop(key)
        payload = {'operation': operation, 'pageId': page_id, 'body': content}
        digest = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        try:
            async with self.sessions() as session, session.begin():
                repo = WikiRepository(session)
                old = await repo.mutation(principal.id, body.request_id)
                if old is not None:
                    if old.payload_hash != digest:
                        raise AppError(409, 'wiki_request_conflict', '같은 요청 ID에 다른 내용을 사용할 수 없습니다.')
                    return MutationResult(**{**old.result, 'replayed': True})
                if operation == 'create':
                    page = await repo.create(principal.id, body)
                else:
                    page = await repo.get(page_id, lock=True)
                    require_edit(principal, page)
                    require_version(page, body.base_version)
                    if operation == 'edit':
                        await repo.append(page, principal.id, title=body.title, markdown=body.markdown,
                            source_note=body.source_note, summary=body.change_summary, aliases=body.aliases, meaning=body.meaning)
                    elif operation == 'restore':
                        source, _ = await repo.revision(page.id, body.revision_id)
                        await repo.append(page, principal.id, title=source.title, markdown=source.markdown,
                            source_note=source.source_note, summary=f'v{source.number} 복구', aliases=source.aliases, meaning=source.meaning, restored_from=source.id)
                    elif operation == 'deactivate':
                        await repo.withdraw(page)
                    elif operation == 'protect':
                        await repo.protect(page, principal.id, body.locked)
                    else:
                        raise ValueError('Unknown wiki mutation')
                if operation not in ('protect', 'deactivate'):
                    from .index_repository import WikiIndexRepository
                    await WikiIndexRepository(session).enqueue(page)
                result = MutationResult(page_id=page.id, revision_id=page.current_revision_id, version=page.version)
                await repo.remember(principal.id, body.request_id, digest, page, result.model_dump())
                # Context-manager commit completes before a successful HTTP response can escape.
                return result
        except SQLAlchemyError as exc:
            # Rollback has completed. Do not leak SQL parameters or return success on failed commit.
            raise AppError(503, 'wiki_storage_failed', '위키 저장을 완료하지 못했습니다. 같은 요청으로 다시 확인해 주세요.', retryable=True) from exc


    async def source(self, principal, page_id, revision_id=None):
        from .dto import WikiSourceView
        from .index_repository import WikiIndexRepository
        require_read(principal)
        async with self.sessions() as session:
            repo = WikiRepository(session)
            # Short DB snapshot only. No provider or network call under this lock.
            page = await repo.get(page_id, lock=True)
            revision, editor = await repo.revision(page_id, revision_id or page.current_revision_id)
            passages = await WikiIndexRepository(session).passages(revision.id, all_passages=True)
            return WikiSourceView(page_id=page.id, revision_id=revision.id, revision_number=revision.number,
                active=page.current_revision_id == revision.id, title=revision.title, content=revision.markdown,
                source_note=revision.source_note, editor=AuthorView(id=editor.id, username=editor.username),
                created_at=revision.created_at, passages=[{
                    'id': p.id, 'ordinal': p.ordinal, 'text': p.text, 'locator': p.locator,
                    'startOffset': p.start_offset, 'endOffset': p.end_offset, 'excluded': p.excluded,
                    'exclusionReason': p.exclusion_reason} for p in passages])

    async def markdown(self, principal, page_id, revision_id=None):
        require_read(principal)
        async with self.sessions() as session:
            repo = WikiRepository(session)
            page = await repo.get(page_id, lock=True)
            return revision_view(*(await repo.revision(page_id, revision_id or page.current_revision_id)))
