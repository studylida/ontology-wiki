export function formatDate(value?: string | null) {
  if (!value) return "날짜 미확인";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "날짜 미확인"
    : new Intl.DateTimeFormat("ko-KR", {
        year: "numeric",
        month: "short",
        day: "numeric",
      }).format(date);
}
export function formatCount(value?: number | null) {
  return value == null ? "미확인" : value.toLocaleString("ko-KR");
}
export function formatDuration(value?: number | null) {
  return value == null ? "미확인" : `${(value / 1000).toFixed(2)}초`;
}
export function safeUrl(value?: string | null): string | undefined {
  if (!value) return undefined;
  try {
    const url = new URL(value);
    return ["https:", "http:"].includes(url.protocol) ? url.href : undefined;
  } catch {
    return undefined;
  }
}
export const documentFormLabels = {
  unknown: "형태 미확인",
  original: "원문",
  editorial_summary: "편집 요약",
  edited_derivative: "편집본",
  text_extraction: "원문 텍스트 추출본",
} as const;
export function documentFormLabel(form?: string | null, sourceType?: string | null) {
  if (form && Object.prototype.hasOwnProperty.call(documentFormLabels, form)) return documentFormLabels[form as keyof typeof documentFormLabels];
  if (sourceType === "editorial_summary") return documentFormLabels.editorial_summary;
  if (sourceType === "research_article_text_extraction") return documentFormLabels.text_extraction;
  return documentFormLabels.unknown;
}
export const reviewLabel: Record<string, string> = {
  pending: "검토 대기",
  approved: "승인",
  rejected: "반려",
  held: "보류",
  withdrawn: "철회",
};
export const indexLabel: Record<string, string> = {
  pending: "검색 반영 대기",
  queued: "검색 반영 대기",
  not_indexed: "검색 미반영",
  indexed: "검색 반영",
  active: "검색 반영",
  ready: "검색 반영",
  running: "색인 생성 중",
  processing: "색인 생성 중",
  failed: "검색 반영 실패",
  withdrawn: "검색 제외",
  stale: "갱신 대기",
};
export const readScopeLabel: Record<string, string> = {
  metadata: "서지정보만 확인",
  abstract: "초록 확인",
  full: "본문 확인",
  partial: "본문 일부 확인",
  failed: "내용 확인 실패",
};
export function organizationReason(reason?: string | null) {
  const reasons: Record<string, string> = {
    no_reusable_content: "별도로 재사용할 내용이 없어 저장하지 않았습니다.",
    already_organized: "이 메시지는 이미 정리되었습니다.",
    automatic_organization_disabled:
      "자동 정리가 꺼져 있거나 이 대화가 제외되었습니다.",
    source_access_changed: "원문 접근 권한이 변경되었습니다.",
    source_access_or_metadata_changed:
      "원문 접근 권한 또는 출처 정보가 변경되었습니다.",
    message_excluded: "삭제·제외된 원메시지라 자동 정리를 생략했습니다.",
    answer_not_completed: "완료된 답변만 정리할 수 있습니다.",
    target_page_deleted: "대상 개인 위키가 삭제되었습니다.",
    page_changed_by_user: "사용자가 수정한 내용과 충돌해 덮어쓰지 않았습니다.",
    conditions_differ_or_target_incomplete:
      "적용 조건이 다르거나 대상 기록이 불완전해 병합하지 않았습니다.",
    matching_page_already_exists:
      "같은 주제의 기록이 있어 새 페이지를 추가하지 않았습니다.",
    job_cancelled_or_finished: "이미 취소되거나 종료된 작업입니다.",
    organization_context_too_large: "정리할 문맥이 허용 범위를 초과했습니다.",
    original_answer_changed: "원래 답변이 변경되어 저장하지 않았습니다.",
  };
  return reason
    ? reasons[reason] || `처리 사유: ${reason}`
    : "처리 사유가 제공되지 않았습니다.";
}
