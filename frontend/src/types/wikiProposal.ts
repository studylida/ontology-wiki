import type { WikiMutation, WikiWrite } from './wiki';
export type ProposalMode = 'create' | 'edit' | 'links';
export type ChatSeed = {conversationId: string; messageId: string; content: string};
export type ProposalRequest = {requestId: string; mode: ProposalMode; pageId?: string; instruction: string;
  contextText?: string; selection?: {conversationId: string; messageId: string; text: string}};
export type ProposalSummary = {id: string; pageId: string | null; mode: ProposalMode; status: string; shared?: boolean; originRevisionId?: string | null; createdAt: string; updatedAt: string};
export type ProposalEvidence = {sourceKind: 'wiki' | 'document'; pageId?: string; documentId?: string;
  sourceRevisionId: string; passageId: string; title: string; locator: string; text: string};
export type Proposal = ProposalSummary & {ownerId: string; baseVersion: number | null; baseRevisionId: string | null;
  base: Partial<WikiWrite>; instruction: string; employeeText: string; inputKind: string;
  result: Partial<WikiWrite> & {reason?: string; diff?: string; warnings?: string[]; evidence?: ProposalEvidence[];
    links?: {anchor: string; pageId: string; reason: string}[]; similar?: {pageId: string; title: string; meaning: string}[]; model?: string};
  error: {code: string; message: string} | null; stale: boolean; sourceChanged?: boolean; currentVersion: number | null; canApply: boolean;
  appliedResult: WikiMutation | null};
export type ProposalCommand = {kind: 'submit'; body: ProposalRequest} |
  {kind: 'apply'; id: string; body: WikiWrite & {requestId: string}};
export type ProposalPending = {command: ProposalCommand; receipt: ProposalSummary | WikiMutation | null};
export function isProposalPending(raw: unknown): raw is ProposalPending {
  if (!raw || typeof raw !== 'object') return false;
  const value = raw as ProposalPending, c = value.command;
  return !!c && ['submit', 'apply'].includes(c.kind) && !!c.body && typeof c.body.requestId === 'string' &&
    /^[A-Za-z0-9_.:-]{8,128}$/.test(c.body.requestId) && (c.kind !== 'apply' || typeof c.id === 'string');
}
