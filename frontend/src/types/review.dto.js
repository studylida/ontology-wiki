/**
 * [계층 5] Review & Governance DTOs
 */

/**
 * @typedef {Object} ReviewTicketCreateDTO
 * @property {string} conceptId - 대상 개념 ID
 * @property {string} proposedChange - 개정 제안 내용
 * @property {string} reason - 발의 사유
 * @property {boolean} [isNewConcept=false] - 완전 신규 개념 발의 여부
 * @property {Object} [newConceptData] - 신규 개념 메타데이터
 */

/**
 * @typedef {Object} ConceptPlacementRecommendRequestDTO
 * @property {string} title - 기술/개념명
 * @property {string} summary - 기술 개요 및 도입 목적
 */

/**
 * @typedef {Object} ConceptPlacementRecommendResponseDTO
 * @property {string} suggestedFacet - 추천 패싯
 * @property {number} suggestedScaleLevel - 추천 스케일 레벨
 * @property {string} suggestedProcessCategory - 추천 공정군
 * @property {string|null} suggestedParentConceptId - 추천 상위 연계 개념 ID
 * @property {string} reasoning - AI 에이전트 추천 추론 근거
 */
