/**
 * [계층 5] Concept & Causal Ontology DTOs
 * Backend Pydantic DTO (backend/app/schemas/ontology.py)와 1:1 대칭
 */

export const DOMAIN_FACET_LABELS = {
  device: '소자·제품·구조',
  unit_process: '제조 공정',
  operations: '팹 운영·제어',
  materials_infra: '소재·설비·인프라'
};

/**
 * @typedef {Object} ExtractedConceptClassificationDTO
 * @property {'device'|'unit_process'|'operations'|'materials_infra'|null} domainFacet
 * @property {string} category
 * @property {number|null} scaleLevel
 * @property {string|null} [classificationNote]
 * @property {Array<string>} [validationWarnings]
 */

/**
 * @typedef {Object} ConceptTreeNodeDTO
 * @property {string} id
 * @property {string} title
 * @property {string} [engName]
 * @property {Array<string>} [aliases]
 * @property {'category'|'concept'} type
 * @property {number} [scaleLevel]
 * @property {string} [badge]
 * @property {string} [status]
 * @property {boolean} [hasPerspectives]
 * @property {Array<ConceptTreeNodeDTO>} [children]
 */

/**
 * @typedef {Object} ConceptTreeResponseDTO
 * @property {'device'|'unit_process'|'operations'|'materials_infra'} currentFacet
 * @property {number} totalNodes
 * @property {Array<ConceptTreeNodeDTO>} tree
 */

/**
 * @typedef {Object} PrincipleDTO
 * @property {number} step
 * @property {string} title
 * @property {string} content
 * @property {string|null} [formula] - LaTeX KaTeX 수식 문자열
 */

/**
 * @typedef {Object} LimitationDTO
 * @property {string} title
 * @property {string} description
 * @property {Array<string>} [evidenceIds]
 */

/**
 * @typedef {Object} SpecificationDTO
 * @property {string} parameter
 * @property {string|null} value
 * @property {string|null} unit
 * @property {string|null} [safetyMargin]
 * @property {string|null} [role]
 * @property {string|null} [tradeoff]
 * @property {string|null} [rationale]
 * @property {string|null} [evidenceQuote]
 * @property {Object<string,string>} [fieldEvidenceQuotes]
 * @property {string[]} [evidenceIds]
 * @property {boolean} [isConfidential]
 * @property {string} [evidenceId]
 */

/**
 * @typedef {Object} CaseContextExplanationDTO
 * @property {string} basisHash
 * @property {string} generatorVersion
 * @property {string} generatedAt
 * @property {{explanation: string, background?: string|null}} content
 */

/**
 * @typedef {Object} PerspectiveCaseDTO
 * @property {string} id
 * @property {string} conceptId
 * @property {string} perspectiveId
 * @property {string} perspectiveTitle
 * @property {string} perspectiveBadge
 * @property {string} [managementCode]
 * @property {string} [contextNarrative]
 * @property {Array<SpecificationDTO>} specifications
 * @property {string} [caution]
 * @property {string} [evidenceId]
 * @property {boolean} isMasked
 * @property {CaseContextExplanationDTO|null} [contextExplanation]
 * @property {'ready'|'missing'|'stale'|'generating'|'restricted'} [contextExplanationState]
 * @property {string|null} [contextExplanationBasisHash]
 */

/**
 * @typedef {Object} ContextualExplanationDTO
 * @property {string|null} [childConceptId]
 * @property {string} parentConceptId
 * @property {string} title
 * @property {string} definition
 * @property {string} contextSentence
 * @property {boolean} cached
 * @property {string|null} [sourceEvidence]
 * @property {string|null} [deepLink]
 */

/**
 * @typedef {Object} SubgraphNodeDTO
 * @property {string} id
 * @property {string} label
 * @property {string} category
 * @property {number} scaleLevel
 * @property {boolean} isCenter
 */

