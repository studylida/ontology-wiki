/**
 * [계층 4] Deep Research & External Literature Repository
 * 백엔드 /api/v1/research 엔드포인트와 1:1 통신하는 순수 I/O 클라이언트
 */

import { httpClient } from './httpClient';

export const researchRepo = {
  /**
   * 과거 외부 문헌 조사 세션 로그 목록 조회
   * @param {{ limit?: number }} [params]
   * @returns {Promise<import('../types/research.dto').ResearchSessionListResponseDTO>}
   */
  async listSessions({ limit = 15 } = {}) {
    return httpClient.get(`/research/sessions?limit=${limit}`);
  },

  /**
   * 외부 문헌 조사 주제 구체화 및 범위 필터 도출
   * @param {{ searchTopic: string, targetInstitutions?: string[], comparisonContext?: Object, clarificationAnswer?: string }} data
   * @returns {Promise<import('../types/research.dto').ResearchClarifyResponseDTO>}
   */
  async clarifyTopic(data) {
    return httpClient.post('/research/clarify', data);
  },

  /**
   * 공인 문헌 발굴 피드 생성 (Deep Research Agent)
   * @param {{ searchTopic: string, targetInstitutions?: string[], comparisonContext?: Object, searchPlan?: Object, clarificationAnswer?: string }} data
   * @returns {Promise<import('../types/research.dto').ResearchDiscoverResponseDTO>}
   */
  async discoverEvidences(data) {
    return httpClient.post('/research/discover', data);
  },

  async continueResearch(sessionId, expectedUpdatedAt) {
    return httpClient.post(`/research/sessions/${sessionId}/continue`, { expectedUpdatedAt });
  },

  /**
   * 발굴 문헌 종합 분석 리포트 및 온톨로지 지식 후보 생성
   * @param {string} sessionId
   * @param {{ selectedEvidenceIds: string[] }} data
   * @returns {Promise<import('../types/research.dto').ResearchSynthesizeResponseDTO>}
   */
  async synthesizeReport(sessionId, data) {
    return httpClient.post(`/research/sessions/${sessionId}/synthesize`, data);
  },

  /**
   * 조사 세션 상세 및 종합 리포트/후보 목록 조회
   * @param {string} sessionId
   * @returns {Promise<import('../types/research.dto').ResearchSynthesizeResponseDTO>}
   */
  async getSession(sessionId) {
    return httpClient.get(`/research/sessions/${sessionId}`);
  },

  /**
   * 지식 후보 ➔ 검토 센터(Tab 3) 거버넌스 큐 등록 (티켓 발행)
   * @param {string} candidateId
   * @param {{ sessionId: string, userNote?: string, author?: string, department?: string }} data
   * @returns {Promise<import('../types/research.dto').ExportCandidateTicketResponseDTO>}
   */
  async exportCandidateTicket(candidateId, data) {
    return httpClient.post(`/research/candidates/${candidateId}/export-ticket`, data);
  }
};
