/**
 * [계층 3] Citation & Evidence Badge Service
 * 공인 출처 [E-01] 각주 토큰 파싱 및 하이라이트 순수 서비스
 */

export const citationService = {
  /**
   * 텍스트 내 [E-01], [E-02] 등 공인 출처 토큰 추출
   * @param {string} text
   * @returns {Array<string>}
   */
  extractEvidenceTokens(text) {
    if (!text || typeof text !== 'string') return [];
    const matches = text.match(/\[(E-[A-Za-z0-9][A-Za-z0-9_.:/-]*)\]/g);
    if (!matches) return [];
    return Array.from(new Set(matches.map((m) => m.replace(/\[|\]/g, ''))));
  }
};
