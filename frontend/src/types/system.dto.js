/**
 * [계층 5] System Health & Version DTOs
 * Backend (backend/app/schemas/system.py) 매핑
 */

/**
 * @typedef {Object} HealthServicesStatusDTO
 * @property {'connected'|'offline'} database
 * @property {'connected'|'fallback_in_memory'} redisCache
 * @property {'ready'|string} llmGateway
 */

/**
 * @typedef {Object} HealthResponseDTO
 * @property {'healthy'|'degraded'|'maintenance'} status
 * @property {string} timestamp
 * @property {HealthServicesStatusDTO} services
 * @property {string} message
 * @property {Array<string>} activeFallbacks
 */

/**
 * @typedef {Object} VersionResponseDTO
 * @property {string} activeVersion
 * @property {string} latestVersion
 * @property {boolean} isUpdateAvailable
 * @property {string} publishedAt
 * @property {number} totalConcepts
 * @property {number} totalEvidences
 * @property {string} schemaHash
 * @property {Object} systemConfig
 */

/**
 * @typedef {Object} AuditIntegrityResponseDTO
 * @property {'VERIFIED'|'CORRUPTED'} status
 * @property {boolean} valid
 * @property {boolean} chainValid
 * @property {number} totalLogs
 * @property {number} totalVerifiedLogs
 * @property {boolean} tamperDetected
 * @property {string} merkleRootHash
 * @property {string} message
 */
