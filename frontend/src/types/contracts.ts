/** Public API DTOs. See docs/design/CONTRACT.md; these are contracts, not an execution layer. */
export type ResponseMode = "wiki" | "analysis";
export type RunStatus =
  "queued" | "running" | "completed" | "failed" | "cancelled" | "interrupted";
export interface ListResult<T> {
  items: T[];
  nextCursor?: string | null;
}
export interface User {
  id: string;
  username: string;
  role: string;
  permissions: string[];
}
export interface LoginResult {
  accessToken: string;
  user: User;
}
export interface SourceGroup {
  groupId: string;
  publisherId?: string;
  sourceType?: string;
}
export interface AnswerSettings {
  responseMode: ResponseMode;
  extended: boolean;
  conceptIds: string[];
  sourceRevisionIds: string[];
  documentContextIds: string[];
  sourceGroups: SourceGroup[];
  aspect?: string | null;
  attachmentIds: string[];
}
export interface AnswerRequest extends AnswerSettings {
  clientRequestId: string;
  conversationId?: string;
  message: string;
  retryOfRunId?: string;
}
export type AnswerOverrides = Partial<AnswerSettings> & {
  retryOfRunId?: string;
};
export interface Conversation {
  id: string;
  title: string;
  updatedAt: string;
  autoWiki: boolean;
  nextSettings?: Partial<AnswerSettings>;
  messages?: Message[];
}
export interface Citation {
  id: string;
  sourceRevisionId: string;
  passageId: string;
  title: string;
  locator: string;
  excerpt: string;
  publisher?: string | null;
  publisherId?: string | null;
  author?: string | null;
  sourceType?: string | null;
  url?: string | null;
}
export interface Relation {
  id: string;
  fromConceptId: string;
  toConceptId: string;
  fromName: string;
  toName: string;
  type: string;
  summary?: string | null;
  conditions?: string | null;
  status: string;
  evidence: Citation[];
}
export interface SourceView {
  id: string;
  conceptId: string;
  sourceRevisionId: string;
  publisher?: string | null;
  publisherId?: string | null;
  author?: string | null;
  attributedTo?: string | null;
  attributionBasis: string;
  sourceType: string;
  aspect: string;
  summary: string;
  conditions?: string | null;
  publishedAt?: string | null;
  contentDate?: string | null;
  status: string;
  evidence: Citation[];
}
export interface UsageComponent {
  operation?: string;
  provider?: string | null;
  model?: string | null;
  modelSource?: string | null;
  requestedModel?: string | null;
  inputTokens?: number | null;
  outputTokens?: number | null;
  calls?: number | null;
  costUsd?: number | null;
}
export interface Usage {
  provider?: string | null;
  model?: string | null;
  requestedEffort?: string | null;
  effectiveEffort?: string | null;
  requestedServiceTier?: string | null;
  serviceTier?: string | null;
  inputTokens: number | null;
  outputTokens: number | null;
  totalTokens: number | null;
  costUsd: number | null;
  costStatus: "estimated" | "unknown" | "fixture";
  calls?: number | null;
  pricingDate?: string | null;
  source?: "provider" | "fixture";
  knownCostUsd?: number | null;
  unknownCostCalls?: number | null;
  components?: UsageComponent[];
}
export interface RunMetrics {
  retrievalMs?: number | null;
  generationMs?: number | null;
  firstTextMs?: number | null;
  clientFirstVisibleTextMs?: number | null;
  clientTimingSource?: string | null;
  providerEventMs?: number | null;
  totalMs?: number | null;
}
export interface GenerationConfig {
  model?: string | null;
  effort?: string | null;
  providerMode?: string | null;
}
export interface GroupCoverage {
  groupId: string;
  hitCount: number;
  status: string;
  missingAspects?: string[];
  reason?: string | null;
}
export interface RetrievalSummary {
  groupCoverage: GroupCoverage[];
  indexSnapshotId?: string | null;
  stopReason?: string | null;
}
export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  responseMode?: ResponseMode;
  extended?: boolean;
  runId?: string;
  status: RunStatus;
  createdAt: string;
  citations: Citation[];
  relations: Relation[];
  sourceViews: SourceView[];
  warnings: string[];
  usage?: Usage | null;
}
export interface AcceptedRun {
  runId: string;
  conversationId: string;
  messageId: string;
  status: RunStatus;
  eventsUrl: string;
}
export interface AnswerRun extends AcceptedRun {
  lastSeq: number;
  message: Message;
  error?: { code: string; message: string } | null;
  usage?: Usage | null;
  warnings: string[];
  metrics?: RunMetrics;
  request?: AnswerRequest;
  generationConfig?: GenerationConfig;
  retrievalSummary?: RetrievalSummary | null;
}
export type EventType =
  | "run.started"
  | "retrieval.status"
  | "text.delta"
  | "citation.add"
  | "relation.add"
  | "source_view.add"
  | "run.completed"
  | "run.failed"
  | "run.cancelled";
