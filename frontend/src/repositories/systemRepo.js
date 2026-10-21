/**
 * [계층 4] System & Health Repository
 * 백엔드 /api/v1/system과 1:1 통신하는 순수 I/O 클라이언트
 */

import { httpClient } from './httpClient';

export const systemRepo = {
  /**
   * 시스템 상태 및 서브엔진 연결 상태 조회
   * @returns {Promise<import('../types/system.dto').HealthResponseDTO>}
   */
  async getHealth() {
    return httpClient.get('/system/health', { skipAuth: true });
  },

  /**
   * 온톨로지 버전 메타데이터 및 전체 개념/증거 통계 조회
   * @param {string} [clientVersion='v1.2']
   * @returns {Promise<import('../types/system.dto').VersionResponseDTO>}
   */
  async getVersion(clientVersion = 'v1.2') {
    return httpClient.get(`/system/version?clientVersion=${clientVersion}`, { skipAuth: true });
  },

  /**
   * WORM 머클 해시체인 암호학적 무결성 감사 검증 (Level >= 3)
   * @returns {Promise<import('../types/system.dto').AuditIntegrityResponseDTO>}
   */
  async verifyAuditIntegrity() {
    return httpClient.get('/system/audit/verify-integrity');
  }
};
