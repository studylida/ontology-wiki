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
 * @property {Array<Object>} [structuredPatches] - 기존 분류 패치와 /wikiDraft의 자료별 검증 기여
 * @property {IntegrityReportDTO} [integrityReport] - 무결성 진단 지표
 * @property {Array<DirectiveHistoryItemDTO>} [directiveHistory] - 지시문 수정 이력
 * @property {string} [overrideReason] - 물리 마진 초과 사유
 * @property {string|null} [approvedAt]
 * @property {string|null} [approvedBy]
 * @property {string|null} [appliedConceptVersion]
 * @property {number} ticketVersion - 낙관적 락 판본 번호
 * @property {ReviewWorkingDraftDTO} [workingDraft]
 * @property {"legacy"|"structured"} editingMode
 * @property {boolean} canUndo
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
 * @property {string} [editedContent] - 저장 전 현재 개요 편집본
 * @property {number} [ticketVersion]
 * @property {boolean} [structuredDraft=false]
 * @property {string[]} [targetSections]
 * @property {boolean} [undoLast=false]
 * @property {string} [overrideReason]
 * @property {boolean} [allowCitationDeletion=false]
 * @property {Array<string>} [deprecatedCitations]
 */

/**
 * @typedef {Object} HumanEditsRequestDTO
 * @property {string} [editedContent] - legacy summary request; cannot accompany changes
 * @property {WorkingDraftChangesDTO} [changes] - structured whole-draft changes
 * @property {number} ticketVersion - 낙관적 락 판본
 * @property {string} [overrideReason]
 * @property {boolean} [allowCitationDeletion=false]
 * @property {Array<string>} [deprecatedCitations]
 */

/**
 * @typedef {Object} ReviewTicketApproveRequestDTO
 * @property {string} [approvedBy] - server uses authenticated actor
 * @property {number} ticketVersion
 * @property {string} [previewSignature] - required for structured draft approval
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
 * @property {Object|null} baselineConcept - 현재 공용 위키의 전체 목차와 권한 적용 결과
 * @property {number} ticketVersion
 * @property {string} previewSignature
 * @property {ReviewWorkingDraftDTO} workingDraft
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

/**
 * @typedef {Object} ConceptPlacementRecommendRequestDTO
 * @property {string} title
 * @property {string} [summary]
 */

/**
 * @typedef {Object} ConceptPlacementRecommendResponseDTO
 * @property {'device'|'unit_process'|'operations'|'materials_infra'} domainFacet
 * @property {number} scaleLevel - 위키의 물리적 규모 1~5
 * @property {string} scaleName
 * @property {string} processCategory
 * @property {string|null} parentConceptId
 * @property {string|null} parentConceptTitle
 * @property {string} reasoning
 */

/**
 * @typedef {Object} ReviewSectionResultDTO
 * @property {'summary'|'principles'|'limitations'|'perspectiveCases'|'relations'|'evidences'} field
 * @property {string} label
 * @property {'보강됨'|'변경 없음'|'근거 부족'|'충돌 확인 필요'} status
 */

/**
 * @typedef {Object} ReviewWorkingDraftDTO
 * @property {1} schemaVersion
 * @property {Object} content - summary/purpose, editable item lists, public source/concept options
 * @property {{canEdit:boolean,canEditConfidential:boolean,canChangeConfidentiality:boolean}} permissions
 *
 * @typedef {Object} ReviewItemChangesDTO
 * @property {Array<{editorId:string}>} [upsert] - typed fields per section; omitted fields are preserved
 * @property {string[]} [remove] - explicit removal in this draft only
 * @property {string[]} [order] - all resulting editor IDs, without duplicates
 *
 * @typedef {Object} WorkingDraftChangesDTO
 * @property {string} [summary]
 * @property {string} [purpose]
 * @property {ReviewItemChangesDTO} [principles]
 * @property {ReviewItemChangesDTO} [limitations]
 * @property {ReviewItemChangesDTO} [perspectiveCases] - nested specifications use the same change shape
 * @property {ReviewItemChangesDTO} [previousSteps]
 * @property {ReviewItemChangesDTO} [nextSteps]
 * @property {ReviewItemChangesDTO} [alternatives]
 * @property {ReviewItemChangesDTO} [partOf]
 * @property {ReviewItemChangesDTO} [isA]
 * @property {ReviewItemChangesDTO} [evidences]
 *
 * @typedef {Object} HumanEditsResponseDTO
 * @property {string} ticketId
 * @property {number} ticketVersion
 * @property {string} humanEdits - compatibility summary only
 * @property {ReviewWorkingDraftDTO} workingDraft
 * @property {Object} integrityReport
 * @property {string} updatedAt
 */
