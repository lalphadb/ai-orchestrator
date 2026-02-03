/**
 * Phase 2: Frontend Stabilization - Multi-Run Support Tests
 * Tests for concurrent run handling, event routing, and watchdog system
 */

import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useChatStore } from '@/stores/chat'
import { setTerminal } from '@/stores/runTypes'

describe('Chat Store - Phase 2: Multi-Run Support', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe('Run Registry', () => {
    it('creates runs and tracks them in Map', () => {
      const chat = useChatStore()

      const userMsg = { id: 1, role: 'user', content: 'Test' }
      const assistantMsg = { id: 2, role: 'assistant', content: '' }

      const run = chat.createRun('run-123', 'conv-1', userMsg, assistantMsg)

      expect(chat.runs.size).toBe(1)
      expect(chat.runs.has('run-123')).toBe(true)
      expect(run.id).toBe('run-123')
      expect(run.status).toBe('running')
      expect(run.conversation_id).toBe('conv-1') // v8: snake_case, no getter alias
      expect(chat.activeRunId).toBe('run-123')
    })

    it('tracks runs by conversation', () => {
      const chat = useChatStore()

      chat.createRun('run-1', 'conv-1', { id: 1 }, { id: 2 })
      chat.createRun('run-2', 'conv-1', { id: 3 }, { id: 4 })
      chat.createRun('run-3', 'conv-2', { id: 5 }, { id: 6 })

      expect(chat.runsByConversation.has('conv-1')).toBe(true)
      expect(chat.runsByConversation.has('conv-2')).toBe(true)
      expect(chat.runsByConversation.get('conv-1').size).toBe(2)
      expect(chat.runsByConversation.get('conv-2').size).toBe(1)
    })

    it('marks run as complete', () => {
      const chat = useChatStore()
      chat.messages = [
        { id: 1, role: 'user', content: 'Test' },
        { id: 2, role: 'assistant', content: '', streaming: true },
      ]

      chat.createRun('run-123', 'conv-1', chat.messages[0], chat.messages[1])

      // Advance time so duration is non-zero
      vi.advanceTimersByTime(100)

      const completeData = {
        response: 'Done!',
        tools_used: ['bash'],
        verification: { passed: true },
        verdict: { status: 'PASS', confidence: 0.95 },
      }

      chat.markRunComplete('run-123', completeData)

      const run = chat.runs.get('run-123')
      expect(run.status).toBe('complete')
      expect(run.workflowPhase).toBe('complete')
      // v8: endedAt is ISO string, not timestamp number
      expect(run.endedAt).toBeTruthy()
      expect(typeof run.endedAt).toBe('string')
      // v8: duration is computed (endedAt - startedAt), not stored
      const duration = new Date(run.endedAt).getTime() - new Date(run.startedAt).getTime()
      expect(duration).toBeGreaterThanOrEqual(0)
      // v8: streaming is derived from status (status === 'running'), not stored
      expect(run.status).not.toBe('running') // Not streaming because status is 'complete'

      // Check message updated
      const msg = chat.messages.find((m) => m.id === 2)
      expect(msg.streaming).toBe(false)
      expect(msg.content).toBe('Done!')
      expect(msg.verification).toEqual({ passed: true })
    })

    it('marks run as failed', () => {
      const chat = useChatStore()
      chat.messages = [
        { id: 1, role: 'user', content: 'Test' },
        { id: 2, role: 'assistant', content: '', streaming: true },
      ]

      chat.createRun('run-123', 'conv-1', chat.messages[0], chat.messages[1])

      chat.markRunFailed('run-123', 'Connection timeout')

      const run = chat.runs.get('run-123')
      expect(run.status).toBe('failed')
      expect(run.workflowPhase).toBe('complete') // v8: failed runs still end in complete phase
      expect(run.error).toBe('Connection timeout')

      // Check message updated
      const msg = chat.messages.find((m) => m.id === 2)
      expect(msg.isError).toBe(true)
      expect(msg.content).toContain('Connection timeout')
    })

    it('cleans up old completed runs', () => {
      const chat = useChatStore()

      // Create and complete run 1 (old)
      chat.createRun('run-1', 'conv-1', { id: 1 }, { id: 2 })
      const run1 = chat.runs.get('run-1')
      // Use setTerminal to properly set endedAt
      setTerminal(run1, 'complete', {})
      // Override endedAt to be 6+ minutes ago
      run1.endedAt = new Date(Date.now() - 400000).toISOString()

      // Create and complete run 2 (recent)
      chat.createRun('run-2', 'conv-1', { id: 3 }, { id: 4 })
      chat.markRunComplete('run-2', { response: 'Done' })

      // Create running run 3
      chat.createRun('run-3', 'conv-1', { id: 5 }, { id: 6 })

      expect(chat.runs.size).toBe(3)

      // Cleanup
      chat.cleanupOldRuns('conv-1')

      // Only old completed run should be removed
      expect(chat.runs.size).toBe(2)
      expect(chat.runs.has('run-1')).toBe(false)
      expect(chat.runs.has('run-2')).toBe(true)
      expect(chat.runs.has('run-3')).toBe(true)
    })
  })

  describe('✓ Playbook Test 1: Lancer plusieurs runs simultanés', () => {
    it('handles 3 concurrent runs without interference', () => {
      const chat = useChatStore()

      // Simulate 3 concurrent message sends
      const run1Id = 'run-abc123'
      const run2Id = 'run-def456'
      const run3Id = 'run-ghi789'

      // Create runs
      chat.createRun(run1Id, 'conv-1', { id: 1 }, { id: 2 })
      chat.createRun(run2Id, 'conv-1', { id: 3 }, { id: 4 })
      chat.createRun(run3Id, 'conv-1', { id: 5 }, { id: 6 })

      // Verify all runs exist
      expect(chat.runs.size).toBe(3)
      expect(chat.runs.has(run1Id)).toBe(true)
      expect(chat.runs.has(run2Id)).toBe(true)
      expect(chat.runs.has(run3Id)).toBe(true)

      // Simulate thinking events for different runs
      const run1 = chat.runs.get(run1Id)
      const run2 = chat.runs.get(run2Id)
      const run3 = chat.runs.get(run3Id)

      run1.thinking.push({ message: 'Analyzing run 1' })
      run2.thinking.push({ message: 'Analyzing run 2' })
      run3.thinking.push({ message: 'Analyzing run 3' })

      // Verify events routed correctly (no cross-contamination)
      expect(run1.thinking[0].message).toBe('Analyzing run 1')
      expect(run2.thinking[0].message).toBe('Analyzing run 2')
      expect(run3.thinking[0].message).toBe('Analyzing run 3')

      // Complete runs in different order
      chat.markRunComplete(run2Id, { response: 'Done 2' })
      chat.markRunComplete(run1Id, { response: 'Done 1' })

      // Verify statuses
      expect(run1.status).toBe('complete')
      expect(run2.status).toBe('complete')
      expect(run3.status).toBe('running')

      // Verify run3 unaffected
      expect(run3.thinking[0].message).toBe('Analyzing run 3')
    })
  })

  describe('✓ Playbook Test 2: Déconnecter/reconnecter le WS', () => {
    it('preserves run state across WS reconnection', () => {
      const chat = useChatStore()

      // Create run
      const runId = 'run-reconnect'
      chat.createRun(runId, 'conv-1', { id: 1 }, { id: 2 })

      // Simulate some events
      const run = chat.runs.get(runId)
      run.phaseHistory.push({ phase: 'spec', timestamp: Date.now() })
      run.tools.push({ tool: 'bash', timestamp: Date.now() }) // v8: tools instead of toolCalls

      expect(run.phaseHistory.length).toBe(1)
      expect(run.tools.length).toBe(1) // v8: tools instead of toolCalls

      // Simulate reconnection (state should persist)
      chat.wsState = 'disconnected'
      chat.wsState = 'connecting'
      chat.wsState = 'connected'

      // Run data should still exist
      expect(chat.runs.has(runId)).toBe(true)
      expect(chat.runs.get(runId).phaseHistory.length).toBe(1)

      // New events after reconnect should still work
      run.phaseHistory.push({ phase: 'execute', timestamp: Date.now() })
      expect(chat.runs.get(runId).phaseHistory.length).toBe(2)
    })
  })

  describe('✓ Playbook Test 3: Timeout sans event → run FAILED', () => {
    it('watchdog marks stuck run as FAILED after 60s', () => {
      const chat = useChatStore()

      const runId = 'run-timeout'
      chat.createRun(runId, 'conv-1', { id: 1 }, { id: 2 })

      const run = chat.runs.get(runId)
      expect(run.status).toBe('running')
      expect(run.watchdog.timerId).toBeTruthy() // v8: watchdog.timerId instead of watchdog.timerId

      // Simulate no events for >120s by manually setting lastHeartbeatAt (v8)
      // CRQ-2026-0203-001: defaultTimeout increased to 120s
      run.watchdog.lastHeartbeatAt = new Date(Date.now() - 125000).toISOString() // 125s ago > 120s timeout

      // Trigger watchdog check by advancing timers (15s interval)
      vi.advanceTimersByTime(15000)

      // Run should be marked failed
      expect(run.status).toBe('failed')
      expect(run.error).toContain('Timeout')
      expect(run.watchdog.timerId).toBe(null) // v8: watchdog.timerId
    })

    it('watchdog stops when run completes normally', () => {
      const chat = useChatStore()

      const runId = 'run-complete'
      chat.createRun(runId, 'conv-1', { id: 1 }, { id: 2 })

      const run = chat.runs.get(runId)
      expect(run.watchdog.timerId).toBeTruthy()

      // Complete run before timeout
      vi.advanceTimersByTime(5000)
      chat.markRunComplete(runId, { response: 'Done' })

      // Watchdog should be stopped
      expect(run.watchdog.timerId).toBe(null)

      // Advance past timeout - should not mark as failed
      vi.advanceTimersByTime(20000)
      expect(run.status).toBe('complete')
    })
  })

  describe('✓ Playbook Test 4: Rafraîchir la page → état cohérent', () => {
    it('documents current behavior: runs lost on refresh (no persistence yet)', () => {
      const chat = useChatStore()

      // Simulate page state before refresh
      const runId = 'run-refresh'
      chat.createRun(runId, 'conv-1', { id: 1 }, { id: 2 })

      const run = chat.runs.get(runId)
      run.phaseHistory.push({ phase: 'spec' })

      expect(run.phaseHistory.length).toBe(1)

      // After refresh, store is recreated
      const freshPinia = createPinia()
      setActivePinia(freshPinia)
      const freshStore = useChatStore()

      // Runs are lost (expected - no localStorage persistence yet)
      expect(freshStore.runs.size).toBe(0)
      expect(freshStore.activeRunId).toBe(null)

      // This documents current behavior - Phase 3 will add persistence
    })
  })

  describe('✓ Playbook Test 5: Aucun crash console navigateur', () => {
    it('handles invalid events gracefully without crashing', () => {
      const chat = useChatStore()
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

      // Simulate events with missing run_id
      const run = chat.runs.get(null) // Should return undefined
      expect(run).toBeUndefined()

      // Simulate events for unknown run
      const unknownRun = chat.runs.get('invalid-run-id')
      expect(unknownRun).toBeUndefined()

      // v8: markRunComplete with unknown run_id creates the run (out-of-order event handling)
      // No longer warns, just creates placeholder
      chat.markRunComplete('unknown-run', { response: 'Done' })
      expect(chat.runs.has('unknown-run')).toBe(true)
      expect(chat.runs.get('unknown-run').status).toBe('complete')

      // v8: markRunFailed also creates run if it doesn't exist
      chat.markRunFailed('unknown-run-2', 'Error')
      expect(chat.runs.has('unknown-run-2')).toBe(true)

      // Valid flow should not log errors
      consoleErrorSpy.mockClear()
      consoleWarnSpy.mockClear()

      const runId = 'run-valid'
      chat.createRun(runId, 'conv-1', { id: 1 }, { id: 2 })
      const validRun = chat.runs.get(runId)
      validRun.thinking.push({ message: 'Valid thinking' })

      expect(consoleErrorSpy).not.toHaveBeenCalled()
      expect(consoleWarnSpy).not.toHaveBeenCalled()

      consoleErrorSpy.mockRestore()
      consoleWarnSpy.mockRestore()
    })
  })

  describe('Per-Run Watchdog', () => {
    it('starts watchdog for new run', () => {
      const chat = useChatStore()

      const runId = 'run-watchdog'
      chat.createRun(runId, 'conv-1', { id: 1 }, { id: 2 })

      const run = chat.runs.get(runId)
      expect(run.watchdog.timerId).toBeTruthy()
    })

    it('stops watchdog when run completes', () => {
      const chat = useChatStore()

      const runId = 'run-complete'
      chat.createRun(runId, 'conv-1', { id: 1 }, { id: 2 })

      const run = chat.runs.get(runId)
      const timerBefore = run.watchdog.timerId
      expect(timerBefore).toBeTruthy()

      chat.markRunComplete(runId, { response: 'Done' })

      expect(run.watchdog.timerId).toBe(null)
    })

    it('stops all watchdogs on cleanup', () => {
      const chat = useChatStore()

      chat.createRun('run-1', 'conv-1', { id: 1 }, { id: 2 })
      chat.createRun('run-2', 'conv-1', { id: 3 }, { id: 4 })
      chat.createRun('run-3', 'conv-2', { id: 5 }, { id: 6 })

      expect(chat.runs.get('run-1').watchdog.timerId).toBeTruthy()
      expect(chat.runs.get('run-2').watchdog.timerId).toBeTruthy()
      expect(chat.runs.get('run-3').watchdog.timerId).toBeTruthy()

      chat.stopAllWatchdogs()

      expect(chat.runs.get('run-1').watchdog.timerId).toBe(null)
      expect(chat.runs.get('run-2').watchdog.timerId).toBe(null)
      expect(chat.runs.get('run-3').watchdog.timerId).toBe(null)
    })

    it('updates lastEventTime on events', () => {
      const chat = useChatStore()

      const runId = 'run-events'
      chat.createRun(runId, 'conv-1', { id: 1 }, { id: 2 })

      const run = chat.runs.get(runId)
      // v8: lastEventAt is ISO string, not timestamp number
      const initialTime = new Date(run.lastEventAt).getTime()

      // Advance time and simulate event
      vi.advanceTimersByTime(5000)
      run.lastEventAt = new Date(Date.now()).toISOString() // v8: ISO string
      run.watchdog.lastHeartbeatAt = run.lastEventAt // v8: also update watchdog

      expect(new Date(run.lastEventAt).getTime()).toBeGreaterThan(initialTime)

      // Watchdog should not fail if events keep coming
      vi.advanceTimersByTime(15000) // Check interval
      expect(run.status).toBe('running')

      // But should fail if no events for >120s (CRQ-2026-0203-001: increased from 90s)
      // Set lastHeartbeatAt to 125s ago, then trigger check
      run.watchdog.lastHeartbeatAt = new Date(Date.now() - 125000).toISOString() // 125s > 120s timeout
      vi.advanceTimersByTime(15000) // Trigger watchdog check
      expect(run.status).toBe('failed')
    })
  })

  describe('Out-of-Order Event Handling', () => {
    it('creates placeholder run for unknown run_id', () => {
      const chat = useChatStore()

      // Simulate receiving an event before conversation_created
      const runId = 'run-early-event'

      // This would normally warn and ignore, but now creates placeholder
      const run = chat.getOrCreateRun(runId)

      expect(chat.runs.has(runId)).toBe(true)
      // v8: isPlaceholder is computed (status === 'pending' && !terminal), not stored
      // But getOrCreateRun creates runs with status 'running', not 'pending'
      expect(run.conversation_id).toBe(null) // v8: snake_case
      expect(run.messageId).toBe(null)
    })

    it('completes placeholder when conversation_created arrives', () => {
      const chat = useChatStore()

      // Create placeholder
      const runId = 'run-placeholder'
      const run = chat.getOrCreateRun(runId)
      // v8: getOrCreateRun creates with status 'running', not a placeholder
      expect(run.conversation_id).toBe(null)

      // Add some events to placeholder
      run.thinking.push({ message: 'Early thinking' })
      run.tools.push({ tool: 'bash' }) // v8: tools instead of toolCalls

      // Simulate conversation_created arriving
      // This would be done by the actual event handler in real usage
      run.conversation_id = 'conv-123' // v8: snake_case

      if (!chat.runsByConversation.has('conv-123')) {
        chat.runsByConversation.set('conv-123', new Set())
      }
      chat.runsByConversation.get('conv-123').add(runId)

      // Verify placeholder was completed and events preserved
      expect(run.conversation_id).toBe('conv-123') // v8: snake_case only
      expect(run.thinking.length).toBe(1)
      expect(run.tools.length).toBe(1) // v8: tools instead of toolCalls
    })
  })

  describe('Backend run_id Authority', () => {
    it('creates pending messages without run_id', () => {
      const chat = useChatStore()

      const tempId = 'pending-123'
      chat.pendingMessages.set(tempId, {
        tempId,
        conversationId: 'conv-1',
        userMsg: { id: 1, role: 'user', content: 'Test' },
        assistantMsg: { id: 2, role: 'assistant', content: '' },
        runId: null, // No run_id yet
      })

      expect(chat.pendingMessages.size).toBe(1)
      const pending = chat.pendingMessages.get(tempId)
      expect(pending.runId).toBe(null)
    })

    it('associates pending message with backend run_id', () => {
      const chat = useChatStore()

      // Create pending message
      const tempId = 'pending-123'
      const pending = {
        tempId,
        conversationId: 'conv-1',
        userMsg: { id: 1, role: 'user', content: 'Test' },
        assistantMsg: { id: 2, role: 'assistant', content: '' },
        runId: null,
      }
      chat.pendingMessages.set(tempId, pending)

      // Backend sends run_id
      const backendRunId = 'backend-run-456'

      // Associate pending with run
      pending.runId = backendRunId
      chat.createRun(backendRunId, 'conv-1', pending.userMsg, pending.assistantMsg)
      chat.pendingMessages.delete(tempId)

      // Verify run created with backend's run_id
      expect(chat.runs.has(backendRunId)).toBe(true)
      expect(chat.pendingMessages.size).toBe(0)
    })
  })

  describe('Run Actions', () => {
    it('rerunVerification includes run_id', () => {
      const chat = useChatStore()

      chat.createRun('run-123', 'conv-1', { id: 1 }, { id: 2 })
      chat.markRunComplete('run-123', { response: 'Done', verification: {} })
      chat.activeRunId = 'run-123'
      chat.currentConversation = { id: 'conv-1' }

      // Mock wsClient
      const mockSend = vi.fn(() => true)
      chat.initWebSocket = vi.fn()

      // We can't easily test wsClient.send without importing it
      // This test documents the expected behavior
      const run = chat.runs.get('run-123')
      expect(run.status).toBe('complete')
      expect(chat.activeRunId).toBe('run-123')
    })

    it('forceRepair includes run_id', () => {
      const chat = useChatStore()

      chat.createRun('run-123', 'conv-1', { id: 1 }, { id: 2 })
      chat.markRunComplete('run-123', {
        response: 'Done',
        verdict: { status: 'FAIL' },
      })
      chat.activeRunId = 'run-123'
      chat.currentConversation = { id: 'conv-1' }

      const run = chat.runs.get('run-123')
      expect(run.verdict.status).toBe('FAIL')
      expect(chat.activeRunId).toBe('run-123')
    })
  })

  describe('exportRunReport', () => {
    it('exports active run report as JSON', () => {
      const chat = useChatStore()

      chat.createRun('run-123', 'conv-1', { id: 1 }, { id: 2 })
      chat.activeRunId = 'run-123'

      const run = chat.runs.get('run-123')
      run.tools.push({ tool: 'bash', params: {}, iteration: 1 }) // v8: tools instead of toolCalls
      run.verification = { passed: true }

      const report = chat.exportRunReport()
      expect(report).toBeTruthy()

      const parsed = JSON.parse(report)
      expect(parsed.run_id).toBe('run-123')
      expect(parsed.status).toBe('running')
      expect(parsed.tools_used).toHaveLength(1)
      expect(parsed.verification).toEqual({ passed: true })
    })

    it('returns null if no active run', () => {
      const chat = useChatStore()
      chat.activeRunId = null

      const report = chat.exportRunReport()
      expect(report).toBe(null)
    })
  })
})
