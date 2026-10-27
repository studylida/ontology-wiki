# Working on the conversation knowledge service

The user explicitly authorized the 2026-10-26 redesign and supplied the executable
implementation prompt. Legacy four-tab, Local/Global, wiki-editor schema and
no-test restrictions were superseded by that instruction. This file describes the
implemented product; historical designs are retained under `docs/legacy/`.

## Start here

Read README.md, docs/ARCHITECTURE.md, docs/API.md, docs/DECISIONS.md and the relevant
feature notes. The baseline is `8e7fb58bd0c051fff99ab97a39278ef2bdc5ba0a`. Do not
restore old runtime modules as compatibility wrappers. Preserve source data,
provenance and audit history independently of code preservation.

## Boundaries

- Frontend: View → Controller → Service → Repository → DTO contracts. Keep network
  and browser storage I/O in repositories, interaction state in controllers,
  reusable transformations in services and presentation in views.
- Backend: Controller → Service → Repository → Entity/DTO. Services own short
  transactions; do not hold transactions across provider/network calls.
- Keep a modular monolith. Introduce an abstraction when there is an actual
  replaceable integration or reused policy, not to add forwarding methods.
- PostgreSQL + pgvector and persistent raw-file storage are required. No silent
  SQLite, memory, local-model or fixture fallback in live operation.

## Product invariants

- New conversation: wiki mode and Extended off. These are independent next-request
  settings. Toggling never invokes retrieval, embedding or generation.
- Response formatting, evidence scope, model/effort and permissions are independent.
- Basic retrieval can use multiple documents. Extended searches only authorized
  internal evidence with explicit bounds; external research requires user action.
- Relation expansion is local. Concept explanation is an explicit followup.
- Personal wiki is private AI organization. It is not a public evidence source.
- Review applies to document versions, not every answer/claim/wiki edit.
- Preserve publisher/author/attributed-to distinctions and source conditions.
- No unsupported fact, fabricated citation, completion, cost or success status.
- Source lineage validation is distinct from semantic correctness evaluation.

## Safety and data

Keep user changes and all existing data intact. Work in an isolated branch and
separate development/test database unless the user explicitly authorizes another
scope. This implementation does not authorize production deployment, destructive
cutover, deletion of original sources, or operations on a production database.

Credentials belong in private environment files or a secret store. Never put
provider keys in browser storage, DTOs, logs, examples, fixtures or Git. Service
accounts do not inherit personal wiki access. Current source authorization applies
to retrieval, derived cards, old answers, wiki and event replay.

## Verification

Use meaningful contract, state, permission and PostgreSQL integration tests.
Backend tests create isolated schemas using schema_translate_map. Never run tests
against production. Frontend `npm test` and `npm run build` check the new contracts.
Live provider evaluation is separate from fake/fixture mechanics testing and must
remain within the user's authorized account/data/cost scope.

Animations must refer to actual https://transitions.dev/ patterns, support reduced
motion and keyboard interaction, and never manufacture progress or typing delays.

## Handoff

Offline preprocessing is owned by `knowledge.documents.preprocessing` and
`scripts/v2/preprocess_documents.py`. It reads hash-pinned local originals and
existing Docling artifacts, writes a fresh immutable review bundle, and never
registers, approves, embeds, indexes, or activates service data. Paragraph/table
boundaries, raw XML nodes, extraction offsets and editorial notes remain separate.
See `docs/PREPROCESSING_QUALITY_20261027.md` for verification and remaining limits.

Runtime Docling PDF/JATS conversion passes through `documents.runtime_preprocessing`
before `DocumentRepository` stores prepared passages. Structural or formula quality
holds use the existing excluded-passage state; only explicitly reviewed edited
revisions can release their edit hold. Markdown segmentation preserves block and
source offsets. Unique XML evidence locations are retained in the source map;
uncertain locations and original files are never replaced. JATS math conversion
retains original MathML when layout is unsupported; unique formula hashes can
link source paragraphs without guessing. Unique titled JATS notes retain their
parent context; ambiguous notes and math whose Markdown display is unsafe are
held for review. Legacy extraction and
previously indexed content are outside this runtime quality gate. See
`docs/PREPROCESSING_RUNTIME_VALIDATION_20261027.md` for scoped checks.

Windows process management belongs to `scripts/v2/windows_dev.ps1`; it starts the existing API/worker/Vite entry points and manages only its recorded local processes. See `docs/WINDOWS_LOCAL.md` for this environment; application layer boundaries remain unchanged.

Offline corpus review uses `scripts/v2/curate_existing_corpus.py` with a hash-checked input manifest and private run-specific rules under `var/corpus-quality/`. It writes only a fresh review run and does not register, approve, or index product data. See `docs/CORPUS_QUALITY_REPORT_20261027.md` for the run and its limitations.

Docling owns structured extraction, the retrieval service merges vector/text query candidates and reranks them with a local CrossEncoder, and RAGChecker runs offline. Original sources and immutable revisions remain owned by the document service. Explicit local parser/reranker runtimes are authorized; they are not silent generation or embedding fallbacks.

The retrieval service also attaches bounded experiment-method and explicit discrepancy-note candidates from the same verified source lineage, and compares relation evidence with direct hits using the local reranker before generation. These are relative retrieval signals, not automatic proof of relevance or numerical contradiction. See `docs/ARCHITECTURE.md`; preserve source text, source forms and history.

Principle questions also rerank a bounded broader candidate pool for an additional distinct-source mechanism passage. Complex comparisons use a separate provider review to map requested aspects to candidate facts and citation IDs before the streamed answer; validate IDs and retain all original evidence. It adds latency and provider cost and is not a factuality guarantee; failure is reported and falls back to the original evidence.

LightRAG was removed at the user's explicit request on 2026-10-27 after the isolated 8-document/94-passage comparison found identical final grounding and model prompts for both questions. Its integration, build code, dependency and runtime settings are removed, and its dedicated database was dropped. File deletion was blocked by automatic approval policy: graph files, the isolated PoC runtime/stores/script and four compiled cache files remain unreferenced. Do not bypass that rejection; see `docs/LIGHTRAG_REMOVAL_20261027.md`. Preserve source documents, versions, normal vectors and comparison/cost records. `docs/RAG_LIGHTRAG_SUBSET_COMPARISON_20261027.md` records the decision. Older checkpoint/research documents describe history and do not authorize reinstalling or resuming the graph build.

Update API/schema migrations and relevant docs when contracts change. Keep frozen
applied migrations immutable; add a new migration. Explain what changed, why,
verified behavior and remaining limits. Keep a stable runId/debugging path. Do not
call a model or change data as a side effect of GET or a UI toggle.
