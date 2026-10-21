/**
 * [계층 4] Admin & Governance Repository
 * 수석 검토관/관리자 전용 /api/v1/auth 엔드포인트와 통신하는 순수 I/O 클라이언트
 */

import { httpClient } from './httpClient';

export const adminRepo = {
  /**
   * L3 비인가 열람 신청 전체 큐 목록 조회
   * @param {{ status?: string }} [params]
   * @returns {Promise<Array<import('../types/admin.dto').AccessRequestDTO>>}
   */
  async listAccessRequests({ status } = {}) {
    const q = status ? `?status=${status}` : '';
    return httpClient.get(`/auth/access-requests${q}`);
  },

  /**
   * L3 비인가 열람 신청 승인
   * @param {string} requestId
   * @returns {Promise<import('../types/admin.dto').AccessRequestDTO>}
   */
  async approveAccessRequest(requestId) {
    return httpClient.post(`/auth/access-requests/${requestId}/approve`);
  },

  /**
   * L3 비인가 열람 신청 반려
   * @param {string} requestId
   * @param {{ reason?: string }} [data]
   * @returns {Promise<import('../types/admin.dto').AccessRequestDTO>}
   */
  async rejectAccessRequest(requestId, data = {}) {
    return httpClient.post(`/auth/access-requests/${requestId}/reject`, data);
  },

  /**
   * 등록 엔지니어 계정 목록 조회
   * @param {{ limit?: number, offset?: number, role?: string, level?: number, search?: string }} [params]
   * @returns {Promise<Array<import('../types/admin.dto').AdminUserDTO>>}
   */
  async listUsers({ limit = 50, offset = 0, role, level, search } = {}) {
    const q = new URLSearchParams();
    q.append('limit', String(limit));
    q.append('offset', String(offset));
    if (role) q.append('role', role);
    if (level) q.append('level', String(level));
    if (search) q.append('search', search);

    return httpClient.get(`/auth/users?${q.toString()}`);
  },

  /**
   * 엔지니어 권한 레벨 및 계정 활성 상태 변경
   * @param {string} userId
   * @param {{ level: number, isActive?: boolean }} data
   * @returns {Promise<import('../types/admin.dto').AdminUserDTO>}
   */
  async updateUserLevel(userId, data) {
    return httpClient.patch(`/auth/users/${userId}/level`, data);
  },

  /**
   * 엔지니어 계정 삭제 (퇴사/차단)
   * @param {string} userId
   * @returns {Promise<{ message: string }>}
   */
  async deleteUser(userId) {
    return httpClient.delete(`/auth/users/${userId}`);
  }
};
