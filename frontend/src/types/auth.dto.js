/**
 * [계층 5] Auth DTO & Schemas
 * Backend Pydantic DTO (backend/app/schemas/auth.py)와 1:1 대칭 매핑
 */

/**
 * @typedef {Object} UserDTO
 * @property {string} id - 사원번호/식별자 (예: EMP-ADMIN-001)
 * @property {string} username - 로그인 아이디
 * @property {string} name - 실명
 * @property {string} department - 소속 부서
 * @property {string} role - 역할 식별자 (admin | chief_reviewer | engineer | guest)
 * @property {number} level - 권한 등급 (1: 게스트, 2: 현장 엔지니어, 3: 수석 검토관, 4: 시스템 관리자)
 * @property {boolean} isActive - 활성화 상태
 * @property {string|null} [createdAt] - 생성 일시
 */

/**
 * @typedef {Object} TokenResponseDTO
 * @property {string} accessToken - 24시간 유효 JWT 토큰
 * @property {string} tokenType - 토큰 타입 (Bearer)
 * @property {number} expiresIn - 만료 시간 (초)
 * @property {UserDTO} user - 사용자 프로필
 */

/**
 * @typedef {Object} UserLoginDTO
 * @property {string} username - 로그인 아이디
 * @property {string} password - 비밀번호
 */

/**
 * @typedef {Object} UserRegisterDTO
 * @property {string} username - 로그인 아이디 (최소 3자)
 * @property {string} password - 비밀번호 (최소 6자)
 * @property {string} name - 성명 (최소 2자)
 * @property {string} department - 소속 부서 (최소 2자)
 */

/**
 * @typedef {Object} AccessRequestDTO
 * @property {string} id
 * @property {string} userId
 * @property {string|null} [userName]
 * @property {string|null} [userDepartment]
 * @property {string} conceptId
 * @property {string} conceptTitle
 * @property {string} reason
 * @property {'pending'|'approved'|'rejected'|'revoked'} status
 * @property {string|null} [reviewedBy]
 * @property {string|null} [reviewedAt]
 * @property {string|null} [reviewComment]
 * @property {string|null} [createdAt]
 */

/**
 * DTO 유효성 검증 헬퍼
 */
export const validateLoginDTO = (data) => {
  const errors = {};
  if (!data?.username || data.username.trim().length === 0) {
    errors.username = '아이디를 입력해 주세요.';
  }
  if (!data?.password || data.password.length === 0) {
    errors.password = '비밀번호를 입력해 주세요.';
  }
  return {
    isValid: Object.keys(errors).length === 0,
    errors
  };
};

export const validateRegisterDTO = (data) => {
  const errors = {};
  if (!data?.username || data.username.trim().length < 3) {
    errors.username = '아이디는 최소 3자 이상이어야 합니다.';
  }
  if (!data?.password || data.password.length < 6) {
    errors.password = '비밀번호는 최소 6자 이상이어야 합니다.';
  }
  if (!data?.name || data.name.trim().length < 2) {
    errors.name = '성명은 최소 2자 이상이어야 합니다.';
  }
  if (!data?.department || data.department.trim().length < 2) {
    errors.department = '소속 부서를 입력해 주세요.';
  }
  return {
    isValid: Object.keys(errors).length === 0,
    errors
  };
};
