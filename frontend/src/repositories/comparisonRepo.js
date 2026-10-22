/**
 * [계층 4] Comparison & Alternative Reasoning Repository
 * 백엔드 /api/v1/comparison 및 /api/v1/comparison-sessions와 1:1 통신하는 순수 I/O 클라이언트
 */

import { httpClient } from './httpClient';

export const comparisonRepo = {
  async listConcepts() {
    return httpClient.get('/comparison/concepts');
  },

  async addResearchEvidence(sessionId, data) {
    return httpClient.post(`/comparison-sessions/${sessionId}/research-evidence`, data);
  },
  /**
   * 자연어 질문 구체화 및 등록 개념 비교 후보 도출 (Track 1)
   * @param {{ query: string, baseConceptId?: string, customAxes?: string[] }} data
   * @returns {Promise<import('../types/comparison.dto').ClarifyResponseDTO>}
   */
  async clarify(data) {
    return httpClient.post('/comparison/clarify', data);
  },

  /**
   * 비교 분석 세션 생성
   * @param {import('../types/comparison.dto').ComparisonSessionCreateDTO} data
   * @returns {Promise<import('../types/comparison.dto').ComparisonSessionDTO>}
   */
  async createSession(data) {
    return httpClient.post('/comparison-sessions', data);
  },

  /**
   * 비교 분석 세션 상세 조회
   * @param {string} sessionId
   * @returns {Promise<import('../types/comparison.dto').ComparisonSessionDTO>}
   */
  async getSession(sessionId) {
    return httpClient.get(`/comparison-sessions/${sessionId}`);
  },

  /**
   * 다차원 축 비교 매트릭스 계산 및 갱신
   * @param {string} sessionId
   * @param {Object} [data]
   * @returns {Promise<{ matrix: Array<import('../types/comparison.dto').ComparisonMatrixRowDTO> }>}
   */
  async updateMatrix(sessionId, data = {}) {
    return httpClient.post(`/comparison-sessions/${sessionId}/matrix`, data);
  },

  /**
   * 꼬리질문 튜닝 상담 및 실시간 물리 마진 검증
   * @param {string} sessionId
   * @param {import('../types/comparison.dto').TuneAdvisorRequestDTO} data
   * @returns {Promise<import('../types/comparison.dto').TuneAdvisorResponseDTO>}
   */
  async tuneAdvisor(sessionId, data) {
    return httpClient.post(`/comparison-sessions/${sessionId}/tune-advisor`, data);
  },

  /**
   * 비교 분석 결과 및 튜닝 상담을 Tab 3 거버넌스 검토 티켓으로 내보내기
   * @param {string} sessionId
   * @param {import('../types/comparison.dto').ExportReviewRequestDTO} data
   * @returns {Promise<{ ticketId: string, message: string }>}
   */
  async exportToReviewTicket(sessionId, data) {
    return httpClient.post(`/comparison-sessions/${sessionId}/export-review`, data);
  }
};
