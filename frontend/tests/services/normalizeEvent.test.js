import { describe, it, expect } from 'vitest'
import { normalizeEvent, isTerminalEvent, requiresRunId, TERMINAL_TYPES } from '@/services/ws/normalizeEvent'

describe('normalizeEvent', () => {
  describe('Type Mapping v7 → v8', () => {
    it('maps conversationCreated to conversation_created', () => {
      const input = {
        type: 'conversationCreated',
        run_id: 'run-1',
        timestamp: '2026-01-28T10:00:00.000Z',
        data: { id: 'conv-1', title: 'Hello' },
      }

      const result = normalizeEvent(input)

      expect(result.type).toBe('conversation_created')
      expect(result.run_id).toBe('run-1')
      expect(result.data.conversation_id).toBe('conv-1')
      expect(result.data.title).toBe('Hello')
    })

    it('maps verificationItem to verification_item', () => {
      const input = {
        type: 'verificationItem',
        run_id: 'run-1',
        data: { name: 'syntax_check', passed: true },
      }

      const result = normalizeEvent(input)

      expect(result.type).toBe('verification_item')
      expect(result.data.check_name).toBe('syntax_check')
      expect(result.data.status).toBe('passed')
    })

    it('maps verificationComplete to complete', () => {
      const input = {
        type: 'verificationComplete',
        run_id: 'run-2',
        data: { verdict: { status: 'PASS' } },
      }

      const result = normalizeEvent(input)

      expect(result.type).toBe('complete')
      expect(result.run_id).toBe('run-2')
      expect(result.data.verdict.status).toBe('PASS')
    })

    it('maps phaseChange to phase', () => {
      const input = {
        type: 'phaseChange',
        run_id: 'run-1',
        data: { phase: 'execute', status: 'started' },
      }

      const result = normalizeEvent(input)

      expect(result.type).toBe('phase')
      expect(result.data.phase).toBe('execute')
      expect(result.data.status).toBe('started')
    })

    it('maps toolCall to tool', () => {
      const input = {
        type: 'toolCall',
        run_id: 'run-1',
        data: { tool: 'execute_command', params: { command: 'ls' } },
      }

      const result = normalizeEvent(input)

      expect(result.type).toBe('tool')
      expect(result.data.tool).toBe('execute_command')
      expect(result.data.params.command).toBe('ls')
    })
  })

  describe('Token/Thinking Normalization', () => {
    it('normalizes tokens to thinking events with kind=token', () => {
      const input = {
        type: 'tokens',
        run_id: 'run-1',
        data: { content: 'Hello' },
      }

      const result = normalizeEvent(input)

      expect(result.type).toBe('thinking')
      expect(result.run_id).toBe('run-1')
      expect(result.data.kind).toBe('token')
      expect(result.data.content).toBe('Hello')
    })

    it('normalizes token (singular) to thinking', () => {
      const input = {
        type: 'token',
        run_id: 'run-1',
        data: { token: 'World' },
      }

      const result = normalizeEvent(input)

      expect(result.type).toBe('thinking')
      expect(result.data.kind).toBe('token')
      expect(result.data.content).toBe('World')
    })

    it('normalizes stream to thinking', () => {
      const input = {
        type: 'stream',
        run_id: 'run-1',
        data: { text: 'Streaming...' },
      }

      const result = normalizeEvent(input)

      expect(result.type).toBe('thinking')
      expect(result.data.kind).toBe('token')
      expect(result.data.content).toBe('Streaming...')
    })

    it('normalizes chunk to thinking', () => {
      const input = {
        type: 'chunk',
        run_id: 'run-1',
        data: { chunk: 'A chunk' },
      }

      const result = normalizeEvent(input)

      expect(result.type).toBe('thinking')
      expect(result.data.kind).toBe('token')
      expect(result.data.content).toBe('A chunk')
    })

    it('handles string token data', () => {
      const input = {
        type: 'tokens',
        run_id: 'run-1',
        data: 'Direct string',
      }

      const result = normalizeEvent(input)

      expect(result.data.kind).toBe('token')
      expect(result.data.content).toBe('Direct string')
    })

    it('preserves thinking event with existing kind', () => {
      const input = {
        type: 'thinking',
        run_id: 'run-1',
        data: { kind: 'thought', message: 'Analyzing...' },
      }

      const result = normalizeEvent(input)

      expect(result.type).toBe('thinking')
      expect(result.data.kind).toBe('thought')
      expect(result.data.message).toBe('Analyzing...')
    })
  })

  describe('Error Normalization', () => {
    it('wraps string errors into message payload', () => {
      const input = {
        type: 'error',
        run_id: 'run-3',
        data: 'Connection failed',
      }

      const result = normalizeEvent(input)

      expect(result.type).toBe('error')
      expect(result.data.message).toBe('Connection failed')
      expect(result.data.code).toBe('UNKNOWN')
    })

    it('extracts message from error object', () => {
      const input = {
        type: 'error',
        run_id: 'run-3',
        data: { error: 'Timeout', code: 'TIMEOUT' },
      }

      const result = normalizeEvent(input)

      expect(result.data.message).toBe('Timeout')
      expect(result.data.code).toBe('TIMEOUT')
    })

    it('handles detail field (FastAPI style)', () => {
      const input = {
        type: 'error',
        run_id: 'run-3',
        data: { detail: 'Not authenticated' },
      }

      const result = normalizeEvent(input)

      expect(result.data.message).toBe('Not authenticated')
    })
  })

  describe('Run ID Extraction', () => {
    it('extracts run_id from root level', () => {
      const input = { type: 'phase', run_id: 'run-root', data: {} }
      expect(normalizeEvent(input).run_id).toBe('run-root')
    })

    it('extracts runId (camelCase) from root level', () => {
      const input = { type: 'phase', runId: 'run-camel', data: {} }
      expect(normalizeEvent(input).run_id).toBe('run-camel')
    })

    it('extracts run_id from data', () => {
      const input = { type: 'phase', data: { run_id: 'run-data' } }
      expect(normalizeEvent(input).run_id).toBe('run-data')
    })

    it('extracts runId from data', () => {
      const input = { type: 'phase', data: { runId: 'run-data-camel' } }
      expect(normalizeEvent(input).run_id).toBe('run-data-camel')
    })

    it('extracts run_id from payload', () => {
      const input = { type: 'phase', payload: { run_id: 'run-payload' } }
      expect(normalizeEvent(input).run_id).toBe('run-payload')
    })

    it('returns null when no run_id found', () => {
      const input = { type: 'phase', data: { phase: 'execute' } }
      expect(normalizeEvent(input).run_id).toBeNull()
    })
  })

  describe('Conversation ID Extraction', () => {
    it('extracts conversation_id from root level', () => {
      const input = { type: 'conversation_created', conversation_id: 'conv-1', data: {} }
      expect(normalizeEvent(input).conversation_id).toBe('conv-1')
    })

    it('extracts conversationId (camelCase) from data', () => {
      const input = { type: 'phase', data: { conversationId: 'conv-camel' } }
      expect(normalizeEvent(input).conversation_id).toBe('conv-camel')
    })

    it('extracts id from conversation_created data', () => {
      const input = { type: 'conversation_created', data: { id: 'conv-from-id' } }
      const result = normalizeEvent(input)
      expect(result.conversation_id).toBe('conv-from-id')
      expect(result.data.conversation_id).toBe('conv-from-id')
    })
  })

  describe('Timestamp Handling', () => {
    it('preserves valid ISO timestamp', () => {
      const input = {
        type: 'phase',
        timestamp: '2026-01-28T12:00:00.000Z',
        data: {},
      }

      const result = normalizeEvent(input)

      expect(result.timestamp).toBe('2026-01-28T12:00:00.000Z')
    })

    it('converts numeric timestamp', () => {
      const ts = Date.now()
      const input = { type: 'phase', timestamp: ts, data: {} }

      const result = normalizeEvent(input)

      expect(result.timestamp).toBe(new Date(ts).toISOString())
    })

    it('generates timestamp when missing', () => {
      const before = Date.now()
      const input = { type: 'phase', data: {} }

      const result = normalizeEvent(input)

      const resultTs = new Date(result.timestamp).getTime()
      expect(resultTs).toBeGreaterThanOrEqual(before)
      expect(resultTs).toBeLessThanOrEqual(Date.now())
    })

    it('handles time alias', () => {
      const input = { type: 'phase', time: '2026-01-28T15:00:00Z', data: {} }
      expect(normalizeEvent(input).timestamp).toBe('2026-01-28T15:00:00Z')
    })

    it('handles ts alias', () => {
      const input = { type: 'phase', ts: '2026-01-28T16:00:00Z', data: {} }
      expect(normalizeEvent(input).timestamp).toBe('2026-01-28T16:00:00Z')
    })
  })

  describe('Unsupported Types', () => {
    it('returns null for models event', () => {
      const input = { type: 'models', data: { models: [] } }
      expect(normalizeEvent(input)).toBeNull()
    })

    it('returns null for ping event', () => {
      const input = { type: 'ping' }
      expect(normalizeEvent(input)).toBeNull()
    })

    it('returns null for unknown custom type', () => {
      const input = { type: 'custom_unknown', data: {} }
      expect(normalizeEvent(input)).toBeNull()
    })

    it('returns null for empty object', () => {
      expect(normalizeEvent({})).toBeNull()
    })

    it('returns null for null input', () => {
      expect(normalizeEvent(null)).toBeNull()
    })

    it('returns null for undefined input', () => {
      expect(normalizeEvent(undefined)).toBeNull()
    })
  })

  describe('Verification Item Normalization', () => {
    it('normalizes passed: true to status: passed', () => {
      const input = {
        type: 'verification_item',
        run_id: 'run-1',
        data: { name: 'test', passed: true },
      }

      const result = normalizeEvent(input)

      expect(result.data.status).toBe('passed')
    })

    it('normalizes passed: false to status: failed', () => {
      const input = {
        type: 'verification_item',
        run_id: 'run-1',
        data: { name: 'test', passed: false },
      }

      const result = normalizeEvent(input)

      expect(result.data.status).toBe('failed')
    })

    it('uses explicit status over passed boolean', () => {
      const input = {
        type: 'verification_item',
        run_id: 'run-1',
        data: { name: 'test', status: 'running', passed: true },
      }

      const result = normalizeEvent(input)

      expect(result.data.status).toBe('running')
    })

    it('extracts check_name from various fields', () => {
      expect(normalizeEvent({ type: 'verification_item', data: { check_name: 'a' } }).data.check_name).toBe('a')
      expect(normalizeEvent({ type: 'verification_item', data: { name: 'b' } }).data.check_name).toBe('b')
      expect(normalizeEvent({ type: 'verification_item', data: { check: 'c' } }).data.check_name).toBe('c')
    })
  })

  describe('Tool Normalization', () => {
    it('extracts tool name from various fields', () => {
      expect(normalizeEvent({ type: 'tool', data: { tool: 'cmd1' } }).data.tool).toBe('cmd1')
      expect(normalizeEvent({ type: 'tool', data: { name: 'cmd2' } }).data.tool).toBe('cmd2')
      expect(normalizeEvent({ type: 'tool', data: { tool_name: 'cmd3' } }).data.tool).toBe('cmd3')
    })

    it('extracts params from various fields', () => {
      expect(normalizeEvent({ type: 'tool', data: { params: { a: 1 } } }).data.params).toEqual({ a: 1 })
      expect(normalizeEvent({ type: 'tool', data: { input: { b: 2 } } }).data.params).toEqual({ b: 2 })
      expect(normalizeEvent({ type: 'tool', data: { arguments: { c: 3 } } }).data.params).toEqual({ c: 3 })
    })
  })

  describe('Complete Event Normalization', () => {
    it('extracts response from various fields', () => {
      expect(normalizeEvent({ type: 'complete', data: { response: 'r1' } }).data.response).toBe('r1')
      expect(normalizeEvent({ type: 'complete', data: { content: 'r2' } }).data.response).toBe('r2')
      expect(normalizeEvent({ type: 'complete', data: { result: 'r3' } }).data.response).toBe('r3')
    })

    it('preserves verdict and verification', () => {
      const input = {
        type: 'complete',
        data: {
          verdict: { status: 'PASS', confidence: 0.95 },
          verification: { checks: [] },
        },
      }

      const result = normalizeEvent(input)

      expect(result.data.verdict.status).toBe('PASS')
      expect(result.data.verification.checks).toEqual([])
    })

    it('normalizes tools_used from camelCase', () => {
      const input = { type: 'complete', data: { toolsUsed: ['a', 'b'] } }
      expect(normalizeEvent(input).data.tools_used).toEqual(['a', 'b'])
    })
  })

  describe('Event Type Alias Handling', () => {
    it('accepts event field as type alias', () => {
      const input = { event: 'phase', data: { phase: 'spec' } }
      expect(normalizeEvent(input).type).toBe('phase')
    })

    it('accepts action field as type alias', () => {
      const input = { action: 'tool', data: { tool: 'test' } }
      expect(normalizeEvent(input).type).toBe('tool')
    })
  })

  describe('Data/Payload Alias', () => {
    it('uses data field', () => {
      const input = { type: 'phase', data: { phase: 'plan' } }
      expect(normalizeEvent(input).data.phase).toBe('plan')
    })

    it('falls back to payload field', () => {
      const input = { type: 'phase', payload: { phase: 'execute' } }
      expect(normalizeEvent(input).data.phase).toBe('execute')
    })
  })
})

