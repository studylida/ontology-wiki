/**
 * [계층 4] Review Tickets & Governance Repository
 * 백엔드 /api/v1/review-tickets와 1:1 통신하는 순수 I/O 클라이언트
 */

import { httpClient } from './httpClient';

export const reviewRepo = {
  /**
   * 새 개정안 또는 신규 개념 편입 발의 티켓 등록
   * @param {Object} ticketData
   * @returns {Promise<Object>}
   */
  async createTicket(ticketData) {
    return httpClient.post('/review-tickets', ticketData);
  },

  /**
   * 티켓 목록 조회 (Tab 3에서 본격 사용)
   * @param {Object} [params]
   */
  async listTickets(params = {}) {
    const qs = new URLSearchParams(params).toString();
    return httpClient.get(`/review-tickets${qs ? `?${qs}` : ''}`);
  },

  /**
   * 티켓 상세 조회
   * @param {string} ticketId
   */
  async getTicketDetail(ticketId) {
    return httpClient.get(`/review-tickets/${ticketId}`);
  }
};
