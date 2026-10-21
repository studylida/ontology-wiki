/**
 * [계층 3] Auth & RBAC Domain Service
 * UI 및 React에 비의존적인 순수 도메인 권한 및 역할 로직
 */

export const authService = {
  /**
   * 사용자 권한 레벨별 배지 정보
   * @param {number} level - 1: 게스트, 2: 현장 엔지니어, 3: 수석 검토관, 4: 시스템 관리자
   */
  getRoleBadge(level) {
    switch (level) {
      case 4:
        return {
          label: 'Level 4 관리자',
          roleName: '시스템 관리자',
          className: 'badge-admin',
          bgStyle: 'var(--accent-danger-light)',
          textStyle: 'var(--accent-danger)',
          borderStyle: 'rgba(239, 68, 68, 0.3)',
          icon: '👑'
        };
      case 3:
        return {
          label: 'Level 3 수석 검토관',
          roleName: '수석 검토관',
          className: 'badge-chief',
          bgStyle: 'var(--accent-primary-light)',
          textStyle: 'var(--accent-primary)',
          borderStyle: 'rgba(37, 99, 235, 0.3)',
          icon: '🛡️'
        };
      case 2:
        return {
          label: 'Level 2 현장 엔지니어',
          roleName: '현장 엔지니어',
          className: 'badge-engineer',
          bgStyle: 'var(--accent-success-light)',
          textStyle: 'var(--accent-success)',
          borderStyle: 'rgba(16, 185, 129, 0.3)',
          icon: '⚙️'
        };
      case 1:
      default:
        return {
          label: 'Level 1 게스트',
          roleName: '게스트',
          className: 'badge-guest',
          bgStyle: 'var(--bg-surface-3)',
          textStyle: 'var(--text-muted)',
          borderStyle: 'var(--border-color)',
          icon: '👤'
        };
    }
  },

  /**
   * 관리자 콘솔 접근 권한 (Level >= 3)
   * @param {import('../types/auth.dto').UserDTO|null} user
   * @returns {boolean}
   */
  canAccessAdmin(user) {
    return Boolean(user && user.level >= 3);
  },

  /**
   * 사용자 관리 권한 (Level >= 4)
   * @param {import('../types/auth.dto').UserDTO|null} user
   * @returns {boolean}
   */
  canManageUsers(user) {
    return Boolean(user && user.level >= 4);
  },

  /**
   * 특정 개념에 대해 L3 극비 파라미터 열람 권한이 있는지 판정
   * @param {import('../types/auth.dto').UserDTO|null} user
   * @param {Array<import('../types/auth.dto').AccessRequestDTO>} myRequests
   * @param {string} conceptId
   * @returns {{ hasAccess: boolean, requestStatus: 'none'|'pending'|'approved'|'rejected' }}
   */
  checkL3Access(user, myRequests = [], conceptId) {
    if (!user) {
      return { hasAccess: false, requestStatus: 'none' };
    }
    // Level 3 이상은 사내 전 개념 L3 열람 인가 기본 부여
    if (user.level >= 3) {
      return { hasAccess: true, requestStatus: 'approved' };
    }

    // 개별 열람 신청 내역 탐색
    const matchingRequest = myRequests.find((r) => r.conceptId === conceptId);
    if (!matchingRequest) {
      return { hasAccess: false, requestStatus: 'none' };
    }

    if (matchingRequest.status === 'approved') {
      return { hasAccess: true, requestStatus: 'approved', request: matchingRequest };
    }

    return {
      hasAccess: false,
      requestStatus: matchingRequest.status,
      request: matchingRequest
    };
  }
};
