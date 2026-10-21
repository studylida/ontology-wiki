/**
 * [계층 4] Central HTTP Client (Fetch Wrapper)
 * - Base URL: /api/v1 (Vite 프록시를 통해 localhost:8000으로 라우팅)
 * - JWT Bearer 토큰 자동 주입
 * - 401 Unauthorized 감지 시 토큰 자동 갱신 및 재시도
 * - 표준화된 ApiError 모델 제공
 */

import { tokenService } from '../services/tokenService';

export class ApiError extends Error {
  constructor(status, message, data = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

const BASE_URL = '/api/v1';
let isRefreshing = false;
let refreshSubscribers = [];

function onRefreshed(newToken) {
  refreshSubscribers.forEach((callback) => callback(newToken));
  refreshSubscribers = [];
}

function addRefreshSubscriber(callback) {
  refreshSubscribers.push(callback);
}

export const httpClient = {
  /**
   * 기본 HTTP 요청 실행 메서드
   * @param {string} endpoint - API 엔드포인트 (예: '/auth/me')
   * @param {RequestInit & { skipAuth?: boolean, retry?: boolean }} [options]
   */
  async request(endpoint, options = {}) {
    const { skipAuth = false, retry = true, ...fetchOptions } = options;

    const url = endpoint.startsWith('http')
      ? endpoint
      : `${BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

    const headers = new Headers(fetchOptions.headers || {});
    if (!headers.has('Content-Type') && !(fetchOptions.body instanceof FormData)) {
      headers.set('Content-Type', 'application/json');
    }

    // JWT Bearer 토큰 주입
    if (!skipAuth) {
      const token = tokenService.getToken();
      if (token && !headers.has('Authorization')) {
        headers.set('Authorization', `Bearer ${token}`);
      }
    }

    try {
      const response = await fetch(url, {
        ...fetchOptions,
        headers
      });

      // 401 Unauthorized 처리 (토큰 자동 갱신 시도)
      if (response.status === 401 && retry && !endpoint.includes('/auth/login') && !endpoint.includes('/auth/refresh')) {
        return this.handleUnauthorizedRetry(endpoint, options);
      }

      // 204 No Content
      if (response.status === 204) {
        return null;
      }

      // JSON 파싱 시도
      let data = null;
      const contentType = response.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        data = await response.text();
      }

      if (!response.ok) {
        // FastAPI 표준 에러 구조 { detail: ... } 파싱
        let errorMessage = `HTTP Error ${response.status}`;
        if (data && typeof data === 'object') {
          if (typeof data.detail === 'string') {
            errorMessage = data.detail;
          } else if (Array.isArray(data.detail)) {
            errorMessage = data.detail.map((err) => `${err.loc?.join('.')}: ${err.msg}`).join(', ');
          } else if (data.message) {
            errorMessage = data.message;
          }
        }
        throw new ApiError(response.status, errorMessage, data);
      }

      return data;
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      throw new ApiError(0, error.message || '네트워크 연결 오류가 발생했습니다.', error);
    }
  },

  /**
   * 401 발생 시 토큰 갱신 후 재시도
   */
  async handleUnauthorizedRetry(endpoint, options) {
    if (!isRefreshing) {
      isRefreshing = true;

      try {
        const refreshResponse = await fetch(`${BASE_URL}/auth/refresh`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${tokenService.getToken()}`
          }
        });

        if (refreshResponse.ok) {
          const result = await refreshResponse.json();
          const newToken = result.accessToken || result.access_token;
          tokenService.setToken(newToken);
          isRefreshing = false;
          onRefreshed(newToken);
          return this.request(endpoint, { ...options, retry: false });
        } else {
          // 토큰 갱신 실패 ➔ 로그아웃 상태 전환
          tokenService.removeToken();
          isRefreshing = false;
          window.dispatchEvent(new CustomEvent('auth:expired'));
          throw new ApiError(401, '인증 세션이 만료되었습니다. 다시 로그인해 주세요.');
        }
      } catch (err) {
        tokenService.removeToken();
        isRefreshing = false;
        window.dispatchEvent(new CustomEvent('auth:expired'));
        throw new ApiError(401, '인증 세션이 만료되었습니다.', err);
      }
    }

    // 이미 갱신 중인 경우 대기열에 등록
    return new Promise((resolve, reject) => {
      addRefreshSubscriber((newToken) => {
        if (!newToken) {
          reject(new ApiError(401, '인증 세션이 만료되었습니다.'));
        } else {
          resolve(this.request(endpoint, { ...options, retry: false }));
        }
      });
    });
  },

  get(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'GET' });
  },

  post(endpoint, body, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: 'POST',
      body: typeof body === 'string' || body instanceof FormData ? body : JSON.stringify(body)
    });
  },

  put(endpoint, body, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: 'PUT',
      body: typeof body === 'string' || body instanceof FormData ? body : JSON.stringify(body)
    });
  },

  patch(endpoint, body, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: 'PATCH',
      body: typeof body === 'string' || body instanceof FormData ? body : JSON.stringify(body)
    });
  },

  delete(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'DELETE' });
  }
};
