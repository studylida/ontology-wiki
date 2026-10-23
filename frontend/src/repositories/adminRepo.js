/**
 * [계층 4] Admin & Governance Repository
 * 수석 검토관/관리자 전용 /api/v1/auth 엔드포인트와 통신하는 순수 I/O 클라이언트
 */

import { httpClient } from './httpClient';
import { tokenService } from '../services/tokenService';

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
  },

  // -------------------------------------------------------------------------
  // [관리자 전용] 원천 백서(Sources) 지식 추출 & 온톨로지 인제스천 I/O
  // -------------------------------------------------------------------------

  /**
   * sources/ 디렉터리 원천 기술 백서 목록 및 추출 상태 조회
   * @returns {Promise<{ documents: Array<Object>, totalCount: number, succeededCount: number, pendingCount: number, modifiedCount: number }>}
   */
  async listSourceDocuments() {
    return httpClient.get('/admin/sources');
  },

  /**
   * 현재 서버 프로세스의 최신 추출 상태 또는 이전 중단 이력 조회
   * @returns {Promise<import('../types/admin.dto').ExtractionStateDTO>}
   */
  async getExtractionState() {
    return httpClient.get('/admin/sources/extraction-state');
  },

  /** 특정 문서의 최근 추출된 위키 DTO 미리보기 데이터 조회 */
  async getDocumentPreview(docId) {
    return httpClient.get(`/admin/sources/${docId}/preview`);
  },

  /**
   * 선택된 원천 백서 단일 프로세스 순차 추출 실행 (SSE 실시간 스트림)
   * @param {{ docIds: string[], forceReextract?: boolean, runId?: string|null, resumeInterrupted?: boolean }} data
   * @param {Object} callbacks
   * @param {(data: Object) => void} [callbacks.onStart]
   * @param {(data: Object) => void} [callbacks.onProgress]
   * @param {(data: Object) => void} [callbacks.onDocSuccess]
   * @param {(data: Object) => void} [callbacks.onDocError]
   * @param {(data: Object) => void} [callbacks.onFinished]
   * @param {(err: Error) => void} [callbacks.onError]
   */
  async streamExtractSources({ docIds, forceReextract = false, runId = null, resumeInterrupted = false }, { onStart, onProgress, onDocSuccess, onDocError, onDocSkipped, onFinished, onError } = {}) {
    try {
      const token = tokenService.getToken();
      const headers = {
        'Content-Type': 'application/json',
        Accept: 'text/event-stream'
      };
      if (token) {
        headers.Authorization = `Bearer ${token}`;
      }

      // 브라우저 로컬 저장소 API Key 헤더 주입
      try {
        const openAiKey = localStorage.getItem('semicon_wiki_openai_key');
        if (openAiKey) headers['X-OpenAI-Key'] = openAiKey;
        const geminiKey = localStorage.getItem('semicon_wiki_gemini_key');
        if (geminiKey) headers['X-Gemini-Key'] = geminiKey;
      } catch (e) {
        // localStorage access blocked in some sandboxes
      }

      const response = await fetch(runId ? `/api/v1/admin/sources/extract?runId=${encodeURIComponent(runId)}` : '/api/v1/admin/sources/extract', {
        method: runId ? 'GET' : 'POST',
        headers,
        ...(!runId && { body: JSON.stringify({ docIds, forceReextract, ...(resumeInterrupted && { resumeInterrupted: true }) }) })
      });

      if (!response.ok) {
        const errJson = await response.json().catch(() => ({}));
        throw new Error(errJson.detail?.message || errJson.detail || `서버 오류 (${response.status})`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';
      let receivedTerminalEvent = false;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split('\n\n');
        buffer = events.pop() || '';

        for (const evtBlock of events) {
          if (!evtBlock.trim()) continue;
          const lines = evtBlock.split('\n');
          let eventType = 'message';
          let dataStr = '';

          for (const line of lines) {
            if (line.startsWith('event:')) {
              eventType = line.replace('event:', '').trim();
            } else if (line.startsWith('data:')) {
              dataStr += line.replace('data:', '').trim();
            }
          }

          if (!dataStr) continue;
          let parsedData = {};
          try {
            parsedData = JSON.parse(dataStr);
          } catch (e) {
            parsedData = { raw: dataStr };
          }

          if (eventType === 'start' && onStart) {
            onStart(parsedData);
          } else if (eventType === 'progress' && onProgress) {
            onProgress(parsedData);
          } else if (eventType === 'doc_success' && onDocSuccess) {
            onDocSuccess(parsedData);
          } else if (eventType === 'doc_error' && onDocError) {
            onDocError(parsedData);
          } else if (eventType === 'doc_skipped' && onDocSkipped) {
            onDocSkipped(parsedData);
          } else if (eventType === 'finished') {
            receivedTerminalEvent = true;
            onFinished?.(parsedData);
          } else if (eventType === 'error') {
            receivedTerminalEvent = true;
            const error = new Error(parsedData.message || '추출 중 오류 발생');
            if (onError) onError(error);
            else throw error;
          }
        }
      }
      if (!receivedTerminalEvent) {
        throw new Error('추출 완료 확인 전에 연결이 끊겼습니다. 문서 목록에서 마지막 결과를 확인해주세요.');
      }
    } catch (err) {
      if (onError) onError(err);
      else throw err;
    }
  },

  /**
   * 관리자 확인 완료된 추출 결과를 위키 DB에 최종 원자적 적용
   * @param {{ docIds: string[], expectedVersions?: Object }} data
   * @returns {Promise<{ appliedCount: number, updatedConcepts: string[], message: string }>}
   */
  async applyExtractionsToWiki(data) {
    return httpClient.post('/admin/sources/apply', data);
  }
};
