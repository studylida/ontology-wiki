# Working on Ontology Wiki — target service redesign

## Source of truth

Read README.md for the implemented chat/RAG. **docs/CHAT_ARCHITECTURE.md governs the implemented conversation, shared document ingestion and RAG design. docs/WIKI_ARCHITECTURE.md independently governs the new shared concept wiki's product architecture (currently planned, not implemented).** Do not apply removed personal-wiki features, legacy ontology flows or historical chat-only decisions as constraints on the new wiki. Neither product agreement nor old implementation plans imply that a new feature is live. Keep the source-preserving preprocessing baseline `68ccd5f3bc98abd480d5a413947974aa02843a66`. Continue the implementation branch, not an old baseline.

Current chat/RAG job: answer work questions using shared company-domain documents, naturally, with clickable evidence footnotes. Every authenticated employee may upload shareable material. Valid passages are indexed automatically without approval. Conversations and answer runs stay private. Operations handle processing exceptions, not mandatory approval.

Removed from the **current chat runtime**: external research, fixed five-part answers, response modes, Extended, old personal wiki and legacy answer compatibility. This does not prohibit the newly agreed **shared concept wiki**, which is a separate product scope; it is not yet implemented. Ontology generation and diagrams are not chat-answer prerequisites. Do not reintroduce old schema fields just to satisfy obsolete tests.

## Implemented boundary: Stages 1–5 (fixture integration, not production qualification)

`knowledge.main` composes Identity, Conversations, Documents and Answers. Additive migrations are `001_foundation.sql`, `002_documents.sql`, `003_answers.sql`. Never rewrite applied migrations. Stage 4 connects the React frontend to these contracts; Stage 5 integrates regression tests, synthetic evaluation and fresh Compose smoke checks. Neither adds a schema. The root HTML/JS prototype and retired frontend hooks, screens and contracts are removed. Run the UI from `frontend`.

The API requires one process per DB (`--workers 1`), enforced by a dedicated PostgreSQL session advisory lock. This prevents startup recovery from interrupting another live API's generation. Concurrent conversations are asynchronous within that process. The document worker is separate and uses its own lock. Do not silently remove these locks or claim multi-replica operation is implemented.

Startup checks the schema and records abandoned answer runs as interrupted. It does not migrate, create users, invoke a provider or start document processing. GET/reconnect never generates another answer. `POST /conversations/{id}/messages` saves only; the UI uses `/conversations/{id}/turns` for an actual question, not both.

## Single-owner responsibilities

- Documents owns shared visibility, active revisions and raw integrity. Upload/read is open to employees; updates/reprocess/deactivation require uploader or admin. Deactivation is not undone by a worker. The UI uses `canManage`, not a second role/approval policy.
- Preprocessing preserves structure, source offsets and held passages. `integrations/document_parser.py` separates conversion from URL fetching. Keep existing Markdown/PDF/JATS assets.
- Indexing owns the small IndexUnit contract, reusable vectors and atomic activation; Jobs owns execution/retry. A failed new revision keeps the earlier valid active revision. Reprocess retries failed jobs, not force-reextracting ready revisions.
- DocumentRepository owns active-source retrieval SQL. RAG owns candidate selection, optional reranking, source-provided companions, neighbors and whole-passage context budgeting. No ontology dependency or Extended branch.
- Answers owns question policy, run idempotency, cancellation/retry and commit-before-publication events. `answers/prompt.py` owns generation policy; `answers/citations.py` owns normalization/numbering. A citation ID check is not semantic entailment validation.
- `conversations/protection.py` is the shared stored-answer/history policy. Withdrawal hides dependent answer content/citations and prevents replay. Replaced but readable revisions are labelled historical; their old assistant messages are not reused as current context.
- Frontend repositories own HTTP, authenticated SSE, source downloads and sessionStorage. Services own event application/reconnection and the canonical citation map. Controllers own lifecycle, cancellation and state. Views render actual server states, not invented progress or success. DTOs contain current contracts only.
- Existing provider adapters remain explicit. Never silently replace a failed live model with a fixture. No paid calls without approved account/data/budget scope.

The live runtime registry contains only current task/cancellation state. PostgreSQL holds messages, runs, retrieval diagnostics and ordered event batches. Commit the body/state/events together before exposing complete. Storage errors are not successful answers. Read run body and durable cursor under the same short DB lock; do not hold that lock during provider/SSE I/O. Reconnect resumes after the durable sequence; retry requires a new requestId and reuses the original user message. Same-user same-request replays return one run. Changed payloads conflict.

