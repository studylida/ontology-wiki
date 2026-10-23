/**
 * [계층 5] Chatbot DTOs
 * 백엔드 /api/v1/chatbot 엔드포인트의 입력/출력 인터페이스 규약
 */

/**
 * @typedef {Object} ChatbotContextDTO
 * @property {string|null} conceptId
 * @property {string} conceptTitle
 * @property {number|null} scaleLevel
 * @property {string} scaleBadge
 * @property {string} engineMode
 * @property {string} engineModeLabel
 * @property {Array<string>} quickQuestionChips
 */

/**
 * @typedef {Object} ChatbotMessageRequestDTO
 * @property {'local'|'global'} [knowledgeScope='local']
 * @property {string} message - 엔지니어 질문
 * @property {string|null} [conceptId] - 현재 열람 중인 개념 ID
 * @property {string} [scaleLevel='3'] - 공정 스케일
 */

/**
 * @typedef {Object} ChatbotMessageResponseDTO
 * @property {'local'|'global'} knowledgeScope
 * @property {'factoid'|'causal_clarifier'|'action_trigger'|'error'} pathType
 * @property {string} answerMarkdown
 * @property {Array<Object>} [sourceEvidences]
 * @property {Array<string>} [suggestedChips]
 * @property {Array<string>} [citations]
 * @property {Array<string>} [followUpChips]
 * @property {Object} [actionPayload]
 */

/**
 * @typedef {Object} ChatbotMessageItem
 * @property {'local'|'global'} [knowledgeScope]
 * @property {'user'|'assistant'} sender
 * @property {string} text
 * @property {string} timestamp
 * @property {'factoid'|'causal_clarifier'|'action_trigger'|'error'} [pathType]
 * @property {Array<string>} [citations]
 * @property {Array<string>} [followUpChips]
 * @property {Object} [actionPayload]
 * @property {boolean} [isStreaming]
 */
