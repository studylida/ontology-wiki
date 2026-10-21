/**
 * [계층 3] SemanticVersionService
 * 거버넌스 승인 시 변경 영향도에 따른 Semantic Version (vMAJOR.MINOR.PATCH) 승계 계산
 */

export const semanticVersionService = {
  /**
   * 세맨틱 버전 문자열 파싱 (예: "v1.2.0" ➔ { major: 1, minor: 2, patch: 0 })
   * @param {string} versionStr
   */
  parseVersion(versionStr = 'v1.2.0') {
    const clean = versionStr.replace(/^v/i, '');
    const parts = clean.split('.').map(Number);
    return {
      major: isNaN(parts[0]) ? 1 : parts[0],
      minor: isNaN(parts[1]) ? 2 : parts[1],
      patch: isNaN(parts[2]) ? 0 : parts[2]
    };
  },

  /**
   * 변경 사항에 따른 목표 승계 버전 계산
   * @param {string} currentVersion - 현재 버전 (예: "v1.2.0")
   * @param {{ isNewConcept?: boolean, hasDeprecatedCitations?: boolean, isMajor?: boolean }} options
   * @returns {{ targetVersion: string, bumpType: 'MAJOR'|'MINOR'|'PATCH', reasoning: string }}
   */
  computeNextVersion(currentVersion = 'v1.2.0', options = {}) {
    const { major, minor, patch } = this.parseVersion(currentVersion);

    if (options.isMajor) {
      return {
        targetVersion: `v${major + 1}.0.0`,
        bumpType: 'MAJOR',
        reasoning: '전체 온톨로지 코어 스키마 전면 개편 또는 호환성 단절 변경 (MAJOR 승계)'
      };
    }

    if (options.isNewConcept) {
      return {
        targetVersion: `v${major}.${minor + 1}.0`,
        bumpType: 'MINOR',
        reasoning: '신규 온톨로지 개념 편입 및 신규 지식 문서 공식 발행 (MINOR 승계)'
      };
    }

    if (options.hasDeprecatedCitations) {
      return {
        targetVersion: `v${major}.${minor + 1}.0`,
        bumpType: 'MINOR',
        reasoning: '공인 출처 공식 폐기에 따른 영향도 승계 (MINOR 승계)'
      };
    }

    return {
      targetVersion: `v${major}.${minor}.${patch + 1}`,
      bumpType: 'PATCH',
      reasoning: '공정 수치 보정, 물리 원리 및 실무 문맥 보완 (PATCH 승계)'
    };
  }
};
