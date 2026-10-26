import type {
  AcceptedRun,
  AnswerRequest,
  AnswerRun,
  Citation,
  Conversation,
  Draft,
  GenerationConfig,
  Message,
  Relation,
  RetrievalSummary,
  RunEvent,
  RunMetrics,
  RunStatus,
  SourceView,
  Usage,
} from "../types/contracts";
import { defaultDraft, isTerminal } from "./conversationService";

export interface ActiveRun {
  id: string;
  messageId: string;
  lastSeq: number;
  status: RunStatus;
  request?: AnswerRequest;
  usage?: Usage | null;
  metrics?: RunMetrics;
  generationConfig?: GenerationConfig;
  retrievalSummary?: RetrievalSummary | null;
}
export interface ChatState {
  id?: string;
  title: string;
  autoWiki: boolean;
  messages: Message[];
  draft: Draft;
  loading: boolean;
  starting: boolean;
  run: ActiveRun | null;
  connection:
    | "idle"
    | "connecting"
    | "streaming"
    | "reconnecting"
    | "disconnected"
    | "cancelling";
  progress: string;
  error: string | null;
  retryRequest: AnswerRequest | null;
}
export const initialChatState = (): ChatState => ({
  title: "새 대화",
  autoWiki: true,
  messages: [],
  draft: defaultDraft(),
  loading: false,
  starting: false,
  run: null,
  connection: "idle",
  progress: "",
  error: null,
  retryRequest: null,
});
export type ChatAction =
  | { type: "loading"; id?: string; draft: Draft }
  | { type: "restored"; conversation: Conversation; draft: Draft }
  | { type: "draft"; values: Partial<Draft> }
  | { type: "autoWiki"; value: boolean }
  | { type: "begin"; request: AnswerRequest; preserveDraft: boolean }
  | { type: "accepted"; value: AcceptedRun; request: AnswerRequest }
  | { type: "startFailed"; message: string; request: AnswerRequest }
  | { type: "error"; message: string | null }
  | { type: "connection"; value: ChatState["connection"]; message?: string }
  | { type: "event"; event: RunEvent }
  | { type: "snapshot"; value: AnswerRun };
export type ClientMetricAction = {
  type: "clientMetric";
  runId: string;
  firstVisibleTextMs: number;
};

