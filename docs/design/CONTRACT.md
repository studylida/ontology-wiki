# Implementation contract — 2026-10-26

This branch implements the uploaded, executed redesign prompt against baseline
`8e7fb58bd0c051fff99ab97a39278ef2bdc5ba0a`. Legacy tab/schema restrictions are superseded
by the user's explicit redesign. Production data and deployment are untouched.

## Boundaries

Modular monolith: React/TypeScript/Vite → FastAPI → PostgreSQL/pgvector.
Frontend: View → Controller → Service → Repository → DTO. Backend:
Controller → Service → Repository → Entity/DTO. DTOs describe contracts; they are
not executable layers. Services own short transactions. No DB transaction spans
provider calls. Persistent files live in `OW_STORAGE_PATH`, not in source control.

Backend package: `backend/knowledge`. Feature packages: `identity`, `conversations`,
`rag`, `answers`, `documents`, `ontology`, `personal_wiki`, `research`, `jobs`.
Cross-cutting modules: `core` and `integrations`. Each feature owns its entity,
repository, DTO, service and router as needed; empty forwarding layers are omitted.

API prefix `/api/v1`. JSON keys are camelCase. Dates are ISO 8601 UTC. IDs are
opaque strings. Lists use `{items: [...]}`; paged lists also use `nextCursor`.
Errors use `{error: {code, message, details?, retryable}}`. Bearer tokens authenticate
both people and scoped service accounts; provider credentials are server-only.

## UI contracts

- `POST /auth/login {username,password}` → `{accessToken,user:{id,username,role,permissions}}`.
- `GET /auth/me` → user. `GET /health` reports actual database/provider configuration.
- `GET /conversations` → items `{id,title,updatedAt,autoWiki,nextSettings}`.
- `POST /conversations {title?}` → conversation.
- `GET /conversations/{id}` → `{...conversation,messages:[Message]}`.
- `PATCH /conversations/{id} {autoWiki?,title?}` → conversation.
- `POST /conversations/{id}/turns` and `POST /answer-runs` accept `AnswerRequest`.
  Return `{runId,conversationId,messageId,status,eventsUrl}` after durable creation.
- `GET /answer-runs/{id}` → durable run including partial/final `message` and `lastSeq`.
- `GET /answer-runs/{id}/events?after=0` → authenticated SSE, replay then live events.
- `POST /answer-runs/{id}/cancel` → `{runId,status}`.

`AnswerRequest = {clientRequestId, conversationId?, message, responseMode:'wiki'|'analysis',
extended:boolean, conceptIds:[], sourceRevisionIds:[], sourceGroups:[], aspect?,
attachmentIds:[], documentContextIds:[]}`. Group = `{groupId,publisherId?,sourceType?}`. Groups are requested
independently, predicates within each group are AND. Explicit revisions, groups,
active index snapshot and current authorization intersect. Settings default to wiki
and Extended=false; changing a UI toggle never sends a request.

`Message = {id,role,content,responseMode?,extended?,runId?,status,createdAt,
citations:[],relations:[],sourceViews:[],warnings:[],usage?}`. User and assistant
messages persist. Citation = `{id,sourceRevisionId,passageId,title,locator,excerpt,
publisher?,author?,sourceType?,url?}`. `locator` is a human-readable section/page
string. Relation = `{id,fromConceptId,toConceptId,fromName,toName,type,summary?,
conditions?,status,evidence:[Citation]}`. SourceView = `{id,conceptId,sourceRevisionId,
publisher?,publisherId?,author?,attributedTo?,attributionBasis,sourceType,aspect,
summary,conditions?,publishedAt?,status,evidence:[Citation]}`.

Every SSE envelope is `{type,runId,seq,at,data}`; SSE `id` is seq, `event` is type,
`data` is the entire envelope. Types:
`run.started`, `retrieval.status`, `text.delta`, `citation.add`, `relation.add`,
`source_view.add`, `run.completed`, `run.failed`, `run.cancelled`.
`text.delta.data={text}`; `.add.data` is the card/citation object.
`retrieval.status.data={stage,message,retrievalRunId?,indexSnapshotId?,groupCoverage?,warnings?}`.
Terminal data includes `{status,messageId,usage,warnings?,error?}`. `run.completed`
is emitted only after final answer commit. Reconnect does not start a new run.
Unknown token counts/costs are null, never synthesized zero. Fixture runs are visibly
labelled and may not be presented as a live-provider success.

Wiki response order: core explanation; purpose/principle; examples/conditions
(including source-view cards); relations; sources/gaps. Relation expand is local.
Explicit followup prepares/sends a distinct request without destroying a draft.

