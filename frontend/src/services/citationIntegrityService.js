/**
 * [계층 3] CitationIntegrityService
 * - [E-01] 공인 출처 각주 누락 방지 및 자동 복원 엔진
 * - 공식 폐기(allowCitationDeletion) 인가 여부 판별
 */

export const citationIntegrityService = {
  /**
   * 텍스트 내 [E-xx] 각주 토큰 세트 추출
   * @param {string} text
   * @returns {Set<string>}
   */
  extractCitations(text) {
    if (!text || typeof text !== 'string') return new Set();
    const matches = text.match(/\[E-\d+\]/g) || [];
    return new Set(matches);
  },

  /**
   * 편집 중 공인 출처가 누락되었는지 검사하고 자동 복원
   * @param {string} originalContent - 원문 또는 이전 판본
   * @param {string} editedContent - 수정 중인 본문
   * @param {boolean} [allowDeletion=false] - 공식 폐기 허용 여부
   * @param {string} [reason=''] - 폐기 사유
   * @returns {{ isValid: boolean, missingCitations: string[], restoredContent: string, isRestored: boolean }}
   */
  validateAndRestore(originalContent = '', editedContent = '', allowDeletion = false, reason = '') {
    const originalCitations = this.extractCitations(originalContent);
    const editedCitations = this.extractCitations(editedContent);

    const missingCitations = [];
    originalCitations.forEach((cit) => {
      if (!editedCitations.has(cit)) {
        missingCitations.push(cit);
      }
    });

    // 누락된 출처가 없거나 공식 폐기 인가 시 그대로 통과
    if (missingCitations.length === 0 || allowDeletion) {
      return {
        isValid: true,
        missingCitations,
        restoredContent: editedContent,
        isRestored: false
      };
    }

    // 🌟 자동 복원 엔진 가동: 누락된 공인 출처 각주를 본문 말미에 자동 합성
    const restoreFootnote = missingCitations
      .map((cit) => `\n> [공인 출처 인용 근거 보존]: 이전 공인 온톨로지 승인에 의해 보존된 필수 근거 자료입니다. ${cit}`)
      .join('\n');

    const restoredContent = `${editedContent.trim()}\n\n${restoreFootnote}`;

    return {
      isValid: false,
      missingCitations,
      restoredContent,
      isRestored: true
    };
  }
};