/**
 * @typedef {Object} CompensatingParamDTO
 * @property {string} parameter
 * @property {string} compensationFormula
 * @property {string} tradeoffCost
 */

/**
 * @typedef {Object} SubgraphEdgeDTO
 * @property {string} id
 * @property {string} source
 * @property {string} target
 * @property {string} relationType
 * @property {string} polarity
 * @property {number} weight
 * @property {string|null} [mechanismLabel]
 * @property {CompensatingParamDTO|null} [compensatingParams]
 * @property {string|null} [evidenceId]
 */

/**
 * @typedef {Object} CausalSubgraphResponseDTO
 * @property {string} centralConceptId
 * @property {{ nodes: Array<SubgraphNodeDTO>, edges: Array<SubgraphEdgeDTO> }} graph
 */

/**
 * @typedef {Object} ConceptDetailResponseDTO
 * @property {Array<string>} evidenceIds - 개요·목적만 있는 문서도 포함하는 실제 출처 ID
 * @property {string} id
 * @property {string} title
 * @property {string} [engName]
 * @property {Array<string>} aliases
 * @property {string} domainFacet
 * @property {string} processCategory
 * @property {number} scaleLevel
 * @property {string} scaleName
 * @property {string} version
 * @property {string} status
 * @property {string|null} [lastReviewedAt]
 * @property {string|null} [lastReviewedBy]
 * @property {string} summary
 * @property {string} purpose
 * @property {Array<PrincipleDTO>} principles
 * @property {Array<LimitationDTO>} limitations
 * @property {Object} relations
 * @property {Array<PerspectiveCaseDTO>} perspectives
 * @property {Array<string>} [selectionTerms] - 화면 선택 범위 보정용 등록명·별칭
 * @property {Record<string, ContextualExplanationDTO>} [preloadedExplainers]
 * @property {EnrichedRelationsDTO} [enrichedRelations]
 * @property {Array<ScaleLadderStepDTO>} [scaleLadder]
 */

/**
 * @typedef {Object} EnrichedRelationItemDTO
 * @property {string} id
 * @property {string} name
 * @property {string} [relationType]
 * @property {string} [reason]
 * @property {string} [mechanism]
 * @property {number} [scaleLevel]
 * @property {boolean} [isRegistered]
 * @property {string} [commonGoal]
 * @property {string} [tradeoff]
 * @property {CompensatingParamDTO} [compensatingParams]
 */

/**
 * @typedef {Object} EnrichedRelationsDTO
 * @property {Array<EnrichedRelationItemDTO>} previousSteps
 * @property {Array<EnrichedRelationItemDTO>} nextSteps
 * @property {Array<EnrichedRelationItemDTO>} alternatives
 * @property {Array<EnrichedRelationItemDTO>} partOf
 * @property {Array<EnrichedRelationItemDTO>} isA
 * @property {Array<EnrichedRelationItemDTO>} hasParts
 * @property {Array<EnrichedRelationItemDTO>} subtypes
 */

/**
 * @typedef {Object} ScaleLadderStepDTO
 * @property {number} scaleLevel
 * @property {string} scaleName
 * @property {string} title
 * @property {string} description
 * @property {string} [governingPhysics]
 * @property {number} hops - 현재 개념에서 실제 관계 연결 단계 (0~2)
 * @property {Array<SubgraphEdgeDTO>} connections - 종류·방향·사유가 보존된 등록 관계
 * @property {boolean} isCurrent
 * @property {string} [entityId]
 * @property {string} [entityName]
 */

/**
 * @typedef {Object} SpotlightSearchResultDTO
 * @property {string} id - 실제 등록 개념 ID
 * @property {string} title
 * @property {string} engName
 * @property {string} domainFacet
 * @property {number} scaleLevel
 */

/**
 * @typedef {Object} SpotlightSearchResponseDTO
 * @property {string} query
 * @property {number} totalIndexed
 * @property {number} totalMatches
 * @property {Array<SpotlightSearchResultDTO>} results
 */