## Documents and review

- `GET /documents?reviewStatus=pending|approved|rejected|held|withdrawn` → list of
  `{id,title,currentRevisionId,reviewStatus,indexStatus,publisher?,sourceType?,url?}`.
- `POST /documents {title,content,format:'markdown'|'text',url?,publisher?,publisherId?,
  author?,attributedTo?,attributionBasis?,sourceType?,visibility:'private'|'shared_candidate'}`
  → document with revision. Text upload is V1; raw binary import is CLI/URL fetch.
- `GET /documents/revisions/{id}` → `{id,documentId,title,content,metadata,reviewStatus,
  indexStatus,passages:[{id,ordinal,text,locator}],readScope}` under current permission.
- `POST /documents/revisions/{id}/review {decision:'approve'|'reject'|'hold'|'withdraw',reason}`.
- `PATCH /documents/revisions/{id}/metadata {publisher?,publisherId?,author?,attributedTo?,
  attributionBasis?,sourceType?,publishedAt?}` invalidates derived attribution.
- `POST /index-jobs {sourceRevisionIds:[],immediate:true}` → job list, reviewer only.
- `GET /jobs?kind?` → caller-visible jobs with actual progress/status/error.

Daily incremental document indexing; explicit immediate jobs use identical code.
Unchanged input hash/profile/scope reuses vectors. Revocation is immediate. New
revision activates atomically after all embeddings and a final permission check.

## Ontology and retrieval

- `POST /retrieval/search` accepts AnswerRequest search fields (message mandatory).
- `GET /ontology/concepts?q=&cursor=&limit=` → items `{id,name,description?,aliases,type,revision}`.
- `GET /ontology/concepts/{id}` → concept.
- `GET /ontology/concepts/{id}/relations` → relation list.
- `GET /ontology/concepts/{id}/source-views?publisherId=&sourceType=&aspect=&dateFrom=&dateTo=&cursor=&limit=`.
These GETs never call models. Concept source views derive only from approved public
documents and canonical concept/aspect. Private chat text cannot enter their jobs.
Other projects use scoped service credentials and the same application services.

## Private wiki

- `GET /personal-wiki?q=` → pages `{id,title,summary,version,updatedAt}`.
- `GET /personal-wiki/{id}` → `{...page,content,versions:[],originMessages:[],citations:[]}`.
- `PATCH /personal-wiki/{id} {title?,content?,expectedVersion}`.
- `DELETE /personal-wiki/{id}` suppresses repeat generation from its source messages.
- `POST /personal-wiki/{id}/undo {expectedVersion}`.
- `GET /personal-wiki/settings` → `{autoOrganize:boolean,defaultIsAssumption:true}`.
- `PATCH /personal-wiki/settings {autoOrganize}`.
- `POST /personal-wiki/organize {messageId,explicit:false}` queues idempotent work.
Completed answers queue automatic work if enabled. Saving rechecks current consent,
source access, answer completion and expected page version. No shared promotion.

## External research

- `POST /research/search {query,conversationId?,limit?}` → `{items:[],warnings:[]}`.
  Explicit bounded single query to configured literature provider; no autonomous loop.
- `POST /research/fetch {url,query?,conversationId?}` → card with actual read scope.
- `POST /research/transfer {conversationId,items:[{id}],query,conditions?}` →
  `{attachmentIds,submittedDocumentIds,warnings}`. Never starts answer generation.
Card = `{id,title,url,publisher?,author?,publishedAt?,readScope:'metadata'|'abstract'|'full'|'partial',
content?,relevance?,limitations:[],status}`. Private attachments stay private;
selected accessible public literature may enter document review (documented assumption).

## Ownership during implementation

- Backend author: core/identity/conversations/rag/answers/main and their tests.
- Root: integrations/documents/ontology/personal_wiki/research/jobs, CLI/import/migration.
- Frontend author: frontend only and frontend-specific notes/tests.
- Runtime author: isolated test PostgreSQL/browser tooling, later infrastructure tests/docs.

Root owns cross-module integration. Interface changes must be communicated before
silently adapting one side. Each feature router exposes `router`, each service
accepts a SQLAlchemy session factory or small integration ports through composition.

### Explicit review context refinement

`sourceRevisionIds` strictly narrows the approved active shared snapshot. Review
questions use a separate `documentContextIds` list for explicitly selected source
excerpts, checked against current reviewer/owner access. These sources do not enter
the shared index or public extraction inputs. This distinction also applies to
private attachments.
