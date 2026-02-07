import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useChatStore } from '@/stores/chat'
import { wsClient } from '@/services/wsClient'

describe('Chat Store - WS normalized event routing', () => {
  let originalConnect

  beforeEach(() => {
    setActivePinia(createPinia())
    originalConnect = wsClient.connect
    wsClient.connect = vi.fn()
    wsClient.listeners = new Map()
    wsClient._listenersInitialized = false
  })

  afterEach(() => {
    wsClient.connect = originalConnect
    wsClient.listeners = new Map()
    wsClient._listenersInitialized = false
  })

  it('routes event without run_id using conversation_id when unambiguous', () => {
    const chat = useChatStore()
    chat.createRun('run-1', 'conv-1', { id: 1 }, { id: 2 })

    chat.initWebSocket()

    wsClient.emit('event', {
      type: 'phase',
      timestamp: new Date().toISOString(),
      run_id: null,
      data: { phase: 'spec', status: 'starting', conversation_id: 'conv-1' },
    })

    const run = chat.runs.get('run-1')
    expect(run.workflowPhase).toBe('spec')
    // V8: updatePhaseStatus may add multiple entries (starting + spec)
    expect(run.phaseHistory.length).toBeGreaterThanOrEqual(1)
  })

  it('ignores event without run_id when routing is ambiguous', () => {
    const chat = useChatStore()
    chat.createRun('run-1', 'conv-1', { id: 1 }, { id: 2 })
    chat.createRun('run-2', 'conv-1', { id: 3 }, { id: 4 })

    chat.initWebSocket()

    wsClient.emit('event', {
      type: 'phase',
      timestamp: new Date().toISOString(),
      run_id: null,
      data: { phase: 'spec', status: 'starting', conversation_id: 'conv-1' },
    })

    expect(chat.runs.get('run-1').phaseHistory.length).toBe(0)
    expect(chat.runs.get('run-2').phaseHistory.length).toBe(0)
  })

  it('streams token chunks to the latest streaming message when run_id is missing', () => {
    const chat = useChatStore()
    chat.messages = [
      { id: 1, role: 'user', content: 'Hi' },
      { id: 2, role: 'assistant', content: '', streaming: true },
    ]

    chat.initWebSocket()

    wsClient.emit('event', {
      type: 'thinking',
      timestamp: new Date().toISOString(),
      run_id: null,
      data: { kind: 'token', content: 'Hello' },
    })

    expect(chat.messages[1].content).toBe('Hello')
  })

  it('binds pending messages to a run when terminal arrives', () => {
    const chat = useChatStore()

    const userMsg = { id: 10, role: 'user', content: 'Test' }
    const assistantMsg = { id: 11, role: 'assistant', content: '', streaming: true }
    chat.messages = [userMsg, assistantMsg]

    chat.pendingMessages.set('pending-1', {
      tempId: 'pending-1',
      conversationId: 'conv-1',
      userMsg,
      assistantMsg,
      runId: null,
    })

    chat.initWebSocket()

    wsClient.emit('event', {
      type: 'complete',
      timestamp: new Date().toISOString(),
      run_id: 'run-xyz',
      data: { response: 'Done', conversation_id: 'conv-1' },
    })

    const run = chat.runs.get('run-xyz')
    expect(run).toBeTruthy()
    expect(run.status).toBe('complete')
    expect(chat.messages[1].content).toBe('Done')
  })
})
