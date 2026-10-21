/**
 * [계층 4] Auth & RBAC Repository
 * 백엔드 /api/v1/auth 16개 엔드포인트와 1:1 대칭 통신하는 순수 I/O 모듈
 */

import { httpClient } from './httpClient';

export const authRepo = {
  /**
   * 사내 로그인
   * @param {import('../types/auth.dto').UserLoginDTO} loginData
   * @returns {Promise<import('../types/auth.dto').TokenResponseDTO>}
   */
  async login(loginData) {
    return httpClient.post('/auth/login', loginData, { skipAuth: true });
  },

  /**
   * 사내 엔지니어 회원가입
   * @param {import('../types/auth.dto').UserRegisterDTO} registerData
   * @returns {Promise<import('../types/auth.dto').TokenResponseDTO>}
   */
  async register(registerData) {
    return httpClient.post('/auth/register', registerData, { skipAuth: true });
  },

  /**
   * 현재 로그인 사용자 정보 조회 (SPA 새로고침 시 세션 복원)
   * @returns {Promise<import('../types/auth.dto').UserDTO>}
   */
  async getMe() {
    return httpClient.get('/auth/me');
  },

  /**
   * 토큰 수동/명시적 갱신
   * @returns {Promise<import('../types/auth.dto').TokenResponseDTO>}
   */
  async refreshToken() {
    return httpClient.post('/auth/refresh', {});
  },

  /**
   * 비밀번호 변경
   * @param {{ oldPassword: string, newPassword: string }} data
   */
  async changePassword(data) {
    return httpClient.post('/auth/change-password', data);
  },

  /**
   * 본인 계정 탈퇴/비활성화 (Soft Delete)
   */
  async deactivateSelf() {
    return httpClient.delete('/auth/me');
  },

  /**
   * Tier 3 대외비 지식 열람 권한 신청
   * @param {{ conceptId: string, reason: string }} data
   * @returns {Promise<import('../types/auth.dto').AccessRequestDTO>}
   */
  async createAccessRequest(data) {
    return httpClient.post('/auth/access-requests', data);
  },

  /**
   * 내가 신청한 열람 권한 내역 조회
   * @returns {Promise<Array<import('../types/auth.dto').AccessRequestDTO>>}
   */
  async getMyAccessRequests() {
    return httpClient.get('/auth/access-requests/my');
  },

  /**
   * 대기 중인 본인 열람 신청 취소
   * @param {string} requestId
   */
  async cancelAccessRequest(requestId) {
    return httpClient.delete(`/auth/access-requests/${requestId}`);
  },

  // ── 수석 검토관(Level >= 3) 심사 엔드포인트 ──
  /**
   * 열람 신청 심사 큐 조회
   * @param {{ status?: string, limit?: number, offset?: number }} [params]
   */
  async getAdminAccessRequests(params = {}) {
    const query = new URLSearchParams();
    if (params.status) query.append('status', params.status);
    if (params.limit) query.append('limit', String(params.limit));
    if (params.offset) query.append('offset', String(params.offset));
    const qs = query.toString();
    return httpClient.get(`/auth/access-requests${qs ? `?${qs}` : ''}`);
  },

  /**
   * 열람 신청 승인
   * @param {string} requestId
   * @param {string} [comment]
   */
  async approveAccessRequest(requestId, comment = '') {
    return httpClient.post(`/auth/access-requests/${requestId}/approve`, { comment });
  },

  /**
   * 열람 신청 반려
   * @param {string} requestId
   * @param {string} [comment]
   */
  async rejectAccessRequest(requestId, comment = '') {
    return httpClient.post(`/auth/access-requests/${requestId}/reject`, { comment });
  },

  /**
   * 승인된 열람 권한 회수
   * @param {string} requestId
   * @param {string} [comment]
   */
  async revokeAccessRequest(requestId, comment = '') {
    return httpClient.post(`/auth/access-requests/${requestId}/revoke`, { comment });
  },

  // ── 관리자(Level >= 4) 엔지니어 관리 엔드포인트 ──
  /**
   * 전체 사용자 목록 조회
   */
  async listUsers(params = {}) {
    const query = new URLSearchParams();
    if (params.role) query.append('role', params.role);
    if (params.minLevel) query.append('min_level', String(params.minLevel));
    if (params.limit) query.append('limit', String(params.limit));
    if (params.offset) query.append('offset', String(params.offset));
    const qs = query.toString();
    return httpClient.get(`/auth/users${qs ? `?${qs}` : ''}`);
  },

  /**
   * 사용자 권한 레벨 및 활성화 상태 변경
   * @param {string} userId
   * @param {{ level: number, isActive?: boolean }} data
   */
  async updateUserLevel(userId, data) {
    return httpClient.patch(`/auth/users/${userId}/level`, data);
  },

  /**
   * 사용자 비활성화/퇴사 처리
   * @param {string} userId
   */
  async deactivateUser(userId) {
    return httpClient.delete(`/auth/users/${userId}`);
  }
};
