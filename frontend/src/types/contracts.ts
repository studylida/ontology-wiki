export interface User { id: string; username: string; role: string; kind: string; permissions: string[] }
export interface PublicError { code: string; message: string; retryable?: boolean; phase?: string }
export type RunStatus = 'accepted' | 'retrieving' | 'generating' | 'completed' | 'failed' | 'cancelled' | 'interrupted';
interface CitationBase {
  id: string; passageId: string; sourceRevisionId: string;
  title: string; locator: string; excerpt: string; number: number;
}
export type Citation = CitationBase & (
  | {sourceKind?: 'document'; documentId: string}
  | {sourceKind: 'wiki'; pageId: string; revisionNumber?: number; sourceNote?: string}
);
export function isCitation(value: unknown): value is Citation {
  if (!value || typeof value !== 'object') return false;
  const c = value as Record<string, unknown>;
  const identity = c.sourceKind === 'wiki' ? typeof c.pageId === 'string' && !!c.pageId && !c.documentId
    : (c.sourceKind === undefined || c.sourceKind === 'document') && typeof c.documentId === 'string' && !!c.documentId;
  return identity && ['id', 'passageId', 'sourceRevisionId', 'title', 'locator', 'excerpt'].every(key => typeof c[key] === 'string') &&
    c.id === c.passageId && !!c.id && Number.isSafeInteger(c.number) && (c.number as number) > 0;
}
export interface Message {
  id: string; role: 'user' | 'assistant'; content: string; createdAt: string;
  status: RunStatus; runId: string | null; citations: Citation[]; warnings: string[];
  sourceUnavailable: boolean; historicalSources: boolean;
}
export interface Conversation { id: string; title: string; createdAt: string; updatedAt: string }
export interface ConversationDetail extends Conversation { messages: Message[] }
export interface RunHandle {
  runId: string; conversationId: string; userMessageId: string; messageId: string;
  requestId: string; status: RunStatus; durableSeq: number; eventsUrl: string;
}
export interface RunDetail extends RunHandle {
  answer: Message; error: PublicError | null; usage: unknown; retrievalRunId: string | null; retrieval: unknown;
}
export type RunEvent = { runId: string } & (
  | { type: 'stream_error'; seq?: never; data: { error: PublicError } }
  | { type: 'delta'; seq: number; data: { text: string } }
  | { type: 'citation'; seq: number; data: Citation }
  | { type: 'state'; seq: number; data: { status: RunStatus; warnings?: string[] } }
  | { type: 'complete' | 'error' | 'cancelled' | 'interrupted'; seq: number;
      data: { status: RunStatus; warnings?: string[]; error?: PublicError | null } }
);
export type Submission =
  | { kind: 'turn'; conversationId: string; requestId: string; question: string }
  | { kind: 'retry'; conversationId: string; requestId: string; runId: string };
export interface Job { id: string; status: string; stage?: string; error?: PublicError | null; attempts?: number }
export interface Revision {
  id: string; revision: number; title: string; filename: string; mediaType: string; status: string;
  passageCount: number; heldPassageCount: number; usablePassageCount: number;
  limitations: string[]; job: Job | null; createdAt: string;
}
export interface SharedDocument {
  id: string; title: string; shared: boolean; withdrawn: boolean; status: string; searchable: boolean;
  canManage: boolean; currentRevisionId: string | null; activeRevisionId: string | null;
  latestRevision: Revision | null; activeRevision: Revision | null; updatedAt: string;
}
export interface Passage { id: string; ordinal: number; text: string; locator: string;
  startOffset: number; endOffset: number; excluded: boolean; exclusionReason: string | null }
export interface Source { documentId: string; revisionId: string; active: boolean; content: string | null; passages: Passage[] }
export type SourceSelection = {revisionId: string; title: string; citation?: Citation} & (
  | {sourceKind?: 'document'; documentId: string}
  | {sourceKind: 'wiki'; pageId: string}
);
export interface WikiSource {
  sourceKind: 'wiki'; pageId: string; revisionId: string; revisionNumber: number;
  title: string; active: boolean; content: string; sourceNote: string;
  editor: {id: string; username: string}; createdAt: string; passages: Passage[];
}
export type EvidenceSource = Source | WikiSource;

export interface UploadReceipt { documentId: string; revisionId: string; status: string; searchable: boolean; duplicate: boolean }
