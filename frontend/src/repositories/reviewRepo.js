/**
 * [계층 4] Review Tickets & Governance Repository
 * 백엔드 /api/v1/review-tickets 10개 엔드포인트와 1:1 통신하는 순수 I/O 클라이언트
 */

import { httpClient } from './httpClient';

export const reviewRepo = {
  /**
   * 티켓 목록 조회 (상태 필터링, 최신순 정렬)
   * @param {{ status?: string, conceptId?: string, limit?: number, offset?: number }} [params]
   * @returns {Promise<Array<import('../types/review.dto').ReviewTicketDTO>>}
   */
  async getTickets(params = {}) {
    const qs = new URLSearchParams();
    if (params.status) qs.append('status', params.status);
    if (params.conceptId) qs.append('concept_id', params.conceptId);
    if (params.limit) qs.append('limit', String(params.limit));
    if (params.offset) qs.append('offset', String(params.offset));
    const query = qs.toString();
    return httpClient.get(`/review-tickets${query ? `?${query}` : ''}`);
  },

  /**
   * 티켓 상세 조회
   * @param {string} ticketId
   * @returns {Promise<import('../types/review.dto').ReviewTicketDTO>}
   */
  async getTicketDetail(ticketId) {
    return httpClient.get(`/review-tickets/${ticketId}`);
  },

  /**
   * 동시 편집 락(Presence Lock) 관리: acquire, renew, steal, release
   * @param {string} ticketId
   * @param {import('../types/review.dto').PresenceLockRequestDTO} data
   * @returns {Promise<import('../types/review.dto').PresenceLockResponseDTO>}
   */
  async managePresence(ticketId, data) {
    return httpClient.post(`/review-tickets/${ticketId}/presence`, data);
  },

  /**
   * 전문가 자연어 보완 지시문 적용
   * @param {string} ticketId
   * @param {import('../types/review.dto').DirectiveRequestDTO} data
   * @returns {Promise<import('../types/review.dto').ReviewTicketDTO>}
   */
  async applyDirective(ticketId, data) {
    return httpClient.post(`/review-tickets/${ticketId}/directive`, data);
  },

  /**
   * 전문가 직접 수정 본문 저장 (인용구 보존 및 버전 검증)
   * @param {string} ticketId
   * @param {import('../types/review.dto').HumanEditsRequestDTO} data
   * @returns {Promise<import('../types/review.dto').HumanEditsResponseDTO>}
   */
  async saveHumanEdits(ticketId, data) {
    return httpClient.put(`/review-tickets/${ticketId}/human-edits`, data);
  },

  /**
   * 공용 위키 사전 렌더링 미리보기 조회
   * @param {string} ticketId
   * @param {boolean} [highlight=true]
   * @returns {Promise<import('../types/review.dto').WikiPreviewResponseDTO>}
   */
  async getWikiPreview(ticketId, request = {}) {
    return httpClient.post(`/review-tickets/${ticketId}/wiki-preview`, request);
  },

  /**
   * 티켓 최종 승인 및 온톨로지 정식 반영
   * @param {string} ticketId
   * @param {import('../types/review.dto').ReviewTicketApproveRequestDTO} data
   * @returns {Promise<Object>}
   */
  async approveTicket(ticketId, data) {
    return httpClient.post(`/review-tickets/${ticketId}/approve`, data);
  },

  /**
   * 티켓 반려 의결
   * @param {string} ticketId
   * @param {import('../types/review.dto').ReviewTicketRejectRequestDTO} data
   * @returns {Promise<Object>}
   */
  async rejectTicket(ticketId, data) {
    return httpClient.post(`/review-tickets/${ticketId}/reject`, data);
  },

  /**
   * WORM 불변 머클 감사 로그 이력 조회
   * @param {string} ticketId
   * @returns {Promise<Array<import('../types/review.dto').AuditLogDTO>>}
   */
  async getAuditLogs(ticketId) {
    return httpClient.get(`/review-tickets/${ticketId}/audit-logs`);
  },

  /**
   * 신규 개정안 또는 신규 개념 발의 티켓 생성
   * @param {Object} data
   * @returns {Promise<Object>}
   */
  async createTicket(data) {
    return httpClient.post('/review-tickets', data);
  }
};
