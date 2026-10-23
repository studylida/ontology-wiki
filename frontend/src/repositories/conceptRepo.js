/**
 * [계층 4] Concept & Causal Ontology Repository
 * 백엔드 /api/v1/concepts와 1:1 통신하는 순수 I/O 클라이언트
 */

import { httpClient } from './httpClient';

export const conceptRepo = {
  /** Registered concept suggestions and search results from the existing Spotlight API. */
  async search(query = '') {
    return httpClient.get(`/search/spotlight?${new URLSearchParams({q: query})}`);
  },
  /**
   * 좌측 4축 계층형 온톨로지 네비게이션 트리 조회 (업무 분야 또는 물리 규모 필터 지원)
   * @param {string|{ facet?: string, scale?: number, expandedId?: string }} [facetOrOptions='unit_process']
   * @param {string} [expandedId]
   * @returns {Promise<import('../types/concept.dto').ConceptTreeResponseDTO>}
   */
  async getTree(facetOrOptions = 'unit_process', expandedId = null) {
    const params = new URLSearchParams();
    if (typeof facetOrOptions === 'object' && facetOrOptions !== null) {
      if (facetOrOptions.scale !== null && facetOrOptions.scale !== undefined) {
        params.append('scale', String(facetOrOptions.scale));
      } else if (facetOrOptions.facet) {
        params.append('facet', facetOrOptions.facet);
      }
      if (facetOrOptions.expandedId) params.append('expandedId', facetOrOptions.expandedId);
    } else {
      if (facetOrOptions) params.append('facet', facetOrOptions);
      if (expandedId) params.append('expandedId', expandedId);
    }
    return httpClient.get(`/concepts/tree?${params.toString()}`);
  },

  /**
   * 개념 상세 및 적응형 실무 사례 조회 (JWT 인가에 따른 L3 동적 마스킹 반영)
   * @param {string} conceptId
   * @returns {Promise<import('../types/concept.dto').ConceptDetailResponseDTO>}
   */
  async getConceptDetail(conceptId) {
    return httpClient.get(`/concepts/${conceptId}`);
  },

  /** @returns {Promise<import('../types/concept.dto').PerspectiveCaseDTO>} */
  async generateCaseContextExplanation(conceptId, caseId) {
    return httpClient.post(`/concepts/${encodeURIComponent(conceptId)}/perspectives/${encodeURIComponent(caseId)}/context-explanation`, {});
  },

  /**
   * 1~2 hop 인과 서브그래프 및 보상 파라미터 조회 (0.65ms Recursive CTE)
   * @param {string} conceptId
   * @param {number} [depth=2]
   * @param {'both'|'out'|'in'} [direction='both']
   * @returns {Promise<import('../types/concept.dto').CausalSubgraphResponseDTO>}
   */
  async getSubgraph(conceptId, depth = 2, direction = 'both') {
    const params = new URLSearchParams({
      depth: String(depth),
      direction
    });
    return httpClient.get(`/concepts/${conceptId}/causal-subgraph?${params.toString()}`);
  },

  /**
   * 0ms 인라인 문맥 해설 조회
   * @param {string} conceptId
   * @param {string} termId
   * @param {string} [perspectiveId='default']
   * @returns {Promise<import('../types/concept.dto').ContextualExplanationDTO>}
   */
  async getContextualExplainer(conceptId, termId, perspectiveId = 'default', context = '') {
    return httpClient.post(`/concepts/${conceptId}/contextual-explainer`, {
      term_id: termId, perspective_id: perspectiveId, selection_context: context
    });
  },

  /**
   * 신규 개념 온톨로지 편입 위치 AI 자동 추천
   * @param {import('../types/review.dto').ConceptPlacementRecommendRequestDTO} data
   * @returns {Promise<import('../types/review.dto').ConceptPlacementRecommendResponseDTO>}
   */
  async recommendPlacement(data) {
    return httpClient.post('/concepts/recommend-placement', data);
  }
};
