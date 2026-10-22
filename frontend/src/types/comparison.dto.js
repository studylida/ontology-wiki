/**
 * [계층 5] Comparison & Alternative Reasoning DTOs
 * Backend (backend/app/schemas/comparison.py)와 1:1 대칭
 */

/**
 * @typedef {Object} ClarificationQuestionDTO
 * @property {string} questionId
 * @property {string} question
 * @property {Array<string>} options
 */

/**
 * @typedef {Object} ClarifyBranchDTO
 * @property {string} branchId
 * @property {string} title
 * @property {string} description
 * @property {string} targetA
 * @property {string} targetB
 * @property {string} [targetAName] - 표시명; targetA는 등록 ID
 * @property {string} [targetBName] - 표시명; targetB는 등록 ID
 * @property {string} domain
 * @property {string} [rationale]
 */

/**
 * @typedef {Object} DynamicAxisTagDTO
 * @property {string} axisKey
 * @property {string} label
 * @property {'thermal'|'defect'|'fab'|'electrical'} category
 * @property {string} description
 */

/**
 * @typedef {Object} ClarifyResponseDTO
 * @property {string} recognizedIntent
 * @property {Array<ClarifyBranchDTO>} branches
 * @property {Array<ClarificationQuestionDTO>} [clarificationQuestions]
 * @property {Array<DynamicAxisTagDTO>} [dynamicAxesPool]
 */

/**
 * @typedef {Object} ComparisonSessionCreateDTO
 * @property {string} title
 * @property {string} userId
 * @property {string} query
 * @property {Object} contextParams
 * @property {string} [folderId]
 */

/**
 * @typedef {Object} ComparisonMatrixRowDTO
 * @property {string} axis - 파라미터/물성 축 명칭
 * @property {'thermal'|'defect'|'fab'|'electrical'} axisCategory - 분류 축
 * @property {string} categoryLabel - 카테고리 라벨
 * @property {string} valA - Target A 기준값
 * @property {string} valB - Target B 기준값
 * @property {string|null} [evidenceA] - Target A 출처
 * @property {string|null} [evidenceB] - Target B 출처
 * @property {boolean} isGap - 온톨로지 공인 실측 미등록(Knowledge Gap) 여부
 * @property {string} [basis] - 출처 또는 측정 조건 안내
 */

/**
 * @typedef {Object} ComparisonSessionDTO
 * @property {string} id
 * @property {string} userId
 * @property {string} title
 * @property {boolean} isPinned
 * @property {string|null} folderId
 * @property {string} query
 * @property {Object} contextParams
 * @property {Array<ComparisonMatrixRowDTO>} [matrix]
 * @property {Array<Object>} [snapshots]
 * @property {string|null} [exportedReviewId]
 * @property {string} createdAt
 * @property {string} updatedAt
 */

/**
 * @typedef {Object} TuneAdvisorRequestDTO
 * @property {string} userPrompt - 꼬리질문 입력
 * @property {'compensationA'|'compensationB'|null} [applyCompensation]
 * @property {Object} [manualConditions]
 */

/**
 * @typedef {Object} TuneAdvisorResponseDTO
 * @property {string} userPrompt
 * @property {string} [riskDetected]
 * @property {Object} [advisorRecommendation]
 * @property {Object} [appliedResult]
 * @property {string} [advice] - 공학적 인과 분석 조언
 * @property {Array<string>} [physicalGuardWarnings] - 물리 마진 경고
 * @property {boolean} [requiresOverride=false] - 예외 사유 요구 여부
 * @property {Array<Object>} [tuningEntries]
 */

/**
 * @typedef {Object} ExportReviewRequestDTO
 * @property {string} conceptId
 * @property {string} title
 * @property {string} [overrideReason]
 * @property {string} author
 * @property {string} reviewType
 */
