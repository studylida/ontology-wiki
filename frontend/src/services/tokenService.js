/**
 * [계층 3] Token Storage & Security Domain Service
 * UI 및 React에 비의존적인 순수 토큰 관리 로직
 */

const TOKEN_KEY = 'semicon_wiki_jwt_token';

export const tokenService = {
  /**
   * 로컬 스토리지에서 액세스 토큰 조회
   * @returns {string|null}
   */
  getToken() {
    try {
      return localStorage.getItem(TOKEN_KEY);
    } catch {
      return null;
    }
  },

  /**
   * 로컬 스토리지에 액세스 토큰 저장
   * @param {string} token
   */
  setToken(token) {
    try {
      if (token) {
        localStorage.setItem(TOKEN_KEY, token);
      } else {
        localStorage.removeItem(TOKEN_KEY);
      }
    } catch (e) {
      console.error('Failed to save JWT token:', e);
    }
  },

  /**
   * 로컬 스토리지에서 액세스 토큰 삭제
   */
  removeToken() {
    try {
      localStorage.removeItem(TOKEN_KEY);
    } catch (e) {
      console.error('Failed to remove JWT token:', e);
    }
  },

  /**
   * JWT Payload 디코딩 및 만료 여부 판별
   * @param {string} [token]
   * @returns {{ valid: boolean, payload: any }}
   */
  inspectToken(token = null) {
    const targetToken = token || this.getToken();
    if (!targetToken) {
      return { valid: false, payload: null };
    }

    try {
      const parts = targetToken.split('.');
      if (parts.length !== 3) {
        return { valid: false, payload: null };
      }
      const payloadBase64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(
        atob(payloadBase64)
          .split('')
          .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join('')
      );
      const payload = JSON.parse(jsonPayload);

      // 만료 시간 (exp, 초 단위) 검사
      const nowSeconds = Math.floor(Date.now() / 1000);
      if (payload.exp && payload.exp < nowSeconds) {
        return { valid: false, payload, expired: true };
      }

      return { valid: true, payload, expired: false };
    } catch (e) {
      return { valid: false, payload: null, error: e.message };
    }
  }
};
