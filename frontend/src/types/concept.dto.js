/**
 * [계층 5] Concept & Causal Ontology DTOs
 * Backend Pydantic DTO (backend/app/schemas/ontology.py)와 1:1 대칭
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
 * @property {string} value
 * @property {string} unit
 * @property {string} [safetyMargin]
 * @property {boolean} [isConfidential]
 * @property {string} [evidenceId]
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
 */

/**
 * @typedef {Object} ContextualExplanationDTO
 * @property {string} childConceptId
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
 * @property {Record<string, ContextualExplanationDTO>} [preloadedExplainers]
 */
