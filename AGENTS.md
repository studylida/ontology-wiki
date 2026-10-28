# Working on Ontology Wiki — target service redesign

## Source of truth and scope

Read `README.md` and `docs/ARCHITECTURE.md` first. The architecture is the future target, not a claim that every stage is implemented. The source-preserving preprocessing baseline is `68ccd5f3bc98abd480d5a413947974aa02843a66`; continue the implementation branch rather than resetting to an old baseline.

The product has one user-facing job: answer work questions using company-domain documents, with natural phrasing and clickable evidence footnotes. Every authenticated employee may upload material suitable for company-wide sharing. Valid passages are indexed automatically without an approval gate. Conversations remain private. Operations handle failures, held passages, reprocessing and deactivation.

Removed from the target: external research workflow, forced five-part answers, response modes, Extended, personal wiki and old-answer compatibility. Do not restore old schema fields to make obsolete tests green. Ontology and diagrams are optional, not answer prerequisites.

## Current implementation boundary: Stages 1 and 2

`knowledge.main` composes Identity, Conversations and Documents. v3 `001_foundation.sql` creates users/conversations/messages; additive `002_documents.sql` creates shared documents/revisions/passages/vectors/jobs. Do not rewrite applied migrations. Startup checks the schema without migration, account creation, provider calls or worker startup.

`POST /conversations/{id}/messages` only persists a user message. Stage 3 will connect RAG/answers; Stage 4 the frontend. Their reusable source and old test files remain temporarily but are not loaded by the current app.

Use `scripts/v2/dev.py migrate|create-user|serve|worker|test`. Explicit process environment overrides `.env`. API and worker must share `OW_DATABASE_URL` and persistent `OW_STORAGE_PATH`. The worker is a separate process. `--once` consumes one pending document job. A DB advisory lock serializes workers; an interrupted job becomes a visible failure on restart and needs explicit retry.

Uploads are open to employees. Updating, retrying or deactivating an existing shared document requires its uploader or admin, centralized in DocumentRepository. This is not a registration approval gate. Deactivation cannot be undone by a worker completion or retry. Revision activation is atomic after all usable passages have vectors; failed newer revisions retain the earlier usable active revision.

`IndexUnit` is a small internal input contract, not a new persistent knowledge table. Indexing owns preprocessing-to-vector-to-activation coordination, Jobs owns queue execution/retries, Documents owns immutable source files and revision/visibility policy. Existing `parsing`, `preprocessing`, `runtime_preprocessing`, bounded processes, provider adapters and retrieval ranking are reused. File conversion lives in `integrations/document_parser.py`, independently of URL fetching. Old jobs/indexing, jobs/router and jobs/service have been removed; do not recreate duplicate implementations.

Completed/partial-ready jobs are not re-enqueued by `reprocess`; failed jobs retry with successful parsed data and embeddings reused. Full correction editors and forced re-extraction of ready revisions are outside this stage. Source changes use a new revision.

## Verification

`tests/foundation` uses real PostgreSQL, HTTP, file storage and Uvicorn/worker processes, with deterministic fixture embeddings only. It covers private ownership, restart persistence, shared upload, valid/held passages, indexing, deduplication, revision replacement/failure, withdrawal and worker interruption. PDF text extraction uses the actual bounded pypdf path. Structured preprocessing and JATS routing tests use explicit fixtures, not actual Docling model execution. The existing `shared-assistant.yml` runs the suite. Old complete backend tests/frontend are not yet ported; update those when their capability is migrated rather than claiming they already pass.

No live model call or business-usefulness evaluation has been performed. Do not confuse saved fixture vectors with semantic retrieval quality. Do not silently substitute a different model, parser or database.

## Architecture and robustness

- Backend: Controller / Service / Repository / Entity / DTO. Frontend: View / Controller / Service / Repository / DTO. Organize by business capability; avoid empty forwarding layers.
- Keep single owners for source access/activation, preprocessing, embedding, search/context budgets, answers, citations, jobs, HTTP/SSE and provider calls. Do not accumulate unrelated logic in one utils/service module.
- Use the existing modular monolith and PostgreSQL/pgvector. Do not add graph databases, brokers, agent frameworks or speculative extraction tables.
- Old wiki/analysis rows and legacy FK mappings need no migration. Git history restores tracked code, not actual raw files, credentials or DB rows.
- Fail closed for unauthorized or corrupt sources, fail soft for independent valid passages and optional features. Never fabricate company facts, citations or success states.
- Preserve raw PDF/XML/Markdown separately from extracted/normalized artifacts. Keep uncertain tables/formula passages held rather than quietly indexing them.
- Normal GET requests do not invoke models, start jobs or mutate activation.

## Work boundaries

Use isolated dev/test databases. Do not delete or alter production/shared data or another worker's uncommitted changes. Push only the requested implementation branch, without force, main merge or deployment. Remove dead paths as their capabilities are ported. Keep `docs/ARCHITECTURE.md` as the sole design document; do not add per-run reports or sensitive execution dumps to docs.
