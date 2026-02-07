/**
 * WebSocket Event Normalizer v8
 *
 * Converts legacy v7 camelCase events to v8 snake_case format.
 * Ensures consistent event structure for the store.
 *
 * @module normalizeEvent
 */

// v7 → v8 type mapping (only for non-token events)
const EVENT_TYPE_MAP = {
  // Legacy camelCase → v8 snake_case
  conversationCreated: 'conversation_created',
  verificationItem: 'verification_item',
  verificationComplete: 'complete', // Terminal event
  phaseChange: 'phase',
  toolCall: 'tool',
  toolResult: 'tool',
}

// Token-like types that should become thinking(kind='token')
const TOKEN_TYPES = new Set(['token', 'tokens', 'stream', 'chunk'])

// Allowed normalized event types (v8 contract)
const ALLOWED_TYPES = new Set([
  'conversation_created',
  'phase',
  'thinking',
  'tool',
  'verification_item',
  'complete',
  'error',
])

// Terminal event types (must end a run)
export const TERMINAL_TYPES = new Set(['complete', 'error'])

/**
 * Convert any timestamp format to ISO string
 */
function toIsoTimestamp(value) {
  if (typeof value === 'string' && value.trim()) {
    // Validate it's a proper ISO timestamp
    const d = new Date(value)
    if (!isNaN(d.getTime())) return value
  }
  if (typeof value === 'number') {
    return new Date(value).toISOString()
  }
  return new Date().toISOString()
}

/**
 * Extract run_id from various possible locations in raw event
 */
function extractRunId(raw) {
  if (!raw || typeof raw !== 'object') return null

  // Direct properties (preferred)
  if (raw.run_id) return raw.run_id
  if (raw.runId) return raw.runId

  // Nested in data
  if (raw.data?.run_id) return raw.data.run_id
  if (raw.data?.runId) return raw.data.runId

  // Nested in payload (some backends)
  if (raw.payload?.run_id) return raw.payload.run_id
  if (raw.payload?.runId) return raw.payload.runId

  return null
}

/**
 * Extract conversation_id from various possible locations
 */
function extractConversationId(raw) {
  if (!raw || typeof raw !== 'object') return null

  if (raw.conversation_id) return raw.conversation_id
  if (raw.conversationId) return raw.conversationId
  if (raw.data?.conversation_id) return raw.data.conversation_id
  if (raw.data?.conversationId) return raw.data.conversationId
  if (raw.data?.id && raw.type === 'conversation_created') return raw.data.id

  return null
}

/**
 * Normalize error data to consistent format
 */
function normalizeErrorData(data) {
  if (typeof data === 'string') {
    return { message: data, code: 'UNKNOWN' }
  }
  if (data && typeof data === 'object') {
    return {
      message: data.message || data.error || data.detail || 'Unknown error',
      code: data.code || data.error_code || 'UNKNOWN',
      ...data,
    }
  }
  return { message: 'Unknown error', code: 'UNKNOWN' }
}

/**
 * Normalize token/stream data to thinking event format
 */
function normalizeTokenData(rawData) {
  if (typeof rawData === 'string') {
    return { kind: 'token', content: rawData }
  }
  if (!rawData || typeof rawData !== 'object') {
    return { kind: 'token', content: '' }
  }
  return {
    kind: 'token',
    content: rawData.content ?? rawData.token ?? rawData.text ?? rawData.chunk ?? '',
    iteration: rawData.iteration,
    phase: rawData.phase,
  }
}

/**
 * Normalize thinking event data
 */
function normalizeThinkingData(rawData) {
  if (!rawData || typeof rawData !== 'object') {
    return { kind: 'thought', message: '' }
  }
  // Already has kind (token or thought)
  if (rawData.kind) return rawData

  // Determine kind based on content
  if (rawData.content || rawData.token || rawData.text || rawData.chunk) {
    return {
      kind: 'token',
      content: rawData.content ?? rawData.token ?? rawData.text ?? rawData.chunk ?? '',
      iteration: rawData.iteration,
      phase: rawData.phase,
    }
  }

  return {
    kind: 'thought',
    message: rawData.message || rawData.thought || '',
    iteration: rawData.iteration,
    phase: rawData.phase,
    ...rawData,
  }
}

/**
 * Normalize phase event data
 */
function normalizePhaseData(rawData) {
  if (!rawData || typeof rawData !== 'object') {
    return { phase: 'unknown', status: 'started' }
  }
  return {
    phase: rawData.phase || rawData.name || 'unknown',
    status: rawData.status || 'started',
    message: rawData.message || rawData.description || '',
    ...rawData,
  }
}

/**
 * Normalize tool event data
 */
