# Working on Ontology Wiki — target service redesign

## Source of truth and scope

Read `README.md` and `docs/ARCHITECTURE.md` first. The latter is the **future target architecture**, not a description of completed implementation. Compare current code against the `68ccd5f3bc98abd480d5a413947974aa02843a66` baseline and subsequent explicitly integrated work. Do not treat the old feature set as requirements.

The product has **one user-facing job**: answer employees' work questions using company-domain documents, with natural phrasing and optional, clickable evidence footnotes. Every authenticated employee may upload material suitable for company-wide sharing; valid passages are indexed automatically, without an administrator approval gate. Personal conversation history remains private. A separate operating area handles processing failures, held passages, reprocessing and deactivation.

Removed from the new product: external research workflow, forced five-part wiki answers, response-mode switch, Extended mode, personal wiki pages/auto-organize, and old wiki/analysis answer compatibility. Do not build migration adapters or keep old entities merely to recover their old saved responses. Ontology extraction is optional admin-side enrichment, not a prerequisite for answers. Diagram rendering is noncritical and may be omitted or gracefully disabled.

## Current implementation boundary: Stage 1

`knowledge.main` composes only Identity and Conversations. The v3 foundation migration creates users, conversations and messages. Starting the API checks the schema; it never creates accounts, migrates the DB, invokes a model or starts a worker. `POST /conversations/{id}/messages` stores a user message only, not a fabricated assistant response.

Use `scripts/v2/dev.py migrate`, `create-user`, `serve`, and `test`. Explicit process environment overrides `.env`. `tests/foundation` starts real Uvicorn processes against isolated PostgreSQL databases and tests persistence after process restart. The existing `shared-assistant.yml` workflow runs this suite. No live model evaluation is performed in Stage 1.

Stage 2 adds document upload/processing/indexing; Stage 3 connects RAG/answers; Stage 4 connects the frontend. Their reusable source and old test files temporarily remain in the repository but are NOT loaded by the Stage 1 app/registry/CLI. Do not claim the old full backend suite or old frontend works against the new contracts. Update relevant tests as each capability is ported; do not restore deprecated schema fields merely to keep old tests green. Do not start the old worker directly against the v3 database.

Append future schema changes to `backend/migrations/v3/`. Do not rewrite the applied foundation migration. The v2 schema/import tools are not a compatibility path. Existing raw files and databases have not been removed by this implementation.

## Architecture

- Backend five-layer responsibilities: Controller (API/SSE), Service (use-case orchestration), Repository (DB/access-filtered queries), Entity (minimum durable model), DTO (contracts). Organize by business capability; don't scatter the same rule across five copies.
- Frontend five-layer responsibilities: View (render), Controller (interaction and state orchestration), Service (pure shared transformations), Repository (HTTP/SSE/browser I/O), DTO (types).
- Maintain single owners for access authorization, source/passage lookup, RAG search, answer lifecycle, citation IDs and UI numbering, job scheduling, provider adapters, and document preprocessing.
- Prefer a modular monolith, PostgreSQL + pgvector, existing streaming/reconnect foundations and functional extraction assets. Avoid graph databases, agent frameworks, queue services, extra tables and indirection without demonstrated benefit.
- A fresh database baseline is permitted for the redesigned service; **there is no requirement to preserve the old wiki/analysis messages, legacy foreign keys, personal wiki tables, or import/mapping tables**.
- Git history can restore tracked source code/docs, **not** live DB rows, raw files, provider secrets or local model caches.

## Robustness: resilient rather than rigid

- Access control, actual evidence origin, source revision identity and approved data handling are hard constraints.
- A parser/embedding/ontology/diagram issue should not invalidate independent valid documents or a grounded partial answer. Preserve valid evidence and state the missing portion. Don't fabricate internal knowledge.
- Fail closed for unauthorized data; fail soft for optional processing. Treat missing evidence, schema mismatch, source corruption and provider failure as distinct cases rather than a universal fatal error.
- Keep original Markdown/PDF/XML and reviewed correction lineage separate from derived snippets. Preprocessing in `knowledge.documents.preprocessing` / `knowledge.documents.runtime_preprocessing` marks uncertain tables, formula display and unresolved locations for review. Do not quietly index suspect passages.
- Do not automatically run generation, indexing or admin changes as a side effect of ordinary GET or a UI toggle. Use meaningful tests instead of claiming total accuracy from mocks.

## Work boundaries

- Work in an isolated feature branch and an explicitly disposable dev/test database. Do not touch a production DB or shared raw-data volume unless the actual target and scope have been explicitly verified and authorized.
- Dropping old schemas is a design option, not an implicit permission to delete unknown current DB instances. There is no DB cleanup performed by a docs-only commit.
- When redesigning, remove dead paths after ensuring no active caller remains. Maintain the smallest useful regression suite for core user question → RAG → answer → citation → follow-up, plus access/partial-failure cases.
- Historical reports under `docs/` were intentionally removed to reduce confusion. Git history remains available. Only the new target architecture is a current design source; update it when a new decision is actually made, not for every experiment.
