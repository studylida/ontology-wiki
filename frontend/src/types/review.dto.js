/**
 * [계층 5] Review & Governance DTOs
 * Backend (backend/app/schemas/review.py)와 1:1 대칭 매핑
 */

/**
 * @typedef {Object} IntegrityReportDTO
 * @property {number} confidenceScore - AI 신뢰도 점수 (0~100)
 * @property {boolean} physicalMarginValid - 물리 안전 마진 유효 여부
 * @property {Array<string>} citedEvidenceIds - 보존된 공인 출처 ID 목록
 * @property {Array<string>} [missingCitations] - 누락 감지된 출처 목록
 * @property {Array<string>} [warnings] - 도메인 가드레일 경고 목록
 */

/**
 * @typedef {Object} DirectiveHistoryItemDTO
 * @property {string} timestamp
 * @property {string} directiveText
 * @property {string} [appliedSummary]
 * @property {string} author
 */

/**
 * @typedef {Object} ReviewTicketDTO
 * @property {string} id - 티켓 식별자 (예: rev-20261021-0f06)
 * @property {string} conceptId - 대상 온톨로지 개념 ID
 * @property {string} [conceptTitle]
 * @property {string} title - 티켓 제목
 * @property {string} reviewType - minor_revision | new_concept | major_correction
 * @property {string} author - 발의자 성명
 * @property {string} department - 발의 부서
 * @property {string} submittedAt - 발의 일시
 * @property {'pending'|'approved'|'rejected'} status - 심사 상태
 * @property {string} [sourceSessionId]
 * @property {string} originType - human_engineer | agent_synthesis
 * @property {string} currentVersion - 현재 버전 (예: v1.2.0)
 * @property {string} targetVersion - 승계 대상 버전 (예: v1.2.1 또는 v1.3.0)
 * @property {string} [currentContent] - 개정 전 기존 본문
 * @property {string} [aiMergedDraft] - AI 합성 백서 초안
 * @property {string} [humanEdits] - 전문가 직접 수정 본문
 * @property {Object} [structuredPatches] - 구조화 패치 데이터
 * @property {IntegrityReportDTO} [integrityReport] - 무결성 진단 지표
 * @property {Array<DirectiveHistoryItemDTO>} [directiveHistory] - 지시문 수정 이력
 * @property {string} [overrideReason] - 물리 마진 초과 사유
 * @property {string|null} [approvedAt]
 * @property {string|null} [approvedBy]
 * @property {string|null} [appliedConceptVersion]
 * @property {number} ticketVersion - 낙관적 락 판본 번호
 * @property {string|null} currentEditor - 현재 편집 락 점유자
 * @property {boolean} isLocked - 편집 락 점유 여부
 */

/**
 * @typedef {Object} PresenceLockRequestDTO
 * @property {'acquire'|'renew'|'steal'|'release'} action
 * @property {string} userId
 * @property {number} [ttl=600] - 최대 점유 허용 초 (기본 10분: 600초)
 */

/**
 * @typedef {Object} PresenceLockResponseDTO
 * @property {boolean} acquired
 * @property {string|null} holder
 * @property {boolean} isLocked
 * @property {string} message
 * @property {number} [remainingSeconds]
 */

/**
 * @typedef {Object} DirectiveRequestDTO
 * @property {string} directiveText - 전문가 자연어 보완 지시문
 * @property {string} [overrideReason]
 * @property {boolean} [allowCitationDeletion=false]
 * @property {Array<string>} [deprecatedCitations]
 */

/**
 * @typedef {Object} HumanEditsRequestDTO
 * @property {string} editedContent - 전문가 수정 본문
 * @property {number} ticketVersion - 낙관적 락 판본
 * @property {string} [overrideReason]
 * @property {boolean} [allowCitationDeletion=false]
 * @property {Array<string>} [deprecatedCitations]
 */

/**
 * @typedef {Object} ReviewTicketApproveRequestDTO
 * @property {string} approvedBy - 승인 심사관 성명
 * @property {string} [overrideReason]
 * @property {string} targetVersion - 최종 승계 세맨틱 버전
 * @property {string} [humanEdits]
 * @property {boolean} [allowCitationDeletion=false]
 * @property {Array<string>} [deprecatedCitations]
 */

/**
 * @typedef {Object} ReviewTicketRejectRequestDTO
 * @property {string} rejectedBy - 반려 심사관 성명
 * @property {string} rejectReason - 반려 사유
 */

/**
 * @typedef {Object} WikiPreviewResponseDTO
 * @property {string} ticketId
 * @property {string} conceptId
 * @property {string} targetVersion
 * @property {Object} previewConcept
 * @property {Object} diffSummary
 */

/**
 * @typedef {Object} AuditLogDTO
 * @property {string} id
 * @property {string} entityType
 * @property {string} entityId
 * @property {string} action
 * @property {string} performedBy
 * @property {string} timestamp
 * @property {string} entryHash
 * @property {string} previousLogHash
 * @property {Object} [details]
 */
