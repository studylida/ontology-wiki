import type {
  AnswerRequest,
  AnswerOverrides,
  AnswerSettings,
  Draft,
  Relation,
  SourceGroup,
  SourceView,
} from "../types/contracts";
import { conversationRepository } from "../repositories/api";

export function defaultDraft(): Draft {
  return {
    text: "",
    responseMode: "wiki",
    extended: false,
    conceptIds: [],
    sourceRevisionIds: [],
    documentContextIds: [],
    sourceGroups: [],
    aspect: null,
    attachmentIds: [],
    conceptLabels: {},
    sourceLabels: {},
  };
}
export function restoreDraft(
  local: Partial<Draft> | null,
  saved?: Partial<AnswerSettings>,
): Draft {
  const base = defaultDraft();
  const values = { ...base, ...saved, ...local };
  // Browser state is untrusted; a stale draft must not introduce a new response mode.
  return {
    ...values,
    text: typeof values.text === "string" ? values.text : "",
    responseMode: values.responseMode === "analysis" ? "analysis" : "wiki",
    extended: values.extended === true,
    conceptIds: Array.isArray(values.conceptIds) ? values.conceptIds : [],
    sourceRevisionIds: Array.isArray(values.sourceRevisionIds)
      ? values.sourceRevisionIds
      : [],
    documentContextIds: Array.isArray(values.documentContextIds)
      ? values.documentContextIds
      : [],
    attachmentIds: Array.isArray(values.attachmentIds)
      ? values.attachmentIds
      : [],
    sourceGroups: Array.isArray(values.sourceGroups) ? values.sourceGroups : [],
    conceptLabels: validLabels(values.conceptLabels),
    sourceLabels: validLabels(values.sourceLabels),
  };
}
function validLabels(value: unknown): Record<string, string> {
  if (!value || typeof value !== "object" || Array.isArray(value)) return {};
  return Object.fromEntries(
    Object.entries(value).filter(([, label]) => typeof label === "string"),
  );
}
export function buildAnswerRequest(
  draft: Draft,
  conversationId: string | undefined,
  text = draft.text,
  overrides: AnswerOverrides = {},
  requestId: string = crypto.randomUUID(),
): AnswerRequest {
  const message = text.trim();
  if (!message) throw new Error("질문을 입력해 주세요.");
  return {
    clientRequestId: requestId,
    conversationId,
    message,
    responseMode: draft.responseMode,
    extended: draft.extended,
    conceptIds: [...draft.conceptIds],
    sourceRevisionIds: [...draft.sourceRevisionIds],
    documentContextIds: [...draft.documentContextIds],
    sourceGroups: draft.sourceGroups.map((group) => ({ ...group })),
    aspect: draft.aspect || null,
    attachmentIds: [...draft.attachmentIds],
    ...overrides,
  };
}
export const conversationService = {
  submit: (request: AnswerRequest) => conversationRepository.start(request),
  restore: (id: string, signal?: AbortSignal) =>
    conversationRepository.get(id, signal),
  recover: (runId: string, signal?: AbortSignal) =>
    conversationRepository.run(runId, signal),
};
export function relationQuestion(relation: Relation) {
  return `${relation.toName}에 대해 설명하고, ${relation.fromName}과의 관계를 근거와 적용 조건을 함께 알려 주세요.`;
}
export function groupsFromViews(views: SourceView[]): SourceGroup[] {
  const groups = new Map<string, SourceGroup>();
  views.forEach((view) => {
    if (!view.publisherId && !view.sourceType) return;
    const groupId = `${view.publisherId || "unspecified"}:${view.sourceType || "unspecified"}`;
    groups.set(groupId, {
      groupId,
      ...(view.publisherId ? { publisherId: view.publisherId } : {}),
      ...(view.sourceType ? { sourceType: view.sourceType } : {}),
    });
  });
  return [...groups.values()];
}
export function isTerminal(status?: string) {
  return (
    status === "completed" ||
    status === "failed" ||
    status === "cancelled" ||
    status === "interrupted"
  );
}

export const WIKI_SECTIONS = [
  "핵심 설명",
  "목적·원리",
  "사례·조건",
  "관계",
  "출처·부족한 부분",
] as const;
export function splitWiki(content: string): string[] {
  const output = ["", "", "", "", ""];
  let index = 0;
  const normalized = (text: string) =>
    text.replace(/[\s·ㆍ・/&:：\d.()\-]/g, "");
  const aliases = [
    ["핵심설명", "개요"],
    ["목적원리", "목적과원리"],
    ["사례조건", "사례와조건"],
    ["관계"],
    ["출처부족한부분", "출처와부족한부분", "출처한계"],
  ];
  for (const line of content.split("\n")) {
    const heading = /^#{1,3}\s+(.+?)\s*#*$/.exec(line);
    const match = heading
      ? aliases.findIndex((names) => names.includes(normalized(heading[1])))
      : -1;
    if (match >= 0) index = match;
    else output[index] += `${line}\n`;
  }
  return output.map((text) => text.trim());
}
