/**
 * @file http_client.js
 * @description 전 도메인 공통 순수 HTTP/SSE 통신 클라이언트 (Repository Base)
 * 
 * 책 임:
 * 1. 백엔드 REST API(/api/v1) 표준 Fetch 호출 래핑 (GET, POST, PUT, PATCH, DELETE)
 * 2. 현재 사용자 보안 역할(X-User-Role: line_engineer / chief_reviewer) 자동 주입
 * 3. HTTP 상태 코드별(400, 403, 404, 409, 422, 500) 정형 ApiError 생성
 * 4. F-01 챗봇용 Server-Sent Events(SSE) 실시간 스트리밍 헬퍼 제공
 * 
 * 금 지: DOM 조작, 화면 렌더링, 특정 탭 UI 상태 소유 절대 금지 (순수 I/O 계층)
 */

export class ApiError extends Error {
  /**
   * @param {number} status HTTP 상태 코드 (e.g. 403, 404, 409, 422)
   * @param {string} message 에러 메시지
   * @param {any} [detail] 백엔드 FastAPI detail 객체
   */
  constructor(status, message, detail = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

class HttpClient {
  constructor() {
    this.baseUrl = 'http://localhost:8000/api/v1';
  }

  /**
   * 현재 선택된 사용자의 RBAC 권한 역할(line_engineer / chief_reviewer)을 반환합니다.
   * index.html 상단의 #header-rbac-selector 값 또는 localStorage에서 동적으로 읽어옵니다.
   * @returns {string}
   */
  getCurrentRole() {
    try {
      const selectEl = document.getElementById('header-rbac-selector');
      if (selectEl && selectEl.value) {
        return selectEl.value;
      }
      return localStorage.getItem('user_role') || 'chief_reviewer';
    } catch (_) {
      return 'chief_reviewer';
    }
  }

  /**
   * 공통 HTTP 요청 헤더 조립
   * @param {Record<string, string>} [customHeaders={}]
   * @returns {Headers}
   */
  buildHeaders(customHeaders = {}) {
    const headers = new Headers();
    headers.set('Content-Type', 'application/json');
    headers.set('Accept', 'application/json');
    
    // RBAC 헤더 자동 주입
    const role = this.getCurrentRole();
    if (role) {
      headers.set('X-User-Role', role);
    }

    // 커스텀 헤더 병합
    for (const [key, value] of Object.entries(customHeaders)) {
      if (value !== undefined && value !== null) {
        headers.set(key, String(value));
      }
    }

    return headers;
  }

  /**
   * 기본 Fetch 실행 및 정형 응답 파싱
   * @param {string} endpoint (e.g. '/concepts/concept-tcb')
   * @param {RequestInit} [options={}]
   * @returns {Promise<any>}
   */
  async request(endpoint, options = {}) {
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    const url = `${this.baseUrl}${cleanEndpoint}`;

    const headers = this.buildHeaders(options.headers || {});
    const config = {
      ...options,
      headers
    };

    let response;
    try {
      response = await fetch(url, config);
    } catch (networkError) {
      throw new ApiError(0, `네트워크 연결에 실패했습니다: ${networkError.message}`);
    }

    // 204 No Content
    if (response.status === 204) {
      return null;
    }

    // JSON 본문 파싱 시도
    let data = null;
    const contentType = response.headers.get('content-type') || '';
    if (contentType.includes('application/json')) {
      try {
        data = await response.json();
      } catch (parseErr) {
        data = null;
      }
    } else {
      data = await response.text();
    }

    // 에러 상태 코드 처리
    if (!response.ok) {
      let errorMessage = `요청 실패 (HTTP ${response.status})`;
      if (data && typeof data === 'object') {
        if (typeof data.detail === 'string') {
          errorMessage = data.detail;
        } else if (data.detail && typeof data.detail === 'object') {
          errorMessage = data.detail.message || JSON.stringify(data.detail);
        } else if (data.message) {
          errorMessage = data.message;
        }
      } else if (typeof data === 'string' && data.trim()) {
        errorMessage = data;
      }

      throw new ApiError(response.status, errorMessage, data ? data.detail : null);
    }

    return data;
  }

  /**
   * HTTP GET
   * @param {string} endpoint
   * @param {Record<string, any>} [params=null] 쿼리 파라미터
   * @param {Record<string, string>} [headers={}]
   */
  async get(endpoint, params = null, headers = {}) {
    let url = endpoint;
    if (params && typeof params === 'object') {
      const searchParams = new URLSearchParams();
      for (const [key, value] of Object.entries(params)) {
        if (value !== undefined && value !== null) {
          searchParams.append(key, String(value));
        }
      }
      const queryString = searchParams.toString();
      if (queryString) {
        url += (url.includes('?') ? '&' : '?') + queryString;
      }
    }
    return this.request(url, { method: 'GET', headers });
  }

  /**
   * HTTP POST
   * @param {string} endpoint
   * @param {any} [body=null]
   * @param {Record<string, string>} [headers={}]
   */
  async post(endpoint, body = null, headers = {}) {
    return this.request(endpoint, {
      method: 'POST',
      headers,
      body: body ? JSON.stringify(body) : undefined
    });
  }

  /**
   * HTTP PUT
   * @param {string} endpoint
   * @param {any} [body=null]
   * @param {Record<string, string>} [headers={}]
   */
  async put(endpoint, body = null, headers = {}) {
    return this.request(endpoint, {
      method: 'PUT',
      headers,
      body: body ? JSON.stringify(body) : undefined
    });
  }

  /**
   * HTTP PATCH
   * @param {string} endpoint
   * @param {any} [body=null]
   * @param {Record<string, string>} [headers={}]
   */
  async patch(endpoint, body = null, headers = {}) {
    return this.request(endpoint, {
      method: 'PATCH',
      headers,
      body: body ? JSON.stringify(body) : undefined
    });
  }

  /**
   * HTTP DELETE
   * @param {string} endpoint
   * @param {Record<string, any>} [params=null]
   * @param {Record<string, string>} [headers={}]
   */
  async delete(endpoint, params = null, headers = {}) {
    let url = endpoint;
    if (params && typeof params === 'object') {
      const searchParams = new URLSearchParams();
      for (const [key, value] of Object.entries(params)) {
        if (value !== undefined && value !== null) {
          searchParams.append(key, String(value));
        }
      }
      const queryString = searchParams.toString();
      if (queryString) {
        url += (url.includes('?') ? '&' : '?') + queryString;
      }
    }
    return this.request(url, { method: 'DELETE', headers });
  }

  /**
   * SSE (Server-Sent Events) 실시간 스트리밍 POST 헬퍼
   * @param {string} endpoint (e.g. '/chatbot/messages/stream')
   * @param {any} body 요청 본문
   * @param {(event: {type: string, data: any}) => void} onEvent 이벤트 수신 콜백
   * @param {(err: Error) => void} onError 에러 수신 콜백
   * @returns {Promise<void>}
   */
  async stream(endpoint, body, onEvent, onError) {
    const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
    const url = `${this.baseUrl}${cleanEndpoint}`;
    const headers = this.buildHeaders({
      'Accept': 'text/event-stream'
    });

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers,
        body: JSON.stringify(body)
      });

      if (!response.ok) {
        const text = await response.text();
        throw new ApiError(response.status, text || `스트림 연결 실패 (${response.status})`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';

        for (const block of lines) {
          if (!block.trim()) continue;
          let eventType = 'message';
          let eventData = '';

          const blockLines = block.split('\n');
          for (const line of blockLines) {
            if (line.startsWith('event:')) {
              eventType = line.replace('event:', '').trim();
            } else if (line.startsWith('data:')) {
              eventData = line.replace('data:', '').trim();
            }
          }

          let parsed = eventData;
          try {
            parsed = JSON.parse(eventData);
          } catch (_) {}

          onEvent({ type: eventType, data: parsed });
        }
      }
    } catch (err) {
      if (onError) onError(err);
      else throw err;
    }
  }
}

// 싱글톤 인스턴스 export
export const httpClient = new HttpClient();
