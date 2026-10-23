"""[계층 4] Source Document Repository Layer.

Safe filesystem scanner and database operations for source documents:
- Scans sources/ directory deterministically
- Issues secure server doc_id (prevents path traversal)
- Tracks SHA-256 file hashes for change detection
- Records last_succeeded_at vs last_attempted_at and error messages
"""
import os
import re
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from backend.app.models.entities import SourceDocumentModel, PerspectiveCaseModel, EvidenceSourceModel


class SourceDocumentRepository:
    """Async database and filesystem operations for source technical whitepapers."""

    def __init__(self, sources_dir: Optional[str] = None):
        if sources_dir:
            self.sources_dir = Path(sources_dir).resolve()
        else:
            self.sources_dir = (Path(__file__).resolve().parent.parent.parent.parent / "sources").resolve()

    def generate_doc_id(self, rel_path: str) -> str:
        """Generate a safe, URL-friendly deterministic doc_id from relative file path."""
        clean = re.sub(r'[^a-zA-Z0-9]+', '-', rel_path.lower()).strip('-')
        h = hashlib.md5(rel_path.encode('utf-8')).hexdigest()[:8]
        prefix = clean[:32].rstrip('-') if clean else "source"
        return f"doc-{prefix}-{h}"

    def compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA-256 hash of file content."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    def detect_publisher(self, folder: str) -> str:
        """Map subfolder to official publisher name."""
        mapping = {
            "samsung": "Samsung Semiconductor",
            "skhynix": "SK hynix",
            "asml": "ASML",
            "lam_research": "Lam Research",
            "amat": "Applied Materials",
            "semi": "SEMI",
            "research_institutes": "imec / IEEE / NIST"
        }
        return mapping.get(folder.lower(), folder.capitalize())

    def extract_title_and_metadata(self, file_path: Path) -> Tuple[str, str, Optional[str]]:
        """Extract title from markdown frontmatter or H1/filename."""
        file_path = file_path.resolve()
        if not file_path.is_relative_to(self.sources_dir):
            raise PermissionError("문서 경로가 sources 디렉터리를 벗어납니다.")
        publisher = self.detect_publisher(file_path.parent.name)
        title = file_path.stem.replace("_", " ").title()
        source_url = None

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read(2048)

            # 1. Frontmatter
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    for line in parts[1].splitlines():
                        if line.startswith("title:"):
                            raw_t = line.split(":", 1)[1].strip().strip('"').strip("'")
                            if raw_t:
                                title = raw_t
                        elif line.startswith("publisher:"):
                            raw_p = line.split(":", 1)[1].strip().strip('"').strip("'")
                            if raw_p:
                                publisher = raw_p
                        elif line.startswith("source_url:"):
                            candidate = line.split(":", 1)[1].strip().strip('"').strip("'")
                            if candidate.startswith(("https://", "http://")):
                                source_url = candidate
                    return title, publisher, source_url

            # 2. H1 Markdown Title
            h1_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
            if h1_match:
                title = h1_match.group(1).strip()
        except Exception:
            pass

        return title, publisher, source_url

    async def sync_and_list_documents(self, session: AsyncSession) -> List[SourceDocumentModel]:
        """Scan sources/ on disk, upsert new/modified files, and return complete document list."""
        if not self.sources_dir.exists():
            return []

        # Find all .md files in sources/
        md_files = list(self.sources_dir.glob("**/*.md"))

        # Load existing DB records
        stmt = select(SourceDocumentModel)
        res = await session.execute(stmt)
        existing_list = list(res.scalars().all())
        existing_by_path: Dict[str, SourceDocumentModel] = {d.file_path: d for d in existing_list}
        existing_by_id: Dict[str, SourceDocumentModel] = {d.doc_id: d for d in existing_list}

        for file_path in md_files:
            try:
                rel_path = file_path.relative_to(self.sources_dir).as_posix()
                # Skip helper scripts or temporary files
                if file_path.name.startswith((".", "_")) or "tmp" in rel_path:
                    continue

                file_hash = self.compute_file_hash(file_path)
                title, publisher, _ = self.extract_title_and_metadata(file_path)
                doc_id = self.generate_doc_id(rel_path)

                if rel_path in existing_by_path:
                    doc = existing_by_path[rel_path]
                    # Update file_hash and title if changed
                    doc.file_hash = file_hash
                    doc.title = title
                    doc.publisher = publisher
                elif doc_id in existing_by_id:
                    doc = existing_by_id[doc_id]
                    doc.file_path = rel_path
                    doc.file_hash = file_hash
                    doc.title = title
                    doc.publisher = publisher
                else:
                    new_doc = SourceDocumentModel(
                        doc_id=doc_id,
                        file_path=rel_path,
                        publisher=publisher,
                        title=title,
                        file_hash=file_hash,
                        attempt_status="never_attempted"
                    )
                    session.add(new_doc)
                    existing_by_path[rel_path] = new_doc
                    existing_by_id[doc_id] = new_doc
            except Exception as e:
                continue

        await session.commit()

        return await self.list_documents(session)

    async def list_documents(self, session: AsyncSession) -> List[SourceDocumentModel]:
        """Read the same catalog order without scanning files or changing metadata."""
        stmt = select(SourceDocumentModel).order_by(SourceDocumentModel.publisher.asc(), SourceDocumentModel.file_path.asc())
        res = await session.execute(stmt)
        return list(res.scalars().all())

    async def get_by_doc_id(self, session: AsyncSession, doc_id: str) -> Optional[SourceDocumentModel]:
        """Fetch document model by doc_id."""
        stmt = select(SourceDocumentModel).where(SourceDocumentModel.doc_id == doc_id)
        res = await session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_perspective_cases(self, session: AsyncSession, concept_id: str):
        result = await session.execute(select(PerspectiveCaseModel).where(PerspectiveCaseModel.concept_id == concept_id))
        cases=list(result.scalars().all())
        public=await self.public_case_ids(session,concept_id,cases)
        for case in cases:case.review_is_public=case.id in public
        return cases

    async def public_case_ids(self, session, concept_id, cases):
        if not cases:
            return set()
        # Public intent comes from an approved ticket or an unchanged applied source snapshot.
        import json
        from backend.app.models.entities import ReviewTicketModel
        tickets=(await session.execute(select(ReviewTicketModel).where(ReviewTicketModel.concept_id==concept_id,ReviewTicketModel.status=='approved').order_by(ReviewTicketModel.approved_at.desc(),ReviewTicketModel.ticket_version.desc()))).scalars().all()
        def facts(narrative,caution,specs):return json.dumps([narrative,caution,[{k:v for k,v in row.items() if k!='editorId'} for row in specs]],sort_keys=True,ensure_ascii=False)
        current={c.id:facts(c.context_narrative,c.caution,c.specifications or []) for c in cases}
        seen=set();public=set()
        for ticket in tickets:
            draft=next((p.get('value',{}) for p in ticket.structured_patches or [] if isinstance(p,dict) and p.get('path')=='/workingDraft'),{})
            for case in draft.get('state',{}).get('perspectiveCases',[]):
                if case['id'] in seen:continue
                seen.add(case['id'])
                if case.get('isPublic') and current.get(case['id'])==facts(case['narrative'],case['caution'],case['specifications']):public.add(case['id'])
        by_id={case.id:case for case in cases}
        evidence_ids={case.evidence_id for case in cases if case.evidence_id}
        evidence=(await session.execute(select(EvidenceSourceModel).where(EvidenceSourceModel.id.in_(evidence_ids)))).scalars().all() if evidence_ids else []
        # These are the published-source records created by source application, not legacy attachments.
        published={e.id:e for e in evidence if e.source_type=='source_document' and e.credibility_tier=='원문 자료'}
        paths={e.section_context for e in published.values()}
        documents=(await session.execute(select(SourceDocumentModel).where(SourceDocumentModel.last_applied_at.is_not(None),SourceDocumentModel.file_path.in_(paths)))).scalars().all() if paths else []
        for document in documents:
            for item in document.last_preview_payload or []:
                if item.get('conceptId')!=concept_id:continue
                for case_id,prior in (item.get('_appliedCases') or {}).items():
                    case=by_id.get(case_id)
                    if case is None or case_id in seen:continue
                    source=published.get(case.evidence_id)
                    if source is not None and source.section_context==document.file_path and case.perspective_title==prior['perspectiveTitle'] and case.perspective_badge==prior['perspectiveBadge'] and current[case_id]==facts(prior['narrative'],prior['caution'],prior['specifications']):
                        public.add(case_id)
        return public

    async def save_perspective_cases(self, session: AsyncSession, concept_id: str, cases):
        for case in cases:
            entity = await session.get(PerspectiveCaseModel, case["id"])
            if entity is not None and entity.concept_id != concept_id:
                raise ValueError('다른 개념의 사례를 수정할 수 없습니다.')
            if entity is None:
                entity = PerspectiveCaseModel(id=case["id"], concept_id=concept_id, perspective_id=case["id"][:32])
                session.add(entity)
            entity.perspective_title = case["perspectiveTitle"]
            entity.perspective_badge = case["perspectiveBadge"]
            entity.context_narrative = case["narrative"]
            entity.specifications = case["specifications"]
            entity.caution = case["caution"]
            entity.evidence_id = case["evidenceId"]

    def resolve_safe_file_path(self, doc: SourceDocumentModel) -> Path:
        """Resolve physical Path and guarantee it resides strictly inside sources/."""
        resolved = (self.sources_dir / doc.file_path).resolve()
        if not resolved.is_relative_to(self.sources_dir):
            raise PermissionError(f"Security Violation: Path {resolved} escapes sources directory!")
        if not resolved.exists():
            raise FileNotFoundError(f"Source file {resolved} not found on disk!")
        return resolved

    async def update_attempt(
        self, session: AsyncSession, doc_id: str, status: str, error_message: Optional[str] = None
    ):
        """Update recent attempt status and timestamp."""
        stmt = (
            update(SourceDocumentModel)
            .where(SourceDocumentModel.doc_id == doc_id)
            .values(
                last_attempted_at=datetime.utcnow(),
                attempt_status=status,
                last_error_message=error_message,
                updated_at=datetime.utcnow()
            )
        )
        await session.execute(stmt)
        await session.commit()

    async def update_success(
        self,
        session: AsyncSession,
        doc_id: str,
        current_hash: str,
        concepts_count: int,
        relations_count: int,
        preview_payload: Optional[Dict[str, Any]] = None
    ):
        """Record successful extraction and save preview payload for admin review."""
        stmt = (
            update(SourceDocumentModel)
            .where(SourceDocumentModel.doc_id == doc_id)
            .values(
                last_succeeded_at=datetime.utcnow(),
                last_succeeded_hash=current_hash,
                attempt_status="success",
                extracted_concepts_count=concepts_count,
                extracted_relations_count=relations_count,
                last_preview_payload=preview_payload,
                last_error_message=None,
                is_applied=False,
                updated_at=datetime.utcnow()
            )
        )
        await session.execute(stmt)
        await session.commit()

    async def get_documents_with_applied_history(self, session: AsyncSession):
        result = await session.execute(select(SourceDocumentModel).where(SourceDocumentModel.last_applied_at.is_not(None)))
        return result.scalars().all()

    async def mark_applied(self, session: AsyncSession, doc_id: str):
        """Mark document extraction as officially applied to the Wiki."""
        stmt = (
            update(SourceDocumentModel)
            .where(SourceDocumentModel.doc_id == doc_id)
            .values(
                is_applied=True,
                last_applied_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
        )
        await session.execute(stmt)


source_repo = SourceDocumentRepository()
