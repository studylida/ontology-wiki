/**
 * [계층 5] Admin & Governance Console DTOs
 * 백엔드 /api/v1/auth 관리자 엔드포인트의 입력/출력 인터페이스 규약
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
