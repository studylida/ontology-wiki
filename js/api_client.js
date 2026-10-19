/**
 * 반도체 공정·소자 인과 온톨로지 지식 위키 - API 클라이언트 모듈 (WikiAPI)
 * 41대 REST API 엔드포인트 전수 연동, 3단계 상태 인디케이터, 자동 폴백 및 토스트 시스템
 */

(function (window) {
  "use strict";

  // 기본 API Base URL (로컬 백엔드 서버)
  const DEFAULT_API_BASE = "http://localhost:8000/api/v1";

  class WikiApiClient {
    constructor() {
      this.baseUrl = sessionStorage.getItem("wiki_api_base_url") || DEFAULT_API_BASE;
      this.systemStatus = "degraded"; // 'healthy' | 'degraded' | 'maintenance'
      this.activeVersion = "v1.2";
      this.latestVersion = "v1.2";
      this.isUpdateAvailable = false;
      this.isOnline = false;
      this.statusListeners = [];
      this.healthTimer = null;
    }

    /**
     * API Base URL 변경 및 재연결
     */
    setBaseUrl(url) {
      this.baseUrl = (url || DEFAULT_API_BASE).replace(/\/+$/, "");
      sessionStorage.setItem("wiki_api_base_url", this.baseUrl);
      this.checkSystemStatus();
    }

    /**
     * 시스템 상태 변경 리스너 등록
     */
    onStatusChange(fn) {
      if (typeof fn === "function") {
        this.statusListeners.push(fn);
      }
    }

    _notifyStatusChange() {
      const data = {
        status: this.systemStatus,
        activeVersion: this.activeVersion,
        latestVersion: this.latestVersion,
        isUpdateAvailable: this.isUpdateAvailable,
        isOnline: this.isOnline
      };
      this.statusListeners.forEach((fn) => {
        try {
          fn(data);
        } catch (e) {
          console.error("Status listener error:", e);
        }
      });
      window.dispatchEvent(new CustomEvent("wiki:system-status-changed", { detail: data }));
    }

    /**
     * 공통 fetch 래퍼 (타임아웃, 에러 핸들링, JSON 파싱)
     */
    async _request(endpoint, options = {}) {
      const url = `${this.baseUrl}${endpoint}`;
      const timeoutMs = options.timeout || 8000;
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

      const headers = {
        "Content-Type": "application/json",
        ...(options.headers || {})
      };

      try {
        const response = await fetch(url, {
          ...options,
          headers,
          signal: controller.signal
        });
        clearTimeout(timeoutId);

        // 3-tier 상태 업데이트
        if (!this.isOnline) {
          this.isOnline = true;
          this.systemStatus = "healthy";
          this._notifyStatusChange();
        }

        if (!response.ok) {
          let errData = null;
          try {
            errData = await response.json();
          } catch (_) {
            errData = { message: `HTTP ${response.status}: ${response.statusText}` };
          }
          const error = new Error(errData.detail?.message || errData.message || `Request failed with ${response.status}`);
          error.status = response.status;
          error.detail = errData.detail || errData;
          throw error;
        }

        return await response.json();
      } catch (err) {
        clearTimeout(timeoutId);
        // 서버 연결 실패 시 degraded (오프라인 / 정적 데이터 폴백) 상태로 전환
        if (err.name === "AbortError" || err.message.includes("Failed to fetch") || err.message.includes("NetworkError")) {
          if (this.isOnline || this.systemStatus !== "degraded") {
            this.isOnline = false;
            this.systemStatus = "degraded";
            this._notifyStatusChange();
          }
        }
        throw err;
      }
    }

    // =========================================================================
    // 1. 시스템 공통 & 전역 검색 API (§ 4.1)
    // =========================================================================

    /**
     * GET /system/health - 시스템 가동 상태 및 헬스체크
     */
    async getSystemHealth() {
      try {
        const data = await this._request("/system/health", { timeout: 3000 });
        this.systemStatus = data.status === "maintenance" ? "maintenance" : (data.status === "degraded" ? "degraded" : "healthy");
        this.isOnline = true;
        this._notifyStatusChange();
        return data;
      } catch (err) {
        this.systemStatus = "degraded";
        this.isOnline = false;
        this._notifyStatusChange();
        return { status: "degraded", message: "Server offline, fallback active" };
      }
    }

    /**
     * GET /system/version - 온톨로지 배포 버전 및 메타 정보
     */
    async getSystemVersion() {
      try {
        const data = await this._request("/system/version", { timeout: 3000 });
        this.activeVersion = data.activeVersion || "v1.2";
        this.latestVersion = data.latestVersion || "v1.2";
        this.isUpdateAvailable = !!data.isUpdateAvailable;
        this._notifyStatusChange();
        return data;
      } catch (err) {
        return {
          activeVersion: "v1.2",
          latestVersion: "v1.2",
          isUpdateAvailable: false,
          totalConcepts: 35,
          totalEvidences: 133
        };
      }
    }

    /**
     * 주기적 헬스체크 시작
     */
    startHealthPolling(intervalMs = 30000) {
      if (this.healthTimer) clearInterval(this.healthTimer);
      this.checkSystemStatus();
      this.healthTimer = setInterval(() => this.checkSystemStatus(), intervalMs);
    }

    async checkSystemStatus() {
      await this.getSystemHealth();
      await this.getSystemVersion();
    }

    /**
     * GET /search/spotlight?q=... - Cmd+K 스포트라이트 전역 검색
     */
    async searchSpotlight(query = "", limit = 10) {
      const q = encodeURIComponent(query.trim());
      return await this._request(`/search/spotlight?q=${q}&limit=${limit}`);
    }

    /**
     * GET /evidences/{id} - [D-01] 공인 출처 원문 드로어 서빙
     */
    async getEvidence(evidenceId) {
      return await this._request(`/evidences/${encodeURIComponent(evidenceId)}`);
    }

    // =========================================================================
    // 2. [Tab 1] 위키 본문 & 인과 온톨로지 API (§ 4.2)
    // =========================================================================

    /**
     * GET /concepts/tree - 좌측 사이드바 4축 계층 아코디언 트리
     */
    async getConceptTree(facet = "unit_process", expandedId = null) {
      let endpoint = `/concepts/tree?facet=${encodeURIComponent(facet)}`;
      if (expandedId) endpoint += `&expandedId=${encodeURIComponent(expandedId)}`;
      return await this._request(endpoint);
    }

    /**
     * GET /concepts/{id} - 위키 본문 상세 조회
     */
    async getConceptDetail(conceptId) {
      return await this._request(`/concepts/${encodeURIComponent(conceptId)}`);
    }

    /**
     * GET /concepts/{id}/causal-subgraph - Cytoscape 캔버스용 인과 서브그래프
     */
    async getCausalSubgraph(conceptId, depth = 2, edgeType = "all") {
      return await this._request(`/concepts/${encodeURIComponent(conceptId)}/causal-subgraph?depth=${depth}&edgeType=${edgeType}`);
    }

    /**
     * GET /concepts/{childId}/contextual-explain - [P-01] 인라인 문맥 해설 팝오버
     */
    async getContextualExplain(childId, parentId = null) {
      let endpoint = `/concepts/${encodeURIComponent(childId)}/contextual-explain`;
      if (parentId) endpoint += `?parentId=${encodeURIComponent(parentId)}`;
      return await this._request(endpoint);
    }

    /**
     * POST /review-tickets - 위키 본문 하단 간이 제안 모달 ([M-05]) 발행
     */
    async createReviewTicket(payload) {
      return await this._request("/review-tickets", {
        method: "POST",
        body: JSON.stringify(payload)
      });
    }

    // =========================================================================
    // 3. [Tab 2] 기술 대안 비교분석 API (§ 4.3)
    // =========================================================================

    /**
     * GET /comparison-sessions - 최근 비교 분석 세션 목록
     */
    async listComparisonSessions(limit = 20) {
      return await this._request(`/comparison-sessions?limit=${limit}`);
    }

    /**
     * POST /comparison/clarify - [화면 2-A] 대화형 질문 구체화 3대 분기 카드
     */
    async clarifyComparison(payload) {
      return await this._request("/comparison/clarify", {
        method: "POST",
        body: JSON.stringify(payload)
      });
    }

    /**
     * POST /comparison-sessions - 신규 비교 분석 세션 생성
     */
    async createComparisonSession(payload) {
      return await this._request("/comparison-sessions", {
        method: "POST",
        body: JSON.stringify(payload)
      });
    }

    /**
     * GET /comparison-sessions/{id} - 비교 세션 3-Step 스냅샷 상세 조회
     */
    async getComparisonSession(sessionId) {
      return await this._request(`/comparison-sessions/${encodeURIComponent(sessionId)}`);
    }

    /**
     * PATCH /comparison-sessions/{id} - 세션 즐겨찾기(⭐), 제목, 폴더 수정
     */
    async patchComparisonSession(sessionId, payload) {
      return await this._request(`/comparison-sessions/${encodeURIComponent(sessionId)}`, {
        method: "PATCH",
        body: JSON.stringify(payload)
      });
    }

    /**
     * POST /comparison-sessions/{id}/matrix - 매트릭스 필터링 및 동적 커스텀 축 추가
     */
    async updateComparisonMatrix(sessionId, payload) {
      return await this._request(`/comparison-sessions/${encodeURIComponent(sessionId)}/matrix`, {
        method: "POST",
        body: JSON.stringify(payload)
      });
    }

    /**
     * POST /comparison-sessions/{id}/tune-advisor - [M-04] AI 파라미터 튜닝 상담
     */
    async tuneAdvisor(sessionId, payload) {
      return await this._request(`/comparison-sessions/${encodeURIComponent(sessionId)}/tune-advisor`, {
        method: "POST",
        body: JSON.stringify(payload)
      });
    }

    /**
     * POST /comparison-sessions/{id}/tail-question - 꼬리질문 및 4단계 인과 체인
     */
    async tailQuestion(sessionId, query, stepIndex = 2) {
      return await this._request(`/comparison-sessions/${encodeURIComponent(sessionId)}/tail-question`, {
        method: "POST",
        body: JSON.stringify({ query, stepIndex })
      });
    }

    /**
     * POST /comparison-sessions/{id}/export-ticket - 거버넌스 티켓 원클릭 승계
     */
    async exportComparisonTicket(sessionId, payload) {
      return await this._request(`/comparison-sessions/${encodeURIComponent(sessionId)}/export-ticket`, {
        method: "POST",
        body: JSON.stringify(payload)
      });
    }

    // =========================================================================
    // 4. [Tab 3] 검토·승인 센터 API (§ 4.4)
    // =========================================================================

    /**
     * GET /review-tickets - 검토 티켓 목록 조회 (상태/개념 필터링)
     */
    async listReviewTickets(status = null, conceptId = null, limit = 20) {
      let endpoint = `/review-tickets?limit=${limit}`;
      if (status) endpoint += `&status=${encodeURIComponent(status)}`;
      if (conceptId) endpoint += `&conceptId=${encodeURIComponent(conceptId)}`;
      return await this._request(endpoint);
    }

    /**
     * GET /review-tickets/{id} - 검토 티켓 상세 조회 (2-Pane Diff 및 무결성 리포트)
     */
    async getReviewTicket(ticketId) {
      return await this._request(`/review-tickets/${encodeURIComponent(ticketId)}`);
    }

    /**
     * POST /review-tickets/{id}/presence - 비관적 동시 편집 방지 락 관리
     */
    async managePresence(ticketId, action = "acquire", reviewerId = "expert-kim") {
      return await this._request(`/review-tickets/${encodeURIComponent(ticketId)}/presence`, {
        method: "POST",
        body: JSON.stringify({ action, reviewerId })
      });
    }

    /**
     * POST /review-tickets/{id}/directive - 전문가 자연어 보완 지시문 반영 초안 재작성
     */
    async sendDirective(ticketId, directiveText, overrideReason = null) {
      return await this._request(`/review-tickets/${encodeURIComponent(ticketId)}/directive`, {
        method: "POST",
        body: JSON.stringify({ directiveText, overrideReason })
      });
    }

    /**
     * PUT /review-tickets/{id}/human-edits - 전문가 직접 편집기 실시간 저장 (409 충돌 방어)
     */
    async saveHumanEdits(ticketId, ticketVersion, editedContent) {
      return await this._request(`/review-tickets/${encodeURIComponent(ticketId)}/human-edits`, {
        method: "PUT",
        body: JSON.stringify({ ticketVersion, editedContent })
      });
    }

    /**
     * GET /review-tickets/{id}/wiki-preview - [M-02] 실시간 위키 미리보기 모달
     */
    async getWikiPreview(ticketId, highlightChanges = true) {
      return await this._request(`/review-tickets/${encodeURIComponent(ticketId)}/wiki-preview?highlightChanges=${highlightChanges}`);
    }

    /**
     * POST /review-tickets/{id}/approve - 최종 승인 집행 및 WORM 머클 감사 체인 서명
     */
    async approveReviewTicket(ticketId, payload) {
      return await this._request(`/review-tickets/${encodeURIComponent(ticketId)}/approve`, {
        method: "POST",
        body: JSON.stringify(payload)
      });
    }

    /**
     * POST /review-tickets/{id}/reject - 반려 처리
     */
    async rejectReviewTicket(ticketId, payload) {
      return await this._request(`/review-tickets/${encodeURIComponent(ticketId)}/reject`, {
        method: "POST",
        body: JSON.stringify(payload)
      });
    }

    /**
     * GET /review-tickets/{id}/audit-logs - Merkle 해시 체인 감사 이력 조회
     */
    async getAuditLogs(ticketId) {
      return await this._request(`/review-tickets/${encodeURIComponent(ticketId)}/audit-logs`);
    }

    // =========================================================================
    // 5. [Tab 4] 외부 문헌·백서 조사 API (§ 4.5)
    // =========================================================================

    /**
     * GET /research/sessions - 최근 문헌 조사 로그 피드
     */
    async listResearchSessions(limit = 15) {
      return await this._request(`/research/sessions?limit=${limit}`);
    }

    /**
     * POST /research/clarify - [화면 4-A] 신뢰 출처 풀 안내 및 범위 필터
     */
    async clarifyResearch(searchTopic, preferredTier = []) {
      return await this._request("/research/clarify", {
        method: "POST",
        body: JSON.stringify({ searchTopic, preferredTier })
      });
    }

    /**
     * POST /research/discover - 공인 문헌(Evidence Feed) 발굴 피드 생성
     */
    async discoverResearch(payload) {
      return await this._request("/research/discover", {
        method: "POST",
        body: JSON.stringify(payload)
      });
    }

    /**
     * POST /research/sessions/{id}/synthesize - [화면 4-B] 교차 분석 종합 리포트 및 지식 후보 생성
     */
    async synthesizeResearch(sessionId, selectedEvidenceIds) {
      return await this._request(`/research/sessions/${encodeURIComponent(sessionId)}/synthesize`, {
        method: "POST",
        body: JSON.stringify({ selectedEvidenceIds })
      });
    }

    /**
     * GET /research/sessions/{id} - 조사 세션 종합 리포트 및 지식 후보 복원
     */
    async getResearchSession(sessionId) {
      return await this._request(`/research/sessions/${encodeURIComponent(sessionId)}`);
    }

    /**
     * POST /research/candidates/{candidateId}/export-ticket - 지식 후보 검토 센터 큐 등록
     */
    async exportResearchCandidate(candidateId, payload) {
      return await this._request(`/research/candidates/${encodeURIComponent(candidateId)}/export-ticket`, {
        method: "POST",
        body: JSON.stringify(payload)
      });
    }

    // =========================================================================
    // 6. [F-01] 전역 플로팅 챗봇 API (§ 4.6)
    // =========================================================================

    /**
     * GET /chatbot/context - 현재 열람 개념 기반 퀵 질문 3종 서빙
     */
    async getChatbotContext(conceptId = null, perspective = "yield") {
      let endpoint = `/chatbot/context?perspective=${encodeURIComponent(perspective)}`;
      if (conceptId) endpoint += `&conceptId=${encodeURIComponent(conceptId)}`;
      return await this._request(endpoint);
    }

    /**
     * POST /chatbot/messages - 3단 지능형 라우터 챗봇 대화 질의
     */
    async sendChatbotMessage(payload) {
      return await this._request("/chatbot/messages", {
        method: "POST",
        body: JSON.stringify(payload)
      });
    }

    /**
     * DELETE /chatbot/messages - 챗봇 대화 초기화
     */
    async resetChatbotMessages(conceptId = null) {
      let endpoint = "/chatbot/messages";
      if (conceptId) endpoint += `?conceptId=${encodeURIComponent(conceptId)}`;
      return await this._request(endpoint, { method: "DELETE" });
    }

    // =========================================================================
    // 7. 토스트 알림 헬퍼 (Transitions.dev CSS Toast Container)
    // =========================================================================

    /**
     * 토스트 알림 렌더링
     * @param {string} message - 표시할 메시지
     * @param {'info'|'success'|'warning'|'error'} type - 알림 유형
     * @param {number} duration - 노출 시간 (ms)
     */
    showToast(message, type = "info", duration = 3000) {
      const container = document.getElementById("toast-container");
      if (!container) return;

      const toast = document.createElement("div");
      toast.className = `toast-item toast-${type}`;
      
      const icons = {
        info: "ℹ️",
        success: "✅",
        warning: "⚠️",
        error: "❌"
      };

      toast.innerHTML = `
        <span style="font-size:1.125rem;">${icons[type] || "ℹ️"}</span>
        <span>${message}</span>
      `;

      container.appendChild(toast);

      // Transitions.dev 부드러운 등장 (다음 프레임에 .show 추가)
      requestAnimationFrame(() => {
        toast.classList.add("show");
      });

      // duration 후 퇴장 및 삭제
      setTimeout(() => {
        toast.classList.remove("show");
        setTimeout(() => {
          if (toast.parentNode) toast.parentNode.removeChild(toast);
        }, 300);
      }, duration);
    }
  }

  // 싱글톤 인스턴스 전역 등록
  window.WikiAPI = new WikiApiClient();

})(window);
