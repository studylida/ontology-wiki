/**
 * [계층 3] ResearchFormatterService
 * 외부 문헌 조사실의 출처 신뢰도 티어, 적합도 점수, 날짜 그룹핑 등 순수 도메인 포맷팅 서비스
 */

export const researchFormatterService = {
  getAcquisitionLabel(outcome) {
    return ({ obtained: '공개 원문 일부 확보', timeout: '응답 시간 초과', retry_later: '잠시 후 재시도', blocked: '접근 제한',
      not_found: '출처 조회 실패', document_identity_unverified: '해당 문헌인지 확인 불가', technical_content_unavailable: '읽을 내용 부족',
      pdf_text_unavailable: 'PDF 텍스트 추출 불가', content_too_large: '파일 크기 제한', unsafe_public_url: '허용되지 않은 주소',
      unsafe_public_address: '공개 주소 아님', unsupported_content_type: '지원하지 않는 파일 형식',
      unsupported_encoding: '지원하지 않는 압축 형식', too_many_redirects: '이동 횟수 제한' })[outcome] || '내용 확보 실패';
  },
  getResearchStateLabel(state) {
    return ({ all: '전체', included: '조사에 포함', content_unavailable: '내용 미확보', insufficient_content: '근거 부족',
      not_assessed: '평가 대기', assessment_failed: '평가 실패', excluded: '이번 조사에서 제외', unverified: '과거 평가 미확인' })[state] || state;
  },
  getCandidateTypeLabel(type) {
    return ({ new_concept: '신규 개념 등록 제안', concept_enrichment: '기존 개념 보강 제안' })[type] || type || '후보 유형 미확인';
  },
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
      label: tierString || '신뢰도 미확인',
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
        return type || '자료 유형 미확인';
    }
  },

  getAssessmentLabel(assessment) {
    return ({ included: '조사에 포함', deferred: '판단 보류', excluded: '이번 조사에서 제외' })[assessment?.decision] || '관련성 평가 기록 없음';
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
