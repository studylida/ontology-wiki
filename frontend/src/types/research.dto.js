/**
 * [계층 5] Deep Research & External Literature DTOs
 * 백엔드 /api/v1/research 엔드포인트의 입력/출력 인터페이스 규약
 */

/**
 * @typedef {Object} ResearchSessionSummaryDTO
 * @property {string} id
 * @property {string} searchTopic
 * @property {number} evidenceCount
 * @property {number} candidateCount
 * @property {string} createdAt
 */

/**
 * @typedef {Object} ScopeFilterDTO
 * @property {string} filterId
 * @property {string} label
 * @property {boolean} selected
 */

/**
 * @typedef {Object} ComparisonResearchContextDTO
 * @property {string} comparisonSessionId
 * @property {string} originalQuestion
 * @property {string} targetA - 등록 개념 ID
 * @property {string} targetB - 등록 개념 ID
 * @property {string} targetAName
 * @property {string} targetBName
 * @property {Array<string>} conditions
 * @property {string} gapAxis
 * @property {string} targetSide
 */

/**
 * @typedef {Object} ResearchEvidenceFeedItemDTO
 * @property {string} id - 공인 문헌 ID (예: 'E-21')
 * @property {string} sourceName - 문헌/논문/표준 명칭
 * @property {'official_whitepaper'|'academic_peer_reviewed'|'international_standard'|string} sourceType - 출처 유형
 * @property {string} publisher - 발행 기관
 * @property {string} publishedDate - 발행 일자
 * @property {string} quote - 핵심 인용구 및 실측 데이터
 * @property {string} sectionContext - 섹션 및 페이지 위치
 * @property {number} relevanceScore - 과거 검색 점수 (새 결과의 관련성 판단에 사용하지 않음)
 * @property {string} externalUrl - 원문 열람 URL
 * @property {string} urlLabel - 링크 라벨
 * @property {ResearchAssessmentDTO|null} assessment
 * @property {Array<{id:string,text:string,sectionContext:string|null}>} readSegments
 * @property {string} credibilityTier - 신뢰성 티어
 * @property {'metadata'|'abstract'|'source_excerpt'|'registered_excerpt'} retrievalStatus - 확보한 내용의 범위
 */

/**
 * @typedef {Object} SynthesisReportDTO
 * @property {string} title - 리포트 제목
 * @property {string} narrativeMarkdown - 교차 분석 종합 서술
 * @property {Array<string>} consensusFacts - 공통 합의 사실 목록
 * @property {Array<string>} tensionGaps - 이견 및 기술적 한계 지점 목록
 */

/**
 * @typedef {Object} KnowledgeCandidateDTO
 * @property {string} candidateId - 지식 후보 식별자
 * @property {string} candidateType - 개념 유형 ('신규 개념', '물리 한계 보완' 등)
 * @property {string} title - 지식 명칭
 * @property {string} summary - 지식 요약
 * @property {Object} draftPayload - 정형 온톨로지 페이로드 (content, specifications, relations)
 * @property {Array<string>} evidenceIds - 뒷받침하는 출처 ID 목록
 */

/**
 * @typedef {Object} ResearchClarifyResponseDTO
 * @property {string} searchTopic
 * @property {Array<ScopeFilterDTO>} scopeFilters
 * @property {Array<string>} targetInstitutions
 * @property {ResearchSearchPlanDTO|null} searchPlan
 */

/**
 * @typedef {Object} ResearchDiscoverResponseDTO
 * @property {string} sessionId
 * @property {string} searchTopic
 * @property {number} totalEvidencesFound
 * @property {Array<ResearchEvidenceFeedItemDTO>} evidenceFeed
 * @property {boolean} synthesisReady
 * @property {string} ctaButtonLabel
 * @property {ComparisonResearchContextDTO|null} comparisonContext
 * @property {string} notice
 * @property {ResearchDiscoveryContextDTO|null} discoveryContext
 */

/**
 * @typedef {Object} ResearchSynthesizeResponseDTO
 * @property {string} sessionId
 * @property {string} searchTopic
 * @property {SynthesisReportDTO} synthesisReport
 * @property {Array<KnowledgeCandidateDTO>} candidates
 */

/**
 * @typedef {Object} ExportCandidateTicketResponseDTO
 * @property {string} ticketId - 생성된 거버넌스 티켓 ID (예: 'rev-20261021-xxxx')
 * @property {string} candidateId
 * @property {string} status - 상태 ('pending')
 * @property {string} conceptTitle
 * @property {string} message
 */

/**
 * Research report generationStatus: ai_generated | source_only | legacy_unverified.
 * Candidate draftPayload: {conceptId, content} for concept_enrichment; for new_concept,
 * {isNewConcept:true, title, engName?, content, purpose, domainFacet:null|string,
 * scaleLevel:null|number, processCategory:string}. Unknown classification stays unknown until approval.
 */

/**
 * @typedef {Object} ResearchSearchPlanDTO
 * @property {string} originalQuestion
 * @property {string} interpretedQuestion
 * @property {string[]} assumptions
 * @property {string[]} searchQueries
 * @property {string|null} clarificationQuestion
 * @property {'ready'|'needs_clarification'|'source_only'} status
 */
/**
 * @typedef {Object} ResearchAssessmentDTO
 * @property {'included'|'deferred'|'excluded'} decision
 * @property {string} documentSummary
 * @property {string} inclusionReason
 * @property {string} usefulness
 * @property {string[]} limitations
 * @property {string[]} evidenceReferences - server-owned read segment IDs
 */
/**
 * @typedef {Object} ResearchDiscoveryContextDTO
 * @property {ResearchSearchPlanDTO} plan
 * @property {string[]} queriesExecuted
 * @property {'complete'|'partial'|'source_only'} generationStatus
 * @property {string[]} remainingQuestions
 * @property {string} stopReason
 * @property {string[]} [pendingQueries]
 * @property {Array<{query:string,newDocumentCount:number,evaluatedCount:number,elapsedMs:number}>} [searchRounds]
 * @property {boolean} [canContinue]
 * @property {number} [schemaVersion]
 */

/**
 * Evidence extensions: deferReason is content_unavailable/insufficient_content/not_assessed/assessment_failed.
 * assessmentCurrent=false keeps the previous explanation for history but blocks downstream selection.
 * acquisitionAttempts contain server-owned {url,resolvedUrl?,at,outcome,contentType?}.
 * readSegments may include sourceUrl/contentKind; external_excerpt means public partial text, never full reading.
 * Session responses include updatedAt for conditional continuation. Synthesis may have needsRefresh.
 */