describe('isTerminalEvent', () => {
  it('returns true for complete event', () => {
    expect(isTerminalEvent({ type: 'complete' })).toBe(true)
  })

  it('returns true for error event', () => {
    expect(isTerminalEvent({ type: 'error' })).toBe(true)
  })

  it('returns false for phase event', () => {
    expect(isTerminalEvent({ type: 'phase' })).toBe(false)
  })

  it('returns false for thinking event', () => {
    expect(isTerminalEvent({ type: 'thinking' })).toBe(false)
  })

  it('returns false for null', () => {
    expect(isTerminalEvent(null)).toBe(false)
  })
})

describe('requiresRunId', () => {
  it('returns false for conversation_created', () => {
    expect(requiresRunId({ type: 'conversation_created' })).toBe(false)
  })

  it('returns true for phase', () => {
    expect(requiresRunId({ type: 'phase' })).toBe(true)
  })

  it('returns true for tool', () => {
    expect(requiresRunId({ type: 'tool' })).toBe(true)
  })

  it('returns true for complete', () => {
    expect(requiresRunId({ type: 'complete' })).toBe(true)
  })

  it('returns false for null', () => {
    expect(requiresRunId(null)).toBe(false)
  })
})

describe('TERMINAL_TYPES', () => {
  it('contains complete', () => {
    expect(TERMINAL_TYPES.has('complete')).toBe(true)
  })

  it('contains error', () => {
    expect(TERMINAL_TYPES.has('error')).toBe(true)
  })

  it('does not contain phase', () => {
    expect(TERMINAL_TYPES.has('phase')).toBe(false)
  })
})
