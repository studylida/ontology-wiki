import type { User, Conversation, ConversationDetail, RunHandle, RunDetail, SharedDocument, Source, UploadReceipt, Submission } from '../types/contracts';
import { http } from './http';
const id = encodeURIComponent;
export const api = {
  login: (username: string, password: string) => http<{accessToken: string; user: User}>('/auth/login', {method: 'POST', body: {username, password}}),
  me: (signal?: AbortSignal) => http<User>('/auth/me', {signal}),
  conversations: (signal?: AbortSignal) => http<{items: Conversation[]}>('/conversations', {signal}),
  conversation: (key: string, signal?: AbortSignal) => http<ConversationDetail>(`/conversations/${id(key)}`, {signal}),
  createConversation: () => http<Conversation>('/conversations', {method: 'POST', body: {}}),
  renameConversation: (key: string, title: string) => http<Conversation>(`/conversations/${id(key)}`, {method: 'PATCH', body: {title}}),
  submit: (pending: Submission) => pending.kind === 'turn'
    ? http<RunHandle>(`/conversations/${id(pending.conversationId)}/turns`, {method: 'POST', body: {question: pending.question, requestId: pending.requestId}})
    : http<RunHandle>(`/answer-runs/${id(pending.runId)}/retry`, {method: 'POST', body: {requestId: pending.requestId}}),
  run: (key: string, signal?: AbortSignal) => http<RunDetail>(`/answer-runs/${id(key)}`, {signal}),
  cancel: (key: string) => http<RunDetail>(`/answer-runs/${id(key)}/cancel`, {method: 'POST'}),
  documents: (signal?: AbortSignal) => http<{items: SharedDocument[]}>('/documents', {signal}),
  document: (key: string, signal?: AbortSignal) => http<SharedDocument>(`/documents/${id(key)}`, {signal}),
  source: (key: string, revision: string, signal?: AbortSignal) => http<Source>(`/documents/${id(key)}/passages?revisionId=${id(revision)}`, {signal}),
  upload: (file: File, title: string) => {
    const body = new FormData(); body.append('file', file);
    if (title.trim()) body.append('title', title.trim());
    return http<UploadReceipt>('/documents', {method: 'POST', body});
  },
  reprocess: (key: string) => http(`/documents/${id(key)}/reprocess`, {method: 'POST'}),
  deactivate: (key: string) => http(`/documents/${id(key)}/deactivate`, {method: 'POST'}),
};