function normalizeToolData(rawData) {
  if (!rawData || typeof rawData !== 'object') {
    return { tool: 'unknown', params: {} }
  }
  return {
    tool: rawData.tool || rawData.name || rawData.tool_name || 'unknown',
    params: rawData.params || rawData.input || rawData.arguments || {},
    status: rawData.status || 'started',
    result: rawData.result || rawData.output,
    error: rawData.error,
    iteration: rawData.iteration,
    ...rawData,
  }
}

/**
 * Normalize verification_item event data
 */
function normalizeVerificationItemData(rawData) {
  if (!rawData || typeof rawData !== 'object') {
    return { check_name: 'unknown', status: 'running' }
  }

  // Determine status from various fields
  let status = rawData.status
  if (!status) {
    if (rawData.passed === true) status = 'passed'
    else if (rawData.passed === false) status = 'failed'
    else status = 'running'
  }

  return {
    check_name: rawData.check_name || rawData.name || rawData.check || 'unknown',
    status,
    output: rawData.output || rawData.result,
    error: rawData.error,
    ...rawData,
  }
}

/**
 * Normalize complete event data
 */
function normalizeCompleteData(rawData) {
  if (!rawData || typeof rawData !== 'object') {
    return { response: '' }
  }
  return {
    response: rawData.response || rawData.content || rawData.result || '',
    verification: rawData.verification,
    verdict: rawData.verdict,
    tools_used: rawData.tools_used || rawData.toolsUsed || [],
    iterations: rawData.iterations,
    duration_ms: rawData.duration_ms || rawData.durationMs,
    model: rawData.model || rawData.model_used || rawData.modelUsed,
    ...rawData,
  }
}

/**
 * Normalize conversation_created event data
 */
function normalizeConversationCreatedData(rawData, rawEvent) {
  if (!rawData || typeof rawData !== 'object') {
    return { conversation_id: null }
  }

  const conversationId =
    rawData.conversation_id ||
    rawData.conversationId ||
    rawData.id ||
    extractConversationId(rawEvent)

  return {
    conversation_id: conversationId,
    title: rawData.title,
    ...rawData,
  }
}

/**
 * Main normalizer function
 *
 * @param {Object} rawEvent - Raw WebSocket event
 * @returns {Object|null} Normalized event or null if invalid/unsupported
 */
export function normalizeEvent(rawEvent) {
  if (!rawEvent || typeof rawEvent !== 'object') return null

  // Extract raw type from various possible fields
  const rawType = rawEvent.type || rawEvent.event || rawEvent.action
  if (!rawType) return null

  // Extract metadata
  const timestamp = toIsoTimestamp(rawEvent.timestamp || rawEvent.time || rawEvent.ts)
  const run_id = extractRunId(rawEvent)
  const conversation_id = extractConversationId(rawEvent)

  // Get raw data
  let rawData = rawEvent.data ?? rawEvent.payload ?? {}

  // Determine final type and normalize data
  let type
  let data

  // Handle token-like types first (before mapping)
  if (TOKEN_TYPES.has(rawType)) {
    type = 'thinking'
    data = normalizeTokenData(rawData)
  } else {
    // Map to v8 type
    type = EVENT_TYPE_MAP[rawType] || rawType

    // Normalize based on type
    switch (type) {
      case 'thinking':
        data = normalizeThinkingData(rawData)
        break

      case 'phase':
        data = normalizePhaseData(rawData)
        break

      case 'tool':
        data = normalizeToolData(rawData)
        break

      case 'verification_item':
        data = normalizeVerificationItemData(rawData)
        break

      case 'verification_complete':
        // Map to 'complete' but preserve verification data
        type = 'complete'
        data = normalizeCompleteData(rawData)
        break

      case 'complete':
        data = normalizeCompleteData(rawData)
        break

      case 'error':
        data = normalizeErrorData(rawData)
        break

      case 'conversation_created':
        data = normalizeConversationCreatedData(rawData, rawEvent)
        break

      default:
        // Unknown type - pass through data as-is
        data = rawData
    }
  }

  // Reject unsupported types
  if (!ALLOWED_TYPES.has(type)) {
    return null
  }

  return {
    type,
    timestamp,
    run_id,
    conversation_id,
    data,
  }
}

/**
 * Check if event is a terminal event (ends a run)
 */
export function isTerminalEvent(event) {
  if (!event) return false
  return TERMINAL_TYPES.has(event.type)
}

/**
 * Check if event requires a run_id
 */
export function requiresRunId(event) {
  if (!event) return false
  // conversation_created doesn't always require run_id upfront
  if (event.type === 'conversation_created') return false
  return true
}

export default normalizeEvent
