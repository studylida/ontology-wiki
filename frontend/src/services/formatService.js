/**
 * [계층 3] Formatting & UI Domain Utility Service
 */

export const formatService = {
  /**
   * 스케일 레벨별 명칭 및 색상 테마
   * @param {number} level
   */
  getScaleInfo(level) {
    const scales = {
      1: { name: '원자/물성', label: 'L1 원자/물성', color: '#6366f1', bg: '#eef2ff' },
      2: { name: '박막/식각 단위공정', label: 'L2 단위공정', color: '#0ea5e9', bg: '#f0f9ff' },
      3: { name: '트랜지스터 소자', label: 'L3 소자', color: '#10b981', bg: '#ecfdf5' },
      4: { name: '웨이퍼/다이 통합', label: 'L4 웨이퍼/다이', color: '#f59e0b', bg: '#fffbeb' },
      5: { name: '첨단 패키징/모듈', label: 'L5 첨단 패키징', color: '#ec4899', bg: '#fdf2f8' }
    };
    return scales[level] || { name: '공정 레벨', label: `L${level || 1}`, color: '#64748b', bg: '#f1f5f9' };
  },

  /**
   * 4대 패싯 명칭 및 아이콘
   * @param {string} facet
   */
  getFacetInfo(facet) {
    const facets = {
      unit_process: { label: '단위 공정 (Process)', badge: '공정', icon: 'Layers' },
      device: { label: '반도체 소자 (Device)', badge: '소자', icon: 'Cpu' },
      operations: { label: 'Fab 운영/수율 (Fab)', badge: '운영', icon: 'Activity' },
      materials_infra: { label: '소재/인프라 (Infra)', badge: '인프라', icon: 'Box' }
    };
    return facets[facet] || { label: facet, badge: facet, icon: 'File' };
  },

  /**
   * ISO 타임스탬프를 현지화 포맷으로 변환 (YYYY.MM.DD HH:mm)
   * @param {string} isoString
   */
  formatDateTime(isoString) {
    if (!isoString) return '-';
    try {
      const d = new Date(isoString);
      if (isNaN(d.getTime())) return isoString;
      const y = d.getFullYear();
      const m = String(d.getMonth() + 1).padStart(2, '0');
      const day = String(d.getDate()).padStart(2, '0');
      const h = String(d.getHours()).padStart(2, '0');
      const min = String(d.getMinutes()).padStart(2, '0');
      return `${y}.${m}.${day} ${h}:${min}`;
    } catch {
      return isoString;
    }
  }
};
