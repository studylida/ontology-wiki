/**
 * [계층 3] Relation Domain Service
 * - 온톨로지 인과 관계 데이터 가공, 다중 전·후 공정 파이프라인 정리 및 등록 상태 판별
 * - UI 비의존적 순수 비즈니스 로직
 */

export const relationService = {
  /**
   * 보강된 관계망 데이터 또는 기존 relations 객체로부터 다중 아이템 목록을 안전하게 추출
   * @param {import('../types/concept.dto').ConceptDetailResponseDTO} conceptDetail
   * @param {'previousSteps'|'nextSteps'|'alternatives'|'partOf'|'isA'|'hasParts'|'subtypes'} key
   * @returns {Array<import('../types/concept.dto').EnrichedRelationItemDTO>}
   */
  getRelationItems(conceptDetail, key) {
    if (!conceptDetail) return [];

    // 1. 백엔드 Service가 보강한 enrichedRelations 우선 참조
    if (conceptDetail.enrichedRelations && Array.isArray(conceptDetail.enrichedRelations[key])) {
      return conceptDetail.enrichedRelations[key];
    }

    // 2. 레거시 relations 객체 폴백 매핑
    const rawRelations = conceptDetail.relations || {};
    const fallbackMap = {
      previousSteps: rawRelations.previous_step || [],
      nextSteps: rawRelations.next_step || [],
      alternatives: rawRelations.alternative_to || [],
      partOf: rawRelations.part_of || [],
      isA: rawRelations.is_a || []
    };

    const items = fallbackMap[key] || [];
    return items.map((item) => {
      const id = item.id || item.targetId;
      const name = item.name || item.targetName || item.title || id;
      return {
        id,
        name,
        relationType: key,
        reason: item.reason || item.mechanism || null,
        commonGoal: item.commonGoal || null,
        tradeoff: item.tradeoff || null,
        scaleLevel: item.scaleLevel ?? null,
        isRegistered: item.isRegistered === true
      };
    });
  },

  /**
   * 스케일 레벨별 공식 한국어 공학 레이블 반환
   * @param {number} scaleLevel
   * @returns {string}
   */
  getScaleLabel(scaleLevel) {
    switch (scaleLevel) {
      case 5:
        return 'Scale 5: 팹·운영·인프라';
      case 4:
        return 'Scale 4: 설비·시스템·모듈';
      case 3:
        return 'Scale 3: 공정·레시피';
      case 2:
        return 'Scale 2: 박막·소자·회로·패키지';
      case 1:
        return 'Scale 1: 원자·양자·재료 물성';
      default:
        return scaleLevel ? `Scale ${scaleLevel}` : '규모 미등록';
    }
  },

  /**
   * 서버가 실제 등록된 연결로 구성한 규모 계층만 전달
   * @param {import('../types/concept.dto').ConceptDetailResponseDTO} conceptDetail
   * @returns {Array<import('../types/concept.dto').ScaleLadderStepDTO>}
   */
  getScaleConnections(step, ladder) {
    const names = new Map(ladder.map(item => [item.entityId, item.title]));
    const labels = {next_step: '후속 공정', previous_step: '선행 공정', alternative_to: '기술적 대안', part_of: '구성 요소 → 소속 대상', is_a: '하위 종류 → 상위 분류'};
    return (step.connections || []).map(link => ({...link,
      sourceName: names.get(link.source) || link.source,
      targetName: names.get(link.target) || link.target,
      label: labels[link.relationType] || link.relationType
    }));
  },

  getScaleLadder(conceptDetail) {
    return Array.isArray(conceptDetail?.scaleLadder) ? conceptDetail.scaleLadder : [];
  }
};