The browser replaces a restored body and cursor together before replaying newer events. EOF is not completion. Only explicit send/retry submits POST. Unknown POST delivery retains the original requestId for explicit resend; never invent a new ID for transport recovery. Session storage is user-scoped and does not cache answers or migrate retired drafts. Logout clears the current workspace. Body footnotes, source list and source panel use the server's numbers through `services/citationService.ts`. Markdown HTML/images are not executable/rendered; unknown IDs do not become clickable citations.

## Execution and verification

Use `scripts/v2/dev.py migrate|create-user|serve|worker|test`. Explicit environment overrides .env. API and document worker share OW_DATABASE_URL and OW_STORAGE_PATH. Token secrets must survive restarts. Source conversions use the configured local parser; missing environments fail visibly. In `frontend`, use `npm ci`, `npm run dev`, `npm run build`, `npm test`; Vite dev and preview proxy `/api` to OW_API_PROXY_TARGET (default loopback port 8000).

`tests/foundation` uses real PostgreSQL, HTTP/SSE, files, Uvicorn and worker processes. Embeddings/generation are labelled fixtures. Provider protocol tests use MockTransport. Tests cover uploads and active evidence, neighbors, actual citation mapping, follow-ups, durable replay, concurrency, cancellation/retry, process kill/restart, source withdrawal and forced storage/retrieval errors. PDF text extraction runs for real; structured Docling/JATS verification is fixture/contract based.

`tests/browser` uses actual Chromium against the built UI, real isolated DB/API/storage and a separate document worker, with explicit fixture providers. The existing shared-assistant workflow also runs frontend type/build/unit tests. Keep browser DB assertions real: the sync Playwright event loop means foundation asyncio.run DB helpers must run on a separate thread. Screenshots/JUnit artifacts use temporary CI storage, not docs. Functional browser tests are not a manual visual/accessibility audit, live model quality evaluation, or business usefulness evaluation. Review dependency security warnings independently of functional test success.

The retired backend/tests suite and v2 migrations/imports are removed. Reusable parser, source preservation, bounded-process, provider and reranking tests now live in tests/unit; current capability tests live in tests/foundation. Default dev.py test collects both plus tests/evaluation. Register the evaluation database fixture locally in its test module rather than adding a second bare conftest import that shadows foundation helpers. Browser verification runs separately. Installed Docling execution is explicitly optional under tests/optional and is not counted as passed by the default suite.

The synthetic-only evaluation corpus has 12 documents and 18 work-style questions. It reuses the real intake/worker/retrieval/answer path with fixture providers and records raw-to-passage-to-candidate-to-context-to-answer trace and observed document coverage. Do not report that coverage as semantic retrieval accuracy or label fixture generation/human usefulness as evaluated. Never tune product answers to the test questions. Outputs stay in temporary CI artifacts or ignored evaluation-output, never docs; manual-review fields remain unreviewed until a human reviews them.

The Compose smoke script uses a new random project/database/raw volume and explicit fixture providers, not an existing developer .env or credentials. Cleanup may only target resources it created. Current schema versions must not be rewritten. Old source crawler scripts and public URL fetch adapters have been removed; uploaded file parsers and existing stored source files are retained.

Optional ontology extraction/management and diagram rendering are deferred, not secretly implemented or required. Remove old incompatible extraction services rather than recreating legacy tables. A code fence is not a rendered diagram. New-revision UI and source correction editors are not yet provided.

The frontend lockfile audit found six development dependency advisories on 2026-10-28 (two critical, one high, three moderate); production-only npm audit reported zero. That is not a security certification. Keep dev/test servers private, record the unresolved tooling upgrades, and do not use audit fix --force or claim the warnings are resolved without a tested lockfile change. Real model quality, employee review and public deployment remain separate work.

## Architecture and work boundaries

Backend: Controller / Service / Repository / Entity / DTO. Frontend: View / Controller / Service / Repository / DTO. These are responsibility boundaries, not mandatory empty forwarding classes. Organize by capability; avoid duplicate rules and a giant utils/service module.

Keep the modular monolith, PostgreSQL/pgvector and existing provider interfaces. Do not add brokers, graph databases, agent frameworks, speculative extracted-knowledge tables or approval workflows. Fail closed for unauthorized/corrupt sources and fail soft for independent valid evidence and optional refinements. General knowledge may supplement explanations but cannot invent internal facts.

Use isolated dev/test databases. No destructive production/shared DB or raw-volume operations, no secret commits, no force push, main merge or deployment. Old personal-wiki rows need no migration, but Git history does not back up raw files or DB rows. Maintain two independent architecture sources: docs/CHAT_ARCHITECTURE.md and docs/WIKI_ARCHITECTURE.md. Do not add per-run reports or sensitive dumps.
