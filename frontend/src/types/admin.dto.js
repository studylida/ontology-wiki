/**
 * [계층 5] Admin & Governance Console DTOs
 * 백엔드 /api/v1/auth 관리자 엔드포인트의 입력/출력 인터페이스 규약
 */

/**
 * @typedef {Object} SourceConceptPreviewDTO
 * @property {string} conceptId
 * @property {{complete: boolean, processedParts: number, totalParts: number, processedCharacters: number, totalCharacters: number, sourceHash: string}|null} sourceCoverage
 * @property {Array<{perspectiveTitle:string,narrative:string,specifications:import("./concept.dto").SpecificationDTO[]}>} perspectiveCases
 * @property {Object|null} mergedPreview - Service가 계산한 보존·보강 후 실제 저장 본문
 * @property {string[]} missingFields - 병합 후에도 내용이 없는 항목
 * @property {Object[]} classificationProposals - 원문별 분류 제안과 사유
 * @property {boolean} classificationConflict - 원문 구간 간 분류 제안 충돌
 * @property {boolean} [classificationConfirmed] - 관리자가 명시적으로 확정한 로컬 검토 상태
 * @property {string[]} applyBlockers - 적용을 막는 사유
 * @property {string[]} validationWarnings - 미확인 근거·보존·보류 안내
 */

/**
 * @typedef {Object} AccessRequestDTO
 * @property {string} id - 신청 식별자 (예: 'req-20261021-xxxx')
 * @property {string} userId - 신청 엔지니어 ID
 * @property {string} [userName] - 신청 엔지니어 이름
 * @property {string} [userDepartment] - 부서
 * @property {string} targetConceptId - L3 보안 대상 개념 ID
 * @property {string} reason - 열람 신청 사유
 * @property {'pending'|'approved'|'rejected'} status - 심사 상태
 * @property {string} submittedAt - 신청 일시
 * @property {string|null} [reviewedBy] - 심사자
 * @property {string|null} [reviewedAt] - 심사 일시
 * @property {string|null} [expiresAt] - 열람 만료 일시
 */

/**
 * @typedef {Object} AdminUserDTO
 * @property {string} id
 * @property {string} username
 * @property {string} name
 * @property {string} department
 * @property {'guest'|'line_engineer'|'chief_reviewer'|'admin'} role
 * @property {number} level - 권한 레벨 (1: 게스트, 2: 현장 엔지니어, 3: 수석 검토관, 4: 관리자)
 * @property {boolean} isActive - 활성화 상태
 * @property {string} [createdAt]
 */

/**
 * @typedef {Object} ExtractionStateDTO
 * @property {'idle'|'running'|'finished'|'error'|'interrupted'} state
 * @property {string|null} runId - 같은 서버 프로세스의 최신 작업 SSE 재연결 ID
 * @property {string[]} docIds - 최신 작업 또는 명시적 전체 목록 이어하기 범위
 * @property {number} preservedCount - 재추출하지 않고 보존할 완료 문서 수
 * @property {string|null} interruptedDocId
 */
