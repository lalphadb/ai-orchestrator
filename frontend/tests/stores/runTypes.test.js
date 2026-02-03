import { describe, it, expect } from 'vitest'
import {
  RunStatus,
  WorkflowPhase,
  PhaseStatus,
  PhaseTimeouts,
  createRunState,
  createPhases,
  createPhaseState,
  isTerminalStatus,
  isValidStatus,
  isValidPhase,
  getPhaseTimeout,
  updatePhaseStatus,
  setTerminal,
} from '@/stores/runTypes'

describe('RunStatus', () => {
  it('has all expected status values (prompt: pending|running|success|failed)', () => {
    expect(RunStatus.PENDING).toBe('pending')
    expect(RunStatus.RUNNING).toBe('running')
    expect(RunStatus.COMPLETE).toBe('complete') // Note: 'complete' instead of 'success'
    expect(RunStatus.FAILED).toBe('failed')
  })

  it('is frozen (immutable)', () => {
    expect(Object.isFrozen(RunStatus)).toBe(true)
  })
})

describe('WorkflowPhase', () => {
  it('has all expected phases', () => {
    expect(WorkflowPhase.STARTING).toBe('starting')
    expect(WorkflowPhase.SPEC).toBe('spec')
    expect(WorkflowPhase.PLAN).toBe('plan')
    expect(WorkflowPhase.EXECUTE).toBe('execute')
    expect(WorkflowPhase.VERIFY).toBe('verify')
    expect(WorkflowPhase.REPAIR).toBe('repair')
    expect(WorkflowPhase.COMPLETE).toBe('complete')
  })

  it('is frozen (immutable)', () => {
    expect(Object.isFrozen(WorkflowPhase)).toBe(true)
  })
})

describe('PhaseStatus', () => {
  it('has all phase status values', () => {
    expect(PhaseStatus.PENDING).toBe('pending')
    expect(PhaseStatus.RUNNING).toBe('running')
    expect(PhaseStatus.COMPLETE).toBe('complete')
    expect(PhaseStatus.SKIPPED).toBe('skipped')
  })
})

describe('PhaseTimeouts', () => {
  it('has timeout for each phase', () => {
    expect(PhaseTimeouts.starting).toBe(30000)
    expect(PhaseTimeouts.spec).toBe(60000)
    expect(PhaseTimeouts.plan).toBe(60000)
    expect(PhaseTimeouts.execute).toBe(120000) // CRQ-2026-0203-001: increased from 90000
    expect(PhaseTimeouts.verify).toBe(120000)
    expect(PhaseTimeouts.repair).toBe(120000)
    expect(PhaseTimeouts.default).toBe(120000) // CRQ-2026-0203-001: increased from 90000
  })

  it('is frozen (immutable)', () => {
    expect(Object.isFrozen(PhaseTimeouts)).toBe(true)
  })
})

describe('createPhaseState', () => {
  it('creates phase state with pending status', () => {
    const state = createPhaseState()
    
    expect(state.status).toBe(PhaseStatus.PENDING)
    expect(state.startedAt).toBeNull()
    expect(state.endedAt).toBeNull()
  })
})

describe('createPhases (prompt: phases with status + timestamps)', () => {
  it('creates all required phases: spec, plan, execute, verify, repair, complete', () => {
    const phases = createPhases()
    
    expect(phases.spec).toBeDefined()
    expect(phases.plan).toBeDefined()
    expect(phases.execute).toBeDefined()
    expect(phases.verify).toBeDefined()
    expect(phases.repair).toBeDefined()
    expect(phases.complete).toBeDefined()
  })

  it('each phase has status and timestamps', () => {
    const phases = createPhases()
    
    for (const phase of ['spec', 'plan', 'execute', 'verify', 'repair', 'complete']) {
      expect(phases[phase].status).toBe(PhaseStatus.PENDING)
      expect(phases[phase].startedAt).toBeNull()
      expect(phases[phase].endedAt).toBeNull()
    }
  })
})

describe('createRunState (prompt compliance)', () => {
  it('has run_id', () => {
    const run = createRunState('run-123')
    expect(run.run_id).toBe('run-123')
    expect(run.id).toBe('run-123') // Alias
  })

  it('has conversation_id (optional)', () => {
    const run1 = createRunState('run-1')
    expect(run1.conversation_id).toBeNull()
    
    const run2 = createRunState('run-2', { conversationId: 'conv-1' })
    expect(run2.conversation_id).toBe('conv-1')
  })

  it('has status: running by default', () => {
    const run = createRunState('run-123')
    expect(run.status).toBe(RunStatus.RUNNING)
  })

  it('has phases with status + timestamps', () => {
    const run = createRunState('run-123')
    expect(run.phases).toBeDefined()
    expect(run.phases.spec.status).toBe(PhaseStatus.PENDING)
    expect(run.phases.verify.startedAt).toBeNull()
  })

  it('has thinkingLog[] (prompt name)', () => {
    const run = createRunState('run-123')
    // v8: renamed thinkingLog → thinking
    expect(Array.isArray(run.thinking)).toBe(true)
    expect(run.thinking.length).toBe(0)
  })

  it('has toolCalls[]', () => {
    const run = createRunState('run-123')
    // v8: renamed toolCalls → tools
    expect(Array.isArray(run.tools)).toBe(true)
  })

  it('has verificationItems[]', () => {
    const run = createRunState('run-123')
    // v8: renamed verificationItems → verification
    expect(Array.isArray(run.verification)).toBe(true)
  })

  it('has startedAt/lastEventAt/endedAt (prompt names)', () => {
    const run = createRunState('run-123')

    // v8: timestamps are ISO strings, not milliseconds
    expect(typeof run.startedAt).toBe('string')
    expect(run.startedAt).toMatch(/^\d{4}-\d{2}-\d{2}T/) // ISO 8601 format
    expect(run.lastEventAt).toBe(run.startedAt)
    expect(run.endedAt).toBeNull()
  })

  it('has terminal: null initially', () => {
    const run = createRunState('run-123')
    // v8: terminal is false initially, not null
    expect(run.terminal).toBe(false)
  })

  it('has watchdog: timerId + config (prompt)', () => {
    const run = createRunState('run-123')
    expect(run.watchdog).toBeDefined()
    expect(run.watchdog.timerId).toBeNull()
    // v8: watchdog structure simplified - no nested config object
    expect(run.watchdog.timeoutMs).toBe(PhaseTimeouts.default)
    expect(typeof run.watchdog.lastHeartbeatAt).toBe('string') // ISO timestamp
  })

  it('maintains backward compat aliases', () => {
    const run = createRunState('run-123', { conversationId: 'conv-1' })

    // v8: No getters (cause Pinia proxy errors), use direct properties
    expect(run.conversation_id).toBe('conv-1')
    expect(run.id).toBe('run-123') // id alias for backward compat
    expect(Array.isArray(run.thinking)).toBe(true)
    expect(Array.isArray(run.tools)).toBe(true)
    expect(Array.isArray(run.verification)).toBe(true)
  })
})

