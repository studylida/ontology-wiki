/**
 * [계층 4] Chatbot Repository
 * 백엔드 /api/v1/chatbot 엔드포인트와 1:1 통신 및 SSE 스트리밍 통신 클라이언트
 */

import { httpClient } from './httpClient';
import { tokenService } from '../services/tokenService';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export const chatbotRepo = {
  /**
   * 컨텍스트 인식 챗봇 헤더 및 퀵 질문 칩 조회
   * @param {{ conceptId?: string, perspective?: string }} [params]
   * @returns {Promise<import('../types/chatbot.dto').ChatbotContextDTO>}
   */
  async getContext({ conceptId, perspective = 'yield' } = {}) {
    const q = new URLSearchParams();
    if (conceptId) q.append('conceptId', conceptId);
    if (perspective) q.append('perspective', perspective);
    const queryStr = q.toString() ? `?${q.toString()}` : '';
    return httpClient.get(`/chatbot/context${queryStr}`);
  },

  /**
   * 챗봇 메시지 전송 (단건 요청)
   * @param {import('../types/chatbot.dto').ChatbotMessageRequestDTO} data
   * @returns {Promise<import('../types/chatbot.dto').ChatbotMessageResponseDTO>}
   */
  async sendMessage(data) {
    return httpClient.post('/chatbot/messages', data);
  },

  /**
   * SSE 실시간 토큰 타이핑 스트리밍 전송
   * @param {import('../types/chatbot.dto').ChatbotMessageRequestDTO} data
   * @param {Object} callbacks
   * @param {(data: Object) => void} [callbacks.onRouting]
   * @param {(delta: string) => void} [callbacks.onDelta]
   * @param {(result: import('../types/chatbot.dto').ChatbotMessageResponseDTO) => void} [callbacks.onDone]
   * @param {(err: Error) => void} [callbacks.onError]
   * @returns {Promise<void>}
   */
  async streamMessage(data, { onRouting, onDelta, onDone, onError } = {}) {
    const token = tokenService.getAccessToken();
    const headers = {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream'
    };
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/chatbot/messages/stream`, {
        method: 'POST',
        headers,
        body: JSON.stringify(data)
      });

      if (!response.ok) {
        const errorJson = await response.json().catch(() => ({}));
        throw new Error(errorJson?.detail?.message || `HTTP ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split('\n\n');
        buffer = events.pop() || ''; // 마지막 미완성 조각 보존

        for (const rawEvent of events) {
          if (!rawEvent.trim()) continue;

          let eventType = 'message';
          let dataStr = '';

          const lines = rawEvent.split('\n');
          for (const line of lines) {
            if (line.startsWith('event:')) {
              eventType = line.replace('event:', '').trim();
            } else if (line.startsWith('data:')) {
              dataStr = line.replace('data:', '').trim();
            }
          }

          if (!dataStr) continue;

          try {
            const parsedData = JSON.parse(dataStr);
            if (eventType === 'routing' && onRouting) {
              onRouting(parsedData);
            } else if (eventType === 'delta' && onDelta) {
              onDelta(parsedData.delta || '');
            } else if (eventType === 'done' && onDone) {
              onDone(parsedData);
            }
          } catch (e) {
            console.warn('Failed to parse SSE JSON chunk:', dataStr, e);
          }
        }
      }
    } catch (err) {
      if (onError) onError(err);
      else throw err;
    }
  },

  /**
   * 대화 이력 초기화
   * @param {{ conceptId?: string }} [params]
   * @returns {Promise<{ cleared: boolean, message: string, welcomeMessage: string }>}
   */
  async resetMessages({ conceptId } = {}) {
    const q = conceptId ? `?conceptId=${conceptId}` : '';
    return httpClient.delete(`/chatbot/messages${q}`);
  }
};
