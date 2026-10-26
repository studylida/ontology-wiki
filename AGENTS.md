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

Windows process management belongs to `scripts/v2/windows_dev.ps1`; it starts the existing API/worker/Vite entry points and manages only its recorded local processes. See `docs/WINDOWS_LOCAL.md` for this environment; application layer boundaries remain unchanged.

Offline corpus review uses `scripts/v2/curate_existing_corpus.py` with a hash-checked input manifest and private run-specific rules under `var/corpus-quality/`. It writes only a fresh review run and does not register, approve, or index product data. See `docs/CORPUS_QUALITY_REPORT_20261027.md` for the run and its limitations.

Update API/schema migrations and relevant docs when contracts change. Keep frozen
applied migrations immutable; add a new migration. Explain what changed, why,
verified behavior and remaining limits. Keep a stable runId/debugging path. Do not
call a model or change data as a side effect of GET or a UI toggle.
