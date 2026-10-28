import type { Submission } from '../types/contracts';

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
}
export function newRequestId(): string {
  return crypto.randomUUID();
}
