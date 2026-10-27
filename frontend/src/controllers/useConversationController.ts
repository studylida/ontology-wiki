import { useCallback, useEffect, useReducer, useRef, useState } from "react";
import type {
  AnswerRequest,
  AnswerOverrides,
  Citation,
  Concept,
  Conversation,
  Draft,
  Relation,
  SourceView,
} from "../types/contracts";
import { conversationRepository, wikiRepository } from "../repositories/api";
import { ApiError, errorMessage, isAbort } from "../repositories/http";
import { readRunStream } from "../repositories/stream";
import { workspaceStorage } from "../repositories/workspaceStorage";
import {
  buildAnswerRequest,
  defaultDraft,
  conversationService,
  groupsFromViews,
  isTerminal,
  relationQuestion,
  restoreDraft,
} from "../services/conversationService";
import { chatReducer, initialChatState } from "../services/chatState";
import { organizationReason } from "../services/display";

export interface Followup {
  title: string;
  text: string;
  overrides?: AnswerOverrides;
}
function reconnectDelay(ms: number, signal: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    const timer = window.setTimeout(() => {
      signal.removeEventListener("abort", abort);
      resolve();
    }, ms);
    const abort = () => {
      clearTimeout(timer);
      reject(new DOMException("Aborted", "AbortError"));
    };
    signal.addEventListener("abort", abort, { once: true });
    if (signal.aborted) abort();
  });
}
export function useConversationController(
  userId: string,
  selectedId: string | undefined,
  onCreated: (id: string) => void,
) {
  const [state, dispatch] = useReducer(
    chatReducer,
    undefined,
    initialChatState,
  );
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [listError, setListError] = useState<string | null>(null);
  const [followup, setFollowup] = useState<Followup | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [hydrated, setHydrated] = useState(false);
  const stateRef = useRef(state);
  stateRef.current = state;
  const selectedRef = useRef<string | null>(null);
  const epoch = useRef(0);
  const streamAbort = useRef<AbortController | null>(null);
  const onCreatedRef = useRef(onCreated);
  onCreatedRef.current = onCreated;
  const submitting = useRef<string | null>(null);
  const visibleTimings = useRef(
    new Map<string, { sentAt: number; reported: boolean }>(),
  );
  const submittedRequests = useRef(new Set<string>());

  const refreshList = useCallback(async () => {
    try {
      const result = await conversationRepository.list();
      setConversations(result.items);
      setListError(null);
    } catch (error) {
      setListError(errorMessage(error));
    }
  }, []);
  useEffect(() => {
    void refreshList();
  }, [refreshList]);

  const listen = useCallback(
    async (runId: string, after: number, requestEpoch: number) => {
      streamAbort.current?.abort();
      const controller = new AbortController();
      streamAbort.current = controller;
      let lastSeq = after;
      let terminal = false;
      let attempts = 0;
      while (
        epoch.current === requestEpoch &&
        !controller.signal.aborted &&
        !terminal
      ) {
        dispatch({
          type: "connection",
          value: attempts ? "reconnecting" : "connecting",
          ...(attempts
            ? { message: "같은 실행의 저장된 응답에 다시 연결하는 중" }
            : {}),
        });
        try {
          await readRunStream(runId, lastSeq, controller.signal, (event) => {
            if (
              epoch.current !== requestEpoch ||
              event.runId !== runId ||
              event.seq <= lastSeq
            )
              return;
            lastSeq = event.seq;
            dispatch({ type: "connection", value: "streaming" });
            dispatch({ type: "event", event });
            if (
              ["run.completed", "run.failed", "run.cancelled"].includes(
                event.type,
              )
            ) {
              terminal = true;
              controller.abort();
            }
          });
        } catch (error) {
          if (terminal) break;
          if (isAbort(error) || epoch.current !== requestEpoch) return;
          if (
            error instanceof ApiError &&
            [401, 403, 404].includes(error.status)
          ) {
            dispatch({ type: "connection", value: "disconnected" });
            dispatch({ type: "error", message: errorMessage(error) });
            return;
          }
        }
        if (
          terminal ||
          controller.signal.aborted ||
          epoch.current !== requestEpoch
        )
          break;
        // A restored/replayed run is not a new first-visible observation.
        visibleTimings.current.delete(runId);
        try {
          const run = await conversationService.recover(
            runId,
            controller.signal,
          );
          if (epoch.current !== requestEpoch) return;
          dispatch({ type: "snapshot", value: run });
          lastSeq = run.lastSeq;
          if (isTerminal(run.status)) {
            terminal = true;
            break;
          }
        } catch (error) {
          if (isAbort(error)) return;
        }
        if (++attempts > 4) {
          dispatch({
            type: "connection",
            value: "disconnected",
            message:
              "연결이 끊어졌습니다. 저장된 실행에 다시 연결할 수 있습니다.",
          });
          return;
        }
        try {
          await reconnectDelay(
            Math.min(500 * 2 ** attempts, 4000),
            controller.signal,
          );
        } catch {
          return;
        }
      }
      if (terminal && epoch.current === requestEpoch) {
        try {
          const run = await conversationService.recover(runId);
          if (epoch.current === requestEpoch)
            dispatch({ type: "snapshot", value: run });
        } catch (error) {
          if (epoch.current === requestEpoch)
            setNotice(
              `응답 상태는 저장되었지만 상세 계측을 가져오지 못했습니다. ${errorMessage(error)}`,
            );
        }
        void refreshList();
      }
    },
    [refreshList],
  );

  useEffect(() => {
    const selection = selectedId || "new";
    if (selectedRef.current === selection) return;
    selectedRef.current = selection;
    const requestEpoch = ++epoch.current;
    visibleTimings.current.clear();
    streamAbort.current?.abort();
    submitting.current = null;
    setFollowup(null);
    setNotice(null);
    setHydrated(false);
    const local = workspaceStorage.load(userId, selectedId);
    dispatch({ type: "loading", id: selectedId, draft: restoreDraft(local) });
    if (!selectedId) {
      setHydrated(true);
      return;
    }
    const controller = new AbortController();
    conversationService
      .restore(selectedId, controller.signal)
      .then(async (conversation) => {
        if (epoch.current !== requestEpoch) return;
        dispatch({
          type: "restored",
          conversation,
          draft: restoreDraft(local, conversation.nextSettings),
        });
        setHydrated(true);
        const candidates = (conversation.messages || []).filter(
          (message) => message.role === "assistant" && message.runId,
        );
        const message =
          [...candidates]
            .reverse()
            .find((message) => !isTerminal(message.status)) ||
          candidates.at(-1);
        if (message?.runId) {
          const run = await conversationService.recover(
            message.runId,
            controller.signal,
          );
          if (epoch.current !== requestEpoch) return;
          dispatch({ type: "snapshot", value: run });
          if (!isTerminal(run.status))
            void listen(run.runId, run.lastSeq, requestEpoch);
        }
      })
      .catch((error) => {
        if (!isAbort(error) && epoch.current === requestEpoch)
          dispatch({ type: "error", message: errorMessage(error) });
      });
    return () => {
      controller.abort();
      if (selectedRef.current === selection) selectedRef.current = null;
    };
  }, [selectedId, userId, listen]);
  useEffect(
    () => () => {
      epoch.current++;
      streamAbort.current?.abort();
    },
    [],
  );
  useEffect(() => {
    if (
      hydrated &&
      !state.loading &&
      !workspaceStorage.save(userId, state.id, state.draft)
    )
      setNotice(
        "이 브라우저가 초안 저장을 허용하지 않습니다. 화면을 닫으면 입력 중인 내용이 복원되지 않을 수 있습니다.",
      );
  }, [userId, state.id, state.draft, state.loading, hydrated]);

  const setDraft = useCallback(
    (values: Partial<Draft>) => dispatch({ type: "draft", values }),
    [],
  );
  const prepareNew = useCallback(() => {
    epoch.current++;
    streamAbort.current?.abort();
    visibleTimings.current.clear();
    submitting.current = null;
    selectedRef.current = null;
    workspaceStorage.removeNew(userId);
    setFollowup(null);
    setNotice(null);
    setHydrated(true);
    dispatch({ type: "loading", draft: defaultDraft() });
  }, [userId]);
  const saveScroll = useCallback(
    (conversationId: string | undefined, scrollTop: number) => {
      if (stateRef.current.id === conversationId)
        dispatch({ type: "draft", values: { scrollTop } });
      else {
        const draft = restoreDraft(
          workspaceStorage.load(userId, conversationId),
        );
        workspaceStorage.save(userId, conversationId, { ...draft, scrollTop });
      }
    },
    [userId],
  );
  const performRequest = useCallback(
    async (request: AnswerRequest, preserveDraft: boolean) => {
      if (
        submitting.current ||
        (stateRef.current.run && !isTerminal(stateRef.current.run.status))
      )
        return;
      submitting.current = request.clientRequestId;
      const requestEpoch = epoch.current;
      const freshRequest = !submittedRequests.current.has(
        request.clientRequestId,
      );
      submittedRequests.current.add(request.clientRequestId);
      const sentAt = performance.now();
      dispatch({ type: "begin", request, preserveDraft });
      try {
        const accepted = await conversationService.submit(request);
        if (epoch.current !== requestEpoch) {
          void refreshList();
          return;
        }
        selectedRef.current = accepted.conversationId;
        if (freshRequest)
          visibleTimings.current.set(accepted.runId, {
            sentAt,
            reported: false,
          });
        dispatch({ type: "accepted", value: accepted, request });
        if (!request.conversationId) {
          workspaceStorage.removeNew(userId);
          onCreatedRef.current(accepted.conversationId);
        }
        setFollowup(null);
        void refreshList();
        void listen(accepted.runId, 0, requestEpoch);
      } catch (error) {
        if (epoch.current === requestEpoch)
          dispatch({
            type: "startFailed",
            message: errorMessage(error),
            request,
          });
      } finally {
        if (submitting.current === request.clientRequestId)
          submitting.current = null;
      }
    },
    [listen, refreshList, userId],
  );
  const send = useCallback(
    (text?: string, overrides?: AnswerOverrides, preserveDraft = false) => {
      try {
        return performRequest(
          buildAnswerRequest(
            stateRef.current.draft,
            stateRef.current.id,
            text,
            overrides,
          ),
          preserveDraft,
        );
      } catch (error) {
        dispatch({ type: "error", message: errorMessage(error) });
        return Promise.resolve();
      }
    },
    [performRequest],
  );
  const cancel = useCallback(async () => {
    const run = stateRef.current.run;
    if (!run || isTerminal(run.status)) return;
    const requestEpoch = epoch.current;
    dispatch({
      type: "connection",
      value: "cancelling",
      message: "중단 요청을 처리하는 중",
    });
    try {
      await conversationRepository.cancel(run.id);
      const recovered = await conversationService.recover(run.id);
      if (requestEpoch === epoch.current)
        dispatch({ type: "snapshot", value: recovered });
    } catch (error) {
      if (requestEpoch === epoch.current) {
        dispatch({ type: "error", message: errorMessage(error) });
        dispatch({ type: "connection", value: "disconnected" });
      }
    }
  }, []);
  const reconnect = useCallback(() => {
    const run = stateRef.current.run;
    if (run) {
      visibleTimings.current.delete(run.id);
      dispatch({ type: "error", message: null });
      void listen(run.id, run.lastSeq, epoch.current);
    }
  }, [listen]);
  const retryCreation = useCallback(() => {
    const request = stateRef.current.retryRequest;
    if (request) void performRequest(request, true);
  }, [performRequest]);
  const attachDocument = useCallback((id: string, title: string) => {
    const draft = stateRef.current.draft;
    dispatch({
      type: "draft",
      values: {
        documentContextIds: [...new Set([...draft.documentContextIds, id])],
        sourceLabels: { ...draft.sourceLabels, [id]: title },
      },
    });
    setNotice(
      "문헌을 다음 질문의 자료로 추가했습니다. 질문을 보내면 이 자료를 함께 확인합니다.",
    );
  }, []);
  const attachResearch = useCallback(
    (attachmentIds: string[], conversationId?: string) => {
      const draft = {
        ...stateRef.current.draft,
        attachmentIds: [
          ...new Set([
            ...stateRef.current.draft.attachmentIds,
            ...attachmentIds,
          ]),
        ],
      };
      if (conversationId && conversationId !== stateRef.current.id)
        workspaceStorage.save(userId, conversationId, draft);
      else
        dispatch({
          type: "draft",
          values: { attachmentIds: draft.attachmentIds },
        });
      setNotice(
        "선택한 문헌을 대화에 가져왔습니다. 입력 중이던 질문은 유지되며 자동으로 답변을 생성하지 않습니다.",
      );
    },
    [userId],
  );
  const removeDocument = useCallback((id: string) => {
    const draft = stateRef.current.draft;
    dispatch({
      type: "draft",
      values: {
        documentContextIds: draft.documentContextIds.filter(
          (value) => value !== id,
        ),
        sourceRevisionIds: draft.sourceRevisionIds.filter(
          (value) => value !== id,
        ),
      },
    });
  }, []);
  const addConcept = useCallback((concept: Concept) => {
    const draft = stateRef.current.draft;
    dispatch({
      type: "draft",
      values: {
        conceptIds: [...new Set([...draft.conceptIds, concept.id])],
        conceptLabels: { ...draft.conceptLabels, [concept.id]: concept.name },
      },
    });
  }, []);
  const toggleAutoWiki = useCallback(async (autoWiki: boolean) => {
    const id = stateRef.current.id;
    const requestEpoch = epoch.current;
    if (!id) return;
    try {
      const result = await conversationRepository.update(id, { autoWiki });
      if (epoch.current === requestEpoch)
        dispatch({ type: "autoWiki", value: result.autoWiki });
    } catch (error) {
      if (epoch.current === requestEpoch) setNotice(errorMessage(error));
    }
  }, []);
  const organize = useCallback(async (messageId: string) => {
    try {
      const result = await wikiRepository.organize(messageId, true);
      setNotice(
        result.action === "queued"
          ? "개인 위키 정리 작업을 요청했습니다. 저장 결과는 개인 위키에서 확인할 수 있습니다."
          : result.action === "existing"
            ? `기존 정리 작업을 확인했습니다. 현재 상태: ${result.status}`
            : `새 정리 작업을 만들지 않았습니다. ${organizationReason(result.reason)}`,
      );
    } catch (error) {
      setNotice(errorMessage(error));
    }
  }, []);
  const relationFollowup = useCallback(
    (relation: Relation) =>
      setFollowup({
        title: `${relation.toName} 이어서 질문`,
        text: relationQuestion(relation),
        overrides: {
          conceptIds: [
            ...new Set([
              ...stateRef.current.draft.conceptIds,
              relation.toConceptId,
            ]),
          ].filter(Boolean),
        },
      }),
    [],
  );
  const compareViews = useCallback((views: SourceView[]) => {
    const labels = views.map(
      (view) =>
        `${view.attributedTo || view.author || `${view.publisher || "발행처 미확인"} (귀속 미확인)`} · ${view.aspect}`,
    );
    setFollowup({
      title: "선택한 출처 관점 비교",
      text: `다음 출처의 관점을 적용 조건과 근거의 차이를 중심으로 비교해 주세요. 자료가 부족한 관점은 구분해 알려 주세요.\n${labels.join("\n")}`,
      overrides: {
        sourceGroups: groupsFromViews(views),
        sourceRevisionIds: [
          ...new Set(views.map((view) => view.sourceRevisionId)),
        ],
      },
    });
  }, []);
  const citeFollowup = useCallback(
    (citation: Citation) =>
      attachDocument(citation.sourceRevisionId, citation.title),
    [attachDocument],
  );
  const reportFirstVisible = useCallback((runId: string) => {
    const timing = visibleTimings.current.get(runId);
    if (!timing || timing.reported || stateRef.current.run?.id !== runId)
      return;
    timing.reported = true;
    const firstVisibleTextMs = Math.max(0, performance.now() - timing.sentAt);
    dispatch({ type: "clientMetric", runId, firstVisibleTextMs });
    void conversationRepository
      .clientMetrics(runId, firstVisibleTextMs)
      .catch(() => {
        /* Telemetry failure must not turn a saved answer into a failed answer. */
      });
  }, []);
  const suspendVisibleMeasurement = useCallback(
    () => visibleTimings.current.clear(),
    [],
  );
  return {
    state,
    conversations,
    listError,
    followup,
    notice,
    busy: state.starting || !!(state.run && !isTerminal(state.run.status)),
    setDraft,
    prepareNew,
    saveScroll,
    send,
    cancel,
    reconnect,
    retryCreation,
    refreshList,
    setFollowup,
    setNotice,
    attachDocument,
    attachResearch,
    removeDocument,
    addConcept,
    toggleAutoWiki,
    organize,
    relationFollowup,
    compareViews,
    citeFollowup,
    reportFirstVisible,
    suspendVisibleMeasurement,
  };
}
