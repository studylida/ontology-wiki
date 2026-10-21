/**
 * [계층 3] ResearchFormatterService
 * 외부 문헌 조사실의 출처 신뢰도 티어, 적합도 점수, 날짜 그룹핑 등 순수 도메인 포맷팅 서비스
 */

export const researchFormatterService = {
  /**
   * 신뢰성 티어 메타데이터 반환
   * @param {string} tierString
   * @returns {{ label: string, color: string, bg: string, border: string }}
   */
  getCredibilityMeta(tierString = '') {
    if (tierString.includes('Tier 1') || tierString.includes('공식 제조사')) {
      return {
        label: tierString || 'Tier 1 (공식 제조사)',
        color: '#2563eb',
        bg: 'rgba(37, 99, 235, 0.1)',
        border: '1px solid rgba(37, 99, 235, 0.3)'
      };
    }
    if (tierString.includes('Tier 2') || tierString.includes('국제 표준')) {
      return {
        label: tierString || 'Tier 2 (국제 표준)',
        color: '#7c3aed',
        bg: 'rgba(124, 58, 237, 0.1)',
        border: '1px solid rgba(124, 58, 237, 0.3)'
      };
    }
    if (tierString.includes('Tier 3') || tierString.includes('공인 학술')) {
      return {
        label: tierString || 'Tier 3 (공인 학술)',
        color: '#059669',
        bg: 'rgba(5, 150, 105, 0.1)',
        border: '1px solid rgba(5, 150, 105, 0.3)'
      };
    }
    return {
      label: tierString || '공인 출처',
      color: 'var(--text-secondary)',
      bg: 'var(--bg-surface-2)',
      border: '1px solid var(--border-color)'
    };
  },

  /**
   * 출처 유형 한글 라벨
   * @param {string} type
   * @returns {string}
   */
  getSourceTypeLabel(type = '') {
    switch (type) {
      case 'official_whitepaper':
        return '공인 기술 백서';
      case 'academic_peer_reviewed':
        return '피어리뷰 학술 논문';
      case 'international_standard':
        return '국제 표준 규격';
      default:
        return type || '학술 자료';
    }
  },

  /**
   * 인과 적합도 백분율 및 색상 반환
   * @param {number} score
   * @returns {{ percentText: string, color: string }}
   */
  getRelevanceMeta(score = 0) {
    const percent = Math.round(score * 100);
    let color = '#2563eb';
    if (percent >= 95) color = '#059669';
    else if (percent >= 90) color = '#2563eb';
    else color = '#d97706';

    return {
      percentText: `${percent}%`,
      color
    };
  },

  /**
   * 조사 세션 목록을 날짜 기준 그룹핑
   * @param {Array<import('../types/research.dto').ResearchSessionSummaryDTO>} sessions
   * @returns {Record<string, Array<import('../types/research.dto').ResearchSessionSummaryDTO>>}
   */
  groupSessionsByDate(sessions = []) {
    const groups = {
      '최근 조사 세션': []
    };

    sessions.forEach((s) => {
      groups['최근 조사 세션'].push(s);
    });

    return groups;
  }
};
