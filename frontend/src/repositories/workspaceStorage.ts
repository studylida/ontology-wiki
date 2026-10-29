import type { Submission } from '../types/contracts';
import { isWikiPending, type WikiPending } from '../types/wiki';

// New service namespace. Never import old drafts, answers or mode preferences.
const PREFIX = 'knowledge-assistant.v3.';
export const AUTH_CHANGED = 'knowledge-assistant:auth-expired';
export const authStorage = {
  getToken: () => sessionStorage.getItem(PREFIX + 'token'),
  setToken: (token: string) => sessionStorage.setItem(PREFIX + 'token', token),
  clear: () => sessionStorage.removeItem(PREFIX + 'token'),
};
export function rememberConversation(userId: string, id: string) {
  sessionStorage.setItem(PREFIX + userId + '.conversation', id);
}
export function rememberedConversation(userId: string) {
  return sessionStorage.getItem(PREFIX + userId + '.conversation');
}
export function pendingSubmission(userId: string): Submission | null {
  try {
    const p = JSON.parse(sessionStorage.getItem(PREFIX + userId + '.pending') || 'null');
    if (!p || typeof p.conversationId !== 'string' || typeof p.requestId !== 'string') return null;
    if (p.kind === 'turn' && typeof p.question === 'string') return p;
    if (p.kind === 'retry' && typeof p.runId === 'string') return p;
  } catch { /* Invalid new-service state is ignored, never converted from legacy data. */ }
  return null;
}
export function savePending(userId: string, pending: Submission | null) {
  const key = PREFIX + userId + '.pending';
  if (pending) sessionStorage.setItem(key, JSON.stringify(pending));
  else sessionStorage.removeItem(key);
}
export function clearWorkspace(userId: string) {
  sessionStorage.removeItem(PREFIX + userId + '.conversation');
  sessionStorage.removeItem(PREFIX + userId + '.pending');
  sessionStorage.removeItem(PREFIX + userId + '.wiki-pending');
}
export function newRequestId(): string {
  return crypto.randomUUID();
}

export function pendingWikiMutation(userId: string): WikiPending | null {
  try {
    const value: unknown = JSON.parse(sessionStorage.getItem(PREFIX + userId + '.wiki-pending') || 'null');
    return isWikiPending(value) ? value : null;
  } catch { return null; }
}
export function savePendingWikiMutation(userId: string, pending: WikiPending | null): boolean {
  try {
    const key = PREFIX + userId + '.wiki-pending';
    if (pending) sessionStorage.setItem(key, JSON.stringify(pending));
    else sessionStorage.removeItem(key);
    return true;
  } catch { return false; } // The controller warns; never pretend refresh recovery was persisted.
}