const unique = <T extends { id: string }>(items: T[], item: T): T[] => [
  ...items.filter((value) => value.id !== item.id),
  item,
];
function normalizeMessage(message: Message): Message {
  return {
    ...message,
    citations: message.citations || [],
    relations: message.relations || [],
    sourceViews: message.sourceViews || [],
    warnings: message.warnings || [],
  };
}
export function chatReducer(
  state: ChatState,
  action: ChatAction | ClientMetricAction,
): ChatState {
  switch (action.type) {
    case "loading":
      return {
        ...initialChatState(),
        id: action.id,
        draft: action.draft,
        loading: !!action.id,
      };
    case "restored":
      return {
        ...state,
        id: action.conversation.id,
        title: action.conversation.title,
        autoWiki: action.conversation.autoWiki,
        draft: action.draft,
        messages: (action.conversation.messages || []).map(normalizeMessage),
        loading: false,
        error: null,
      };
    case "draft":
      return { ...state, draft: { ...state.draft, ...action.values } };
    case "autoWiki":
      return { ...state, autoWiki: action.value };
    case "clientMetric":
      return state.run?.id === action.runId
        ? {
            ...state,
            run: {
              ...state.run,
              metrics: {
                ...state.run.metrics,
                clientFirstVisibleTextMs: action.firstVisibleTextMs,
              },
            },
          }
        : state;
    case "error":
      return { ...state, error: action.message, loading: false };
    case "connection":
      return {
        ...state,
        connection: action.value,
        ...(action.message ? { progress: action.message } : {}),
      };
    case "begin": {
      const request = action.request;
      const base = {
        createdAt: new Date().toISOString(),
        citations: [],
        relations: [],
        sourceViews: [],
        warnings: [],
      };
      const user: Message = {
        ...base,
        id: `pending-user-${request.clientRequestId}`,
        role: "user",
        content: request.message,
        status: "completed",
      };
      const assistant: Message = {
        ...base,
        id: `pending-${request.clientRequestId}`,
        role: "assistant",
        content: "",
        responseMode: request.responseMode,
        extended: request.extended,
        status: "queued",
      };
      return {
        ...state,
        messages: [
          ...state.messages.filter(
            (message) => message.id !== user.id && message.id !== assistant.id,
          ),
          user,
          assistant,
        ],
        starting: true,
        run: null,
        connection: "connecting",
        progress: "요청을 저장하는 중",
        error: null,
        retryRequest: null,
        draft: action.preserveDraft
          ? state.draft
          : { ...state.draft, text: "" },
      };
    }
    case "accepted":
      return {
        ...state,
        id: action.value.conversationId,
        starting: false,
        retryRequest: null,
        messages: state.messages.map((message) =>
          message.id === `pending-${action.request.clientRequestId}`
            ? {
                ...message,
                id: action.value.messageId,
                runId: action.value.runId,
                status: action.value.status,
              }
            : message,
        ),
        run: {
          id: action.value.runId,
          messageId: action.value.messageId,
          lastSeq: 0,
          status: action.value.status,
          request: action.request,
        },
        connection: "connecting",
      };
    case "startFailed":
      return {
        ...state,
        starting: false,
        connection: "disconnected",
        progress: "",
        error: action.message,
        retryRequest: action.request,
        messages: state.messages.map((message) =>
          message.id === `pending-${action.request.clientRequestId}`
            ? { ...message, status: "failed" }
            : message,
        ),
      };
    case "snapshot": {
      const run = action.value;
      if (state.id && run.conversationId !== state.id) return state;
      if (state.run && state.run.id !== run.runId) return state;
      if (state.run && state.run.lastSeq > run.lastSeq) return state;
      if (state.run && isTerminal(state.run.status) && !isTerminal(run.status))
        return state;
      const message = normalizeMessage(run.message);
      const found = state.messages.some(
        (value) => value.id === message.id || value.runId === run.runId,
      );
      return {
        ...state,
        id: run.conversationId,
        starting: false,
        messages: found
          ? state.messages.map((value) =>
              value.id === message.id || value.runId === run.runId
                ? message
                : value,
            )
          : [...state.messages, message],
        run: {
          id: run.runId,
          messageId: run.messageId,
          lastSeq: run.lastSeq,
          status: run.status,
          request: run.request,
          usage: run.usage,
          metrics: {
            ...state.run?.metrics,
            ...run.metrics,
            clientFirstVisibleTextMs:
              run.metrics?.clientFirstVisibleTextMs ??
              state.run?.metrics?.clientFirstVisibleTextMs,
          },
          generationConfig: run.generationConfig,
          retrievalSummary: run.retrievalSummary ?? state.run?.retrievalSummary,
        },
        connection: isTerminal(run.status) ? "idle" : state.connection,
        progress: isTerminal(run.status) ? "" : state.progress,
        error: run.error?.message || null,
      };
    }
    case "event": {
      const event = action.event;
      if (
        !state.run ||
        state.run.id !== event.runId ||
        event.seq <= state.run.lastSeq ||
        isTerminal(state.run.status)
      )
        return state;
      let run: ActiveRun = { ...state.run, lastSeq: event.seq };
      let progress = state.progress;
      let error = state.error;
      let connection = state.connection;
      const messages = state.messages.map((message) => {
        if (message.id !== run.messageId) return message;
        const next = { ...message };
        switch (event.type) {
          case "run.started":
            run.status = "running";
            next.status = "running";
            if (event.data.generationConfig)
              run.generationConfig = event.data
                .generationConfig as GenerationConfig;
            break;
          case "retrieval.status": {
            if (Array.isArray(event.data.groupCoverage))
              run.retrievalSummary = {
                groupCoverage: event.data
                  .groupCoverage as unknown as RetrievalSummary["groupCoverage"],
                indexSnapshotId:
                  typeof event.data.indexSnapshotId === "string"
                    ? event.data.indexSnapshotId
                    : null,
                stopReason:
                  typeof event.data.stopReason === "string"
                    ? event.data.stopReason
                    : null,
              };
            progress =
              typeof event.data.message === "string"
                ? event.data.message
                : "근거를 확인하는 중";
            if (Array.isArray(event.data.warnings))
              next.warnings = [
                ...new Set([
                  ...next.warnings,
                  ...event.data.warnings.filter(
                    (value): value is string => typeof value === "string",
                  ),
                ]),
              ];
            break;
          }
          case "text.delta":
            if (typeof event.data.text === "string")
              next.content += event.data.text;
            break;
          case "citation.add":
            next.citations = unique(
              next.citations,
              event.data as unknown as Citation,
            );
            break;
          case "relation.add":
            next.relations = unique(
              next.relations,
              event.data as unknown as Relation,
            );
            break;
          case "source_view.add":
            next.sourceViews = unique(
              next.sourceViews,
              event.data as unknown as SourceView,
            );
            break;
          case "run.completed":
          case "run.failed":
          case "run.cancelled": {
            const status =
              event.type === "run.completed"
                ? "completed"
                : event.type === "run.cancelled"
                  ? "cancelled"
                  : "failed";
            run = { ...run, status, usage: event.data.usage as Usage | null };
            next.status = status;
            next.usage = run.usage;
            if (Array.isArray(event.data.warnings))
              next.warnings = [
                ...new Set([
                  ...next.warnings,
                  ...event.data.warnings.filter(
                    (value): value is string => typeof value === "string",
                  ),
                ]),
              ];
            const failure = event.data.error as
              { message?: string } | undefined;
            error = failure?.message || null;
            progress = "";
            connection = "idle";
            break;
          }
        }
        return next;
      });
      return { ...state, run, messages, progress, error, connection };
    }
  }
}