export interface RunEvent {
  type: EventType;
  runId: string;
  seq: number;
  at: string;
  data: Record<string, unknown>;
}
export interface Concept {
  id: string;
  name: string;
  description?: string | null;
  aliases: string[];
  type: string;
  revision: number;
}
export type ReviewStatus =
  "pending" | "approved" | "rejected" | "held" | "withdrawn";
export interface DocumentSummary {
  id: string;
  title: string;
  currentRevisionId: string;
  reviewStatus: ReviewStatus;
  indexStatus: string;
  publisher?: string | null;
  sourceType?: string | null;
  url?: string | null;
  publisherId?: string | null;
  visibility?: string;
  activeRevisionId?: string | null;
}
export interface DocumentMetadata {
  publisher?: string | null;
  publisherId?: string | null;
  author?: string | null;
  attributedTo?: string | null;
  attributionBasis?: string | null;
  sourceType?: string | null;
  publishedAt?: string | null;
  url?: string | null;
  visibility?: string;
}
export interface Passage {
  id: string;
  ordinal: number;
  text: string;
  locator: string;
}
export interface DocumentRevision {
  id: string;
  documentId: string;
  title: string;
  content: string;
  metadata: DocumentMetadata;
  reviewStatus: ReviewStatus;
  indexStatus: string;
  passages: Passage[];
  readScope: string;
}
export interface CreateDocument extends DocumentMetadata {
  title: string;
  content: string;
  format: "markdown" | "text";
  visibility: "private" | "shared_candidate";
}
export interface Job {
  id: string;
  kind: string;
  status: string;
  progress?: number | Record<string, unknown> | null;
  error?: string | { message?: string; code?: string } | null;
  createdAt?: string;
  result?: {
    action?: string;
    reason?: string;
    pageId?: string;
    version?: number;
  } | null;
}
export interface ResearchCard {
  id: string;
  title: string;
  url: string;
  publisher?: string | null;
  author?: string | null;
  publishedAt?: string | null;
  readScope: "metadata" | "abstract" | "full" | "partial";
  content?: string | null;
  relevance?: string | null;
  limitations: string[];
  status: string;
}
export interface ResearchResult {
  items: ResearchCard[];
  warnings: string[];
}
export interface TransferResult {
  attachmentIds: string[];
  submittedDocumentIds: string[];
  warnings: string[];
}
export interface WikiPageSummary {
  id: string;
  title: string;
  summary: string;
  version: number;
  updatedAt: string;
  restricted?: boolean;
}
export interface WikiVersion {
  id?: string;
  version: number;
  content?: string;
  createdAt?: string;
  origin?: string;
  operation?: string;
  restoredFromVersion?: number;
}
export interface WikiOrigin {
  id?: string;
  messageId?: string;
  conversationId?: string;
  content?: string;
}
export interface WikiPage extends WikiPageSummary {
  content: string;
  versions: WikiVersion[];
  originMessages: WikiOrigin[];
  citations: Citation[];
  conditions?: string[];
  limitations?: string[];
  status?: string;
  userEdited?: boolean;
  warnings?: string[];
}
export interface WikiDeleted {
  id: string;
  deleted: true;
  version: number;
}
export interface OrganizationResult {
  jobId?: string;
  status: string;
  action: "queued" | "existing" | "skipped";
  reason?: string;
  pageId?: string;
}
export interface WikiSettings {
  autoOrganize: boolean;
  defaultIsAssumption: boolean;
}
export type Screen = "conversation" | "research" | "personal-wiki" | "review";
export interface Route {
  screen: Screen;
  id?: string;
}
export interface Draft extends AnswerSettings {
  text: string;
  sourceLabels: Record<string, string>;
  conceptLabels: Record<string, string>;
  scrollTop?: number;
}
