import { http } from "./http";
import type {
  AcceptedRun,
  AnswerRequest,
  AnswerRun,
  Concept,
  Conversation,
  CreateDocument,
  DocumentMetadata,
  DocumentRevision,
  DocumentSummary,
  Job,
  ListResult,
  LoginResult,
  OrganizationResult,
  ResearchCard,
  ResearchResult,
  ReviewStatus,
  SourceView,
  TransferResult,
  User,
  WikiDeleted,
  WikiPage,
  WikiPageSummary,
  WikiSettings,
} from "../types/contracts";

const enc = encodeURIComponent;
export const identityRepository = {
  login: (username: string, password: string) =>
    http<LoginResult>("/auth/login", {
      method: "POST",
      body: { username, password },
    }),
  me: (signal?: AbortSignal) => http<User>("/auth/me", { signal }),
  health: (signal?: AbortSignal) =>
    http<Record<string, unknown>>("/health", { signal }),
};
export const conversationRepository = {
  list: (signal?: AbortSignal) =>
    http<ListResult<Conversation>>("/conversations", { signal }),
  get: (id: string, signal?: AbortSignal) =>
    http<Conversation>(`/conversations/${enc(id)}`, { signal }),
  create: (title?: string) =>
    http<Conversation>("/conversations", { method: "POST", body: { title } }),
  update: (id: string, values: { autoWiki?: boolean; title?: string }) =>
    http<Conversation>(`/conversations/${enc(id)}`, {
      method: "PATCH",
      body: values,
    }),
  start: (request: AnswerRequest) =>
    http<AcceptedRun>("/answer-runs", { method: "POST", body: request }),
  run: (id: string, signal?: AbortSignal) =>
    http<AnswerRun>(`/answer-runs/${enc(id)}`, { signal }),
  cancel: (id: string) =>
    http<{ runId: string; status: string }>(`/answer-runs/${enc(id)}/cancel`, {
      method: "POST",
    }),
  clientMetrics: (id: string, firstVisibleTextMs: number) =>
    http<unknown>(`/answer-runs/${enc(id)}/client-metrics`, {
      method: "POST",
      body: { firstVisibleTextMs },
    }),
};
export const documentRepository = {
  list: (reviewStatus?: ReviewStatus, signal?: AbortSignal) =>
    http<ListResult<DocumentSummary>>(
      `/documents${reviewStatus ? `?reviewStatus=${enc(reviewStatus)}` : ""}`,
      { signal },
    ),
  revision: (id: string, signal?: AbortSignal) =>
    http<DocumentRevision>(`/documents/revisions/${enc(id)}`, { signal }),
  create: (values: CreateDocument) =>
    http<DocumentSummary>("/documents", { method: "POST", body: values }),
  newRevision: (documentId: string, content: string) =>
    http<DocumentSummary>(`/documents/${enc(documentId)}/revisions`, {
      method: "POST",
      body: { content, format: "markdown" },
    }),
  review: (
    id: string,
    decision: "approve" | "reject" | "hold" | "withdraw",
    reason: string,
  ) =>
    http<DocumentSummary>(`/documents/revisions/${enc(id)}/review`, {
      method: "POST",
      body: { decision, reason },
    }),
  metadata: (id: string, metadata: DocumentMetadata) =>
    http<{ metadataVersion: number; changed: boolean }>(
      `/documents/revisions/${enc(id)}/metadata`,
      {
        method: "PATCH",
        body: metadata,
      },
    ),
  index: (ids: string[]) =>
    http<ListResult<Job>>("/index-jobs", {
      method: "POST",
      body: { sourceRevisionIds: ids, immediate: true },
    }),
  jobs: (signal?: AbortSignal) => http<ListResult<Job>>("/jobs", { signal }),
  cancelJob: (id: string) =>
    http<Job>(`/jobs/${enc(id)}/cancel`, { method: "POST" }),
  retryJob: (id: string) =>
    http<Job>(`/jobs/${enc(id)}/retry`, { method: "POST" }),
};
export const ontologyRepository = {
  concepts: (q: string, signal?: AbortSignal) =>
    http<ListResult<Concept>>(`/ontology/concepts?q=${enc(q)}&limit=20`, {
      signal,
    }),
  sourceViews: (
    id: string,
    filters: {
      publisherId?: string;
      sourceType?: string;
      aspect?: string;
      dateFrom?: string;
      dateTo?: string;
    },
    signal?: AbortSignal,
  ) => {
    const query = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value) query.set(key, value);
    });
    query.set("limit", "50");
    return http<ListResult<SourceView>>(
      `/ontology/concepts/${enc(id)}/source-views?${query}`,
      { signal },
    );
  },
};
export const researchRepository = {
  search: (query: string, conversationId?: string) =>
    http<ResearchResult>("/research/search", {
      method: "POST",
      body: { query, conversationId, limit: 8 },
    }),
  fetch: (url: string, query: string, conversationId?: string) =>
    http<ResearchCard>("/research/fetch", {
      method: "POST",
      body: { url, query, conversationId },
    }),
  transfer: (
    conversationId: string,
    ids: string[],
    query: string,
    conditions: string,
  ) =>
    http<TransferResult>("/research/transfer", {
      method: "POST",
      body: {
        conversationId,
        items: ids.map((id) => ({ id })),
        query,
        conditions,
      },
    }),
};
export const wikiRepository = {
  list: (q: string, signal?: AbortSignal) =>
    http<ListResult<WikiPageSummary>>(`/personal-wiki?q=${enc(q)}`, { signal }),
  get: (id: string, signal?: AbortSignal) =>
    http<WikiPage>(`/personal-wiki/${enc(id)}`, { signal }),
  update: (
    id: string,
    title: string,
    content: string,
    expectedVersion: number,
  ) =>
    http<WikiPage>(`/personal-wiki/${enc(id)}`, {
      method: "PATCH",
      body: { title, content, expectedVersion },
    }),
  remove: (id: string) =>
    http<WikiDeleted>(`/personal-wiki/${enc(id)}`, { method: "DELETE" }),
  undo: (id: string, expectedVersion: number) =>
    http<WikiPage | WikiDeleted>(`/personal-wiki/${enc(id)}/undo`, {
      method: "POST",
      body: { expectedVersion },
    }),
  settings: (signal?: AbortSignal) =>
    http<WikiSettings>("/personal-wiki/settings", { signal }),
  updateSettings: (autoOrganize: boolean) =>
    http<WikiSettings>("/personal-wiki/settings", {
      method: "PATCH",
      body: { autoOrganize },
    }),
  organize: (messageId: string, explicit: boolean) =>
    http<OrganizationResult>("/personal-wiki/organize", {
      method: "POST",
      body: { messageId, explicit },
    }),
  jobs: (signal?: AbortSignal) =>
    http<ListResult<Job>>("/jobs?kind=personal_wiki", { signal }),
};