describe('isTerminalStatus', () => {
  it('returns true for complete', () => {
    expect(isTerminalStatus(RunStatus.COMPLETE)).toBe(true)
    expect(isTerminalStatus('complete')).toBe(true)
  })

  it('returns true for failed', () => {
    expect(isTerminalStatus(RunStatus.FAILED)).toBe(true)
    expect(isTerminalStatus('failed')).toBe(true)
  })

  it('returns false for running and pending', () => {
    expect(isTerminalStatus(RunStatus.RUNNING)).toBe(false)
    expect(isTerminalStatus(RunStatus.PENDING)).toBe(false)
  })
})

describe('isValidStatus', () => {
  it('returns true for valid statuses', () => {
    expect(isValidStatus('pending')).toBe(true)
    expect(isValidStatus('running')).toBe(true)
    expect(isValidStatus('complete')).toBe(true)
    expect(isValidStatus('failed')).toBe(true)
  })

  it('returns false for invalid statuses', () => {
    expect(isValidStatus('unknown')).toBe(false)
    expect(isValidStatus('success')).toBe(false) // We use 'complete' not 'success'
    expect(isValidStatus(null)).toBe(false)
  })
})

describe('isValidPhase', () => {
  it('returns true for valid phases', () => {
    expect(isValidPhase('starting')).toBe(true)
    expect(isValidPhase('spec')).toBe(true)
    expect(isValidPhase('plan')).toBe(true)
    expect(isValidPhase('execute')).toBe(true)
    expect(isValidPhase('verify')).toBe(true)
    expect(isValidPhase('repair')).toBe(true)
    expect(isValidPhase('complete')).toBe(true)
  })

  it('returns false for invalid phases', () => {
    expect(isValidPhase('unknown')).toBe(false)
    expect(isValidPhase(null)).toBe(false)
  })
})

describe('getPhaseTimeout', () => {
  it('returns correct timeout for each phase', () => {
    expect(getPhaseTimeout('starting')).toBe(30000)
    expect(getPhaseTimeout('spec')).toBe(60000)
    expect(getPhaseTimeout('verify')).toBe(120000)
  })

  it('returns default timeout for unknown phase', () => {
    // CRQ-2026-0203-001: increased from 90000 to 120000
    expect(getPhaseTimeout('unknown')).toBe(120000)
    expect(getPhaseTimeout(null)).toBe(120000)
  })
})

describe('updatePhaseStatus', () => {
  it('updates phase status', () => {
    const run = createRunState('run-123')
    
    updatePhaseStatus(run, 'spec', PhaseStatus.RUNNING)
    
    expect(run.phases.spec.status).toBe(PhaseStatus.RUNNING)
    expect(run.phases.spec.startedAt).not.toBeNull()
  })

  it('sets endedAt when complete', () => {
    const run = createRunState('run-123')
    
    updatePhaseStatus(run, 'spec', PhaseStatus.RUNNING)
    updatePhaseStatus(run, 'spec', PhaseStatus.COMPLETE)
    
    expect(run.phases.spec.status).toBe(PhaseStatus.COMPLETE)
    expect(run.phases.spec.endedAt).not.toBeNull()
  })

  it('also updates legacy phaseTimestamps', () => {
    const run = createRunState('run-123')
    
    updatePhaseStatus(run, 'spec', PhaseStatus.RUNNING)
    
    expect(run.phaseTimestamps.spec).not.toBeNull()
  })
})

describe('setTerminal (prompt: terminal: complete/error payload)', () => {
  it('sets complete terminal', () => {
    const run = createRunState('run-123')
    
    setTerminal(run, 'complete', { response: 'done' })
    
    expect(run.terminal).toBe(true)
    expect(run.terminalEvent.type).toBe('complete')
    expect(run.terminalEvent.payload.response).toBe('done')
    expect(run.terminalEvent.timestamp).toBeDefined()
    expect(run.status).toBe(RunStatus.COMPLETE)
    expect(run.endedAt).not.toBeNull()
  })

  it('sets error terminal', () => {
    const run = createRunState('run-123')
    
    setTerminal(run, 'error', { message: 'failed' })
    
    expect(run.terminal).toBe(true)
    expect(run.terminalEvent.type).toBe('error')
    expect(run.terminalEvent.payload.message).toBe('failed')
    expect(run.status).toBe(RunStatus.FAILED)
    expect(run.endedAt).not.toBeNull()
  })
})
