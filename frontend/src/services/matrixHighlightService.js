/**
 * [계층 3] MatrixHighlightService
 * 비교 매트릭스 카테고리 분류 및 온톨로지 지식 갭(Knowledge Gap) 셀 파싱 서비스
 */

export const matrixHighlightService = {
  /**
   * 축 카테고리 메타데이터
   */
  getCategoryMeta(category = 'thermal') {
    const meta = {
      thermal: { label: '열·물성 특성', color: '#ea580c', bg: '#fff7ed' },
      defect: { label: '결함 및 신뢰성', color: '#dc2626', bg: '#fef2f2' },
      fab: { label: '팹 양산 공정성', color: '#2563eb', bg: '#eff6ff' },
      electrical: { label: '전기적 인터커넥트', color: '#7c3aed', bg: '#f5f3ff' }
    };
    return meta[category] || { label: category, color: '#64748b', bg: '#f8fafc' };
  },

  /**
   * 셀 값이 온톨로지 미등록 Gap인지 판별
   * @param {string} val
   * @returns {boolean}
   */
  isGapValue(val) {
    return val == null || ['', '미등록', '공개 근거 미확인', 'Gap', 'null'].includes(String(val).trim());
  }
};
