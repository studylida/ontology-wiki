/**
 * [계층 3] PhysicalSafetyGuardService
 * 꼬리질문 및 파라미터 튜닝 상담 시 물리 안전 마진(140N 등) 이탈 여부 사전 검증 서비스
 */

export const physicalSafetyGuardService = {
  /**
   * 사용자 튜닝 텍스트 내 안전 마진 위반 여부 판별
   * @param {string} text
   * @param {string} [overrideReason]
   * @returns {{ isSafe: boolean, warningMessage: string|null, requiresOverride: boolean }}
   */
  validateSafetyMargins(text = '', overrideReason = '') {
    if (!text) return { isSafe: true, warningMessage: null, requiresOverride: false };

    // 1. 본딩 압력 (140N 초과 여부 검출)
    const forceMatch = text.match(/(\d+)\s*(n|뉴턴|newton)/i);
    if (forceMatch) {
      const forceVal = parseInt(forceMatch[1], 10);
      if (forceVal > 140) {
        if (!overrideReason || overrideReason.trim().length === 0) {
          return {
            isSafe: false,
            warningMessage: `⚠️ 인가 본딩 압력(${forceVal}N)이 표준 안전 마진(140N 이하)을 초과했습니다. 다이 크랙 방지를 위해 물리 예외 사유(overrideReason)를 명시해야 합니다.`,
            requiresOverride: true
          };
        }
      }
    }

    // 2. 피크 본딩 온도 (280°C 초과 여부 검출)
    const tempMatch = text.match(/(\d+)\s*(도|°c|c)/i);
    if (tempMatch) {
      const tempVal = parseInt(tempMatch[1], 10);
      if (tempVal > 280) {
        if (!overrideReason || overrideReason.trim().length === 0) {
          return {
            isSafe: false,
            warningMessage: `⚠️ 리플로우 피크 온도(${tempVal}°C)가 허용 임계치(280°C 이하)를 초과했습니다. NCF 열화 방지를 위해 물리 예외 사유를 명시해야 합니다.`,
            requiresOverride: true
          };
        }
      }
    }

    return {
      isSafe: true,
      warningMessage: null,
      requiresOverride: false
    };
  }
};
