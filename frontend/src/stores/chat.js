import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import api from '@/services/api'
import { wsClient } from '@/services/wsClient'
import { isTerminalEvent, requiresRunId } from '@/services/ws/normalizeEvent'
import {
  RunStatus,
  WorkflowPhase,
  PhaseStatus,
  createRunState,
  isTerminalStatus,
  getPhaseTimeout,
  updatePhaseStatus,
  setTerminal,
  updateWatchdogHeartbeat,
  hasWatchdogTimeout,
  failRunByWatchdog,
  clearWatchdogTimer,
} from '@/stores/runTypes'

export const useChatStore = defineStore('chat', () => {
  // Conversations
  const conversations = ref([])
  const currentConversation = ref(null)
  const conversationsLoading = ref(false)
  const searchQuery = ref('')

  // Messages
  const messages = ref([])

  // Models
  const currentModel = ref(localStorage.getItem('preferredModel') || 'kimi-k2.5:cloud')
  const availableModels = ref([])
  const modelsData = ref(null) // Full models response with categories

  // Multi-Run State (Phase 2: v8 Frontend Stabilization)
  const runs = ref(new Map()) // Map<run_id, RunState>
  const activeRunId = ref(null) // Currently displayed run_id
  const pendingMessages = ref(new Map()) // Map<temp_id, {userMsg, assistantMsg, conversationId}>
  const runsByConversation = ref(new Map()) // Map<conv_id, Set<run_id>>
  const runHistory = ref([]) // Legacy: archived runs
  const orphanEvents = ref([]) // Events without valid run_id (for debugging)

  // Phases du workflow
  const WORKFLOW_PHASES = ['spec', 'plan', 'execute', 'verify', 'repair', 'complete']

  // Watchdog Configuration (v8: configurable)
  const watchdogConfig = ref({
    checkInterval: 15000, // Check every 15s
    defaultTimeout: 90000, // Default 90s timeout (increased from 60s for slow phases)
    phaseTimeouts: {
      // Per-phase timeouts (optional overrides)
      verify: 120000, // QA can take longer
      repair: 120000, // Repair cycles too
      execute: 90000,
    },
  })

  // WebSocket state
  const wsState = ref('disconnected')
  const wsDiagnostics = ref({
    url: '',
    state: 'disconnected',
    reconnectAttempts: 0,
    lastCloseCode: null,
    lastCloseReason: null,
    tokenPresent: false,
  })

  // Settings
  const settings = ref({
    showThinking: localStorage.getItem('showThinking') !== 'false',
    showToolParams: localStorage.getItem('showToolParams') !== 'false',
    compactMode: localStorage.getItem('compactMode') === 'true',
  })

  // Computed
  const filteredConversations = computed(() => {
    if (!searchQuery.value) return conversations.value
    const q = searchQuery.value.toLowerCase()
    return conversations.value.filter(
      (c) => c.title?.toLowerCase().includes(q) || c.id?.toLowerCase().includes(q)
    )
  })

  const modelsByCategory = computed(() => {
    if (!modelsData.value?.categories) {
      // Fallback: group all models under "other"
      return {
        other: availableModels.value.map((name) => ({ name })),
      }
    }
    return modelsData.value.categories
  })

  // ============================================================
  // Run Management Functions (Phase 2: Multi-Run Support)
  // ============================================================

  /**
   * Create a new run and track it in the registry
   */
  function createRun(runId, conversationId, userMessage, assistantMessage) {
    const isPlaceholder = !userMessage || !assistantMessage

    // Use factory function from runTypes
    const run = createRunState(runId, {
      conversationId,
      messageId: userMessage?.id || null,
      assistantMessageId: assistantMessage?.id || null,
      isPlaceholder,
    })

    // v8: Initialize phase timestamp for starting
    run.phaseTimestamps.starting = new Date(run.startedAt).getTime()

    runs.value.set(runId, run)

    // Track run by conversation (if known)
    if (conversationId) {
      if (!runsByConversation.value.has(conversationId)) {
        runsByConversation.value.set(conversationId, new Set())
      }
      runsByConversation.value.get(conversationId).add(runId)
    }

    // Set as active
    activeRunId.value = runId

    // Start watchdog
    startWatchdog(runId)

    return run
  }

  /**
   * Get or create run (for out-of-order events)
   * @param {string} runId - Run identifier
   * @param {Object} event - Optional event data for context resolution
   * @returns {Object} Run state object
   */
  function getOrCreateRun(runId, event = null) {
    let run = runs.value.get(runId)
    if (run) return run

    // Try to resolve conversation from event or current context
    const convId = event
      ? event?.data?.conversation_id ||
        event?.data?.conversationId ||
        currentConversation.value?.id ||
        null
      : currentConversation.value?.id || null

    // Check pending messages for matching conversation
    // V8 FIX: For new conversations, pending.conversationId may be null, so match on:
    //   1. Exact conversation match (pending.conversationId === convId)
    //   2. OR pending has no conversation (new conversation case)
    if (convId) {
      for (const pending of pendingMessages.value.values()) {
        if (!pending.runId && (pending.conversationId === convId || !pending.conversationId)) {
          pending.runId = runId
          pending.userMsg.run_id = runId
          pending.assistantMsg.run_id = runId
          run = createRun(runId, convId, pending.userMsg, pending.assistantMsg)
          pendingMessages.value.delete(pending.tempId)
          return run
        }
      }
    }

    // Create placeholder run
    return createRun(runId, convId, null, null)
  }

  /**
   * Mark run as complete and finalize associated message
   */
  function markRunComplete(runId, data) {
    const run = runs.value.get(runId) || getOrCreateRun(runId)
    if (run.status === RunStatus.COMPLETE || run.status === RunStatus.FAILED) {
      console.warn(`[Run Registry] Terminal already set for run ${runId}`)
      return
    }

    // 🔍 DEBUG: Log incoming data
    console.log('[DEBUG] markRunComplete called:', {
      runId,
      dataKeys: Object.keys(data),
      hasResponse: !!data.response,
      responseLength: data.response?.length || 0,
      response: data.response,
      runTokens: run.tokens,
      assistantMessageId: run.assistantMessageId,
    })

    // v8: Use setTerminal helper
    const finalResponse = data.response || data.content || run.tokens
    const runDuration = run.endedAt
      ? new Date(run.endedAt).getTime() - new Date(run.startedAt).getTime()
      : null
    setTerminal(run, 'complete', {
      response: finalResponse,
      tools_used: data.tools_used || [],
      iterations: data.iterations,
      duration_ms: data.duration_ms || runDuration,
      verification: data.verification,
      verdict: data.verdict,
    })

    run.workflowPhase = WorkflowPhase.COMPLETE
    // Note: run.status, endedAt, duration are handled by setTerminal
    run.verification = data.verification
    run.verdict = data.verdict
    run.currentPhase = WorkflowPhase.COMPLETE

    // Mark last active phase as complete
    if (run.phaseHistory.length > 0) {
      const lastPhase = run.phaseHistory[run.phaseHistory.length - 1].phase
      updatePhaseStatus(run, lastPhase, PhaseStatus.COMPLETE)
    }
    updatePhaseStatus(run, 'complete', PhaseStatus.COMPLETE)

    // Update associated message
    const msg = messages.value.find((m) => m.id === run.assistantMessageId)

    // 🔍 DEBUG: Log message update
    console.log('[DEBUG] Message update:', {
      messageFound: !!msg,
      messageId: msg?.id,
      currentContent: msg?.content,
      newContent: finalResponse,
      willUpdate: !!msg && !!finalResponse,
    })

    if (msg) {
      msg.streaming = false
      msg.content = finalResponse
      msg.tools_used = data.tools_used || []
      msg.iterations = data.iterations
      const msgDuration = run.endedAt
        ? new Date(run.endedAt).getTime() - new Date(run.startedAt).getTime()
        : null
      msg.duration_ms = data.duration_ms || msgDuration
      msg.model = data.model_used || data.model
      msg.verification = data.verification
      msg.verdict = data.verdict
      msg.finalized_at = Date.now()

      // 🔍 DEBUG: Confirm update
      console.log('[DEBUG] Message updated successfully:', {
        msgId: msg.id,
        contentLength: msg.content?.length || 0,
      })
    } else {
      console.error('[DEBUG] ❌ Message NOT FOUND for assistantMessageId:', run.assistantMessageId)
      console.error(
        '[DEBUG] Available messages:',
        messages.value.map((m) => ({ id: m.id, role: m.role }))
      )
    }

    // Archive run
    runHistory.value.unshift({ ...run })
    if (runHistory.value.length > 50) {
      runHistory.value.pop()
    }

    stopWatchdog(runId)
  }

  /**
   * Mark run as failed with error message
   */
  function markRunFailed(runId, errorMsg) {
    const run = runs.value.get(runId) || getOrCreateRun(runId)
    if (run.status === RunStatus.COMPLETE || run.status === RunStatus.FAILED) {
      return
    }

    // v8: Use setTerminal helper
    setTerminal(run, 'error', {
      message: errorMsg,
      phase: run.workflowPhase,
    })

    run.workflowPhase = WorkflowPhase.COMPLETE
    // Note: run.status, endedAt are handled by setTerminal
    run.error = errorMsg
    run.currentPhase = 'error'

    // Update associated message
    const msg = messages.value.find((m) => m.id === run.assistantMessageId)
    if (msg) {
      msg.streaming = false
      msg.content = `❌ Erreur: ${errorMsg}`
      msg.isError = true
    }

    stopWatchdog(runId)
    console.error(`[Run Registry] Failed run ${runId}: ${errorMsg}`)
  }

  /**
   * Cleanup old completed runs to prevent memory bloat
   */
  function cleanupOldRuns(conversationId) {
    const runIds = runsByConversation.value.get(conversationId)
    if (!runIds) return

    const now = Date.now()
    const CLEANUP_THRESHOLD = 300000 // 5 minutes

    for (const runId of Array.from(runIds)) {
      const run = runs.value.get(runId)
      const endTime = run?.endedAt ? new Date(run.endedAt).getTime() : null
      if (run && run.status !== RunStatus.RUNNING && endTime && now - endTime > CLEANUP_THRESHOLD) {
        runs.value.delete(runId)
        runIds.delete(runId)
        console.log(`[Run Registry] Cleaned up old run ${runId}`)
      }
    }
  }

  /**
   * Cleanup global: purge terminées > 5min, limite Map à 100 runs (CRQ-P0-5)
   * Appelé automatiquement toutes les 60s
   */
  function cleanupGlobalRuns() {
    const now = Date.now()
    const RETENTION_MS = 5 * 60 * 1000 // 5 minutes
    const MAX_RUNS = 100

    // 1. Purger runs terminées > 5min
    let purged = 0
    for (const [runId, run] of runs.value.entries()) {
      if (run.terminal && run.endedAt) {
        const elapsed = now - new Date(run.endedAt).getTime()
        if (elapsed > RETENTION_MS) {
          runs.value.delete(runId)
          // Aussi supprimer de runsByConversation
          if (run.conversationId) {
            const convRuns = runsByConversation.value.get(run.conversationId)
            convRuns?.delete(runId)
          }
          purged++
        }
      }
    }

    // 2. Si encore > MAX_RUNS, purger plus anciennes
    if (runs.value.size > MAX_RUNS) {
      const sorted = Array.from(runs.value.entries()).sort(
        (a, b) => new Date(a[1].startedAt) - new Date(b[1].startedAt)
      )

      const toDelete = sorted.slice(0, runs.value.size - MAX_RUNS)
      toDelete.forEach(([runId, run]) => {
        runs.value.delete(runId)
        if (run.conversationId) {
          const convRuns = runsByConversation.value.get(run.conversationId)
          convRuns?.delete(runId)
        }
        purged++
      })
    }

    // 3. Purger orphanEvents > 100
    if (orphanEvents.value.length > 100) {
      orphanEvents.value = orphanEvents.value.slice(-100)
    }

    if (purged > 0) {
      console.log(`[Cleanup] Purged ${purged} old runs (total: ${runs.value.size})`)
    }
  }

  // ============================================================
  // Initialize WebSocket listeners
  function initWebSocket() {
    // Éviter les listeners dupliqués
    if (wsClient._listenersInitialized) {
      return
    }
    wsClient._listenersInitialized = true
    wsClient.on('stateChange', (state) => {
      wsState.value = state
      wsDiagnostics.value = wsClient.getDiagnostics()
    })

    wsClient.on('event', (event) => {
      handleNormalizedEvent(event)
    })

    wsClient.on('error', (error) => {
      // WebSocket connection error (no run_id)
      addErrorMessage(error?.message || 'WebSocket error')
    })

    // NOUVEAU: Réception de la liste des modèles
    wsClient.on('models', (data) => {
      if (data.models) {
        availableModels.value = data.models
      }
    })

    wsClient.connect()
  }

  function resolveRunId(event) {
    if (event.run_id) return event.run_id
    const dataRunId = event.data?.run_id || event.data?.runId
    if (dataRunId) return dataRunId

    const convId = event.data?.conversation_id || event.data?.conversationId
    if (convId && runsByConversation.value.has(convId)) {
      const runIds = Array.from(runsByConversation.value.get(convId))
      const running = runIds
        .map((id) => runs.value.get(id))
        .filter((r) => r && r.status === RunStatus.RUNNING)
      if (running.length === 1) return running[0].id
    }

    const runningRuns = Array.from(runs.value.values()).filter(
      (r) => r.status === RunStatus.RUNNING
    )
    if (runningRuns.length === 1) return runningRuns[0].id

    return null
  }

  function handleNormalizedEvent(event) {
    if (!event || !event.type) return

    const resolvedRunId = resolveRunId(event)
    const data = event.data || {}

    // V8: Enforce backend authority - reject events without run_id (except conversation_created)
    if (!resolvedRunId && event.type !== 'conversation_created') {
      orphanEvents.value.push({ ...event, receivedAt: Date.now(), rejected: true })
      if (orphanEvents.value.length > 100) orphanEvents.value.shift()

      // Try to handle tokens gracefully for UX
      if (event.type === 'thinking' && data.kind === 'token') {
        const lastMsg = messages.value[messages.value.length - 1]
        if (lastMsg && lastMsg.streaming) {
          lastMsg.content += data.content || ''
          lastMsg.lastUpdate = Date.now()
        }
      }

      // Handle explicit errors
      if (event.type === 'error') {
        addErrorMessage(data.message || data.error || 'Erreur inconnue')
      }

      return
    }

    switch (event.type) {
      case 'thinking': {
        if (data.kind === 'token') {
          const run = getOrCreateRun(resolvedRunId, event)
          run.tokens += data.content || ''
          run.currentPhase = 'streaming'
          run.lastEventAt = new Date().toISOString() // V8: Update ISO timestamp

          // Update watchdog heartbeat
          run.watchdog.lastHeartbeatAt = run.lastEventAt

          const msg = messages.value.find((m) => m.id === run.assistantMessageId)
          if (msg && msg.streaming) {
            msg.content = run.tokens
            msg.lastUpdate = Date.now()
          }
          break
        }

        const run = getOrCreateRun(resolvedRunId, event)
        run.thinking.push({
          // V8: thinking array
          message: data.message,
          iteration: data.iteration,
          phase: data.phase,
          timestamp: Date.now(),
        })
        if (data.phase) {
          run.workflowPhase = data.phase
        }
        run.currentPhase = 'thinking'
        run.currentIteration = data.iteration
        run.lastEventAt = new Date().toISOString() // V8: Update ISO timestamp

        // Update watchdog heartbeat
        run.watchdog.lastHeartbeatAt = run.lastEventAt
        break
      }

      case 'phase': {
        const run = getOrCreateRun(resolvedRunId, event)
        const now = Date.now()
        run.workflowPhase = data.phase

        // v8: Update phase status and timestamps
        if (data.status) {
          updatePhaseStatus(run, data.phase, data.status)
        } else {
          // Default to running if no status provided
          updatePhaseStatus(run, data.phase, PhaseStatus.RUNNING)
        }

        // Legacy: Record phase timestamp
        if (run.phaseTimestamps && data.phase in run.phaseTimestamps) {
          run.phaseTimestamps[data.phase] = now
        }

        run.phaseHistory.push({
          phase: data.phase,
          status: data.status,
          message: data.message,
          timestamp: now,
        })
        run.currentPhase = data.phase
        run.lastEventAt = new Date().toISOString() // V8: Update ISO timestamp

        // Update watchdog heartbeat
        run.watchdog.lastHeartbeatAt = run.lastEventAt
        break
      }

      case 'verification_item': {
        const run = getOrCreateRun(resolvedRunId, event)
        const checkName = data.check_name || data.name || data.check || 'unknown'
        const status =
          data.status || (data.passed === true ? 'passed' : data.passed === false ? 'failed' : null)
        const item = {
          check_name: checkName,
          status: status || 'running',
          output: data.output,
          error: data.error,
          timestamp: Date.now(),
        }

        const existingIdx = run.verification.findIndex((v) => v.check_name === checkName)
        if (existingIdx >= 0) {
          run.verification[existingIdx] = item
        } else {
          run.verification.push(item)
        }
        run.lastEventAt = new Date().toISOString() // V8: Update ISO timestamp

        // Update watchdog heartbeat
        run.watchdog.lastHeartbeatAt = run.lastEventAt
        break
      }

      case 'tool': {
        const run = getOrCreateRun(resolvedRunId, event)
        run.tools.push({
          // V8: Use 'tools' instead of 'toolCalls'
          tool: data.tool,
          params: data.params || data.input || {},
          iteration: data.iteration,
          status: data.status,
          timestamp: Date.now(),
        })
        run.currentPhase = 'tool'
        run.currentTool = data.tool
        run.lastEventAt = new Date().toISOString() // V8: Update ISO timestamp

        // Update watchdog heartbeat
        run.watchdog.lastHeartbeatAt = run.lastEventAt
        break
      }

      case 'complete': {
        // 🔍 DEBUG: Log complete event
        console.log('[DEBUG] Complete event received:', {
          runId: resolvedRunId,
          dataKeys: Object.keys(data),
          hasResponse: !!data.response,
          responsePreview: data.response?.substring(0, 100),
          eventData: data,
        })

        const run = getOrCreateRun(resolvedRunId, event)
        run.terminal = true // V8: Mark as terminal
        markRunComplete(resolvedRunId, data)
        break
      }

      case 'error': {
        const run = getOrCreateRun(resolvedRunId, event)
        run.terminal = true // V8: Mark as terminal
        const errorMsg = data.message || data.error || 'Unknown error'
        markRunFailed(resolvedRunId, errorMsg)
        break
      }

      case 'conversation_created': {
        const convId = data.conversation_id || data.id
        if (!convId) {
          console.error('[WS] conversation_created missing conversation_id')
          return
        }

        currentConversation.value = {
          id: convId,
          title: data.title || currentConversation.value?.title,
        }

        if (!resolvedRunId) {
          fetchConversations()
          return
        }

        let run = runs.value.get(resolvedRunId)

        const isPlaceholder = run && run.status === RunStatus.PENDING && !run.terminal
        if (run && isPlaceholder) {
          run.conversation_id = convId
          run.status = RunStatus.RUNNING

          if (!runsByConversation.value.has(convId)) {
            runsByConversation.value.set(convId, new Set())
          }
          runsByConversation.value.get(convId).add(resolvedRunId)
        } else if (!run) {
          // V8 FIX: For new conversations, pending.conversationId may be null
          const pending = Array.from(pendingMessages.value.values()).find(
            (p) => !p.runId && (p.conversationId === convId || !p.conversationId)
          )

          if (pending) {
            pending.runId = resolvedRunId
            pending.conversationId = convId // Update with backend's conversation_id
            createRun(resolvedRunId, convId, pending.userMsg, pending.assistantMsg)
            pendingMessages.value.delete(pending.tempId)
          } else {
            createRun(resolvedRunId, convId, null, null)
          }
        }

        fetchConversations()
        break
      }

      default:
    }
  }

  function addErrorMessage(error) {
    const lastMsg = messages.value[messages.value.length - 1]
    if (lastMsg && lastMsg.streaming) {
      lastMsg.content = `❌ Erreur: ${error}`
      lastMsg.streaming = false
      lastMsg.isError = true
    } else {
      messages.value.push({
        id: Date.now(),
        role: 'assistant',
        content: `❌ Erreur: ${error}`,
        isError: true,
        created_at: new Date().toISOString(),
      })
    }
  }

  // ============================================================
  // Per-Run Watchdog System (V8 Complete Implementation)
  // ============================================================

  /**
   * Start watchdog for a specific run (V8)
   * Features:
   * - Per-run timer with configurable timeout
   * - Heartbeat tracking on every WS event
   * - Automatic failure on timeout
   * - Cleanup on terminal state
   */
  function startWatchdog(runId) {
    const run = runs.value.get(runId)
    if (!run) {
      console.warn(`[Watchdog] Cannot start: run ${runId} not found`)
      return
    }

    // Clear any existing timer first
    clearWatchdogTimer(run)

    const config = watchdogConfig.value
    const WATCHDOG_INTERVAL = config.checkInterval

    // Set initial timeout based on current phase
    const phaseTimeout = getPhaseTimeout(run.workflowPhase)
    run.watchdog.timeoutMs = phaseTimeout
    run.watchdog.lastHeartbeatAt = new Date().toISOString()

    // Create the watchdog interval
    const timerId = setInterval(() => {
      const currentRun = runs.value.get(runId)

      // Run was deleted - clean up
      if (!currentRun) {
        clearInterval(timerId)
        return
      }

      // Check for timeout
      if (hasWatchdogTimeout(currentRun)) {
        const elapsed = Date.now() - new Date(currentRun.watchdog.lastHeartbeatAt).getTime()
        console.error(
          `[Watchdog] Run ${runId} timeout after ${elapsed}ms in phase ${currentRun.workflowPhase}`
        )

        // Fail the run
        failRunByWatchdog(
          currentRun,
          `Timeout: no events for ${Math.round(elapsed / 1000)}s in phase ${currentRun.workflowPhase}`
        )

        // Update UI
        const msg = messages.value.find((m) => m.id === currentRun.assistantMessageId)
        if (msg) {
          msg.streaming = false
          msg.content = `❌ Timeout: Run stalled for ${Math.round(elapsed / 1000)} seconds`
          msg.isError = true
        }

        // Clean up timer
        clearWatchdogTimer(currentRun)
        return
      }

      // Stop watchdog if run is terminal
      if (isTerminalStatus(currentRun.status)) {
        clearWatchdogTimer(currentRun)
      }
    }, WATCHDOG_INTERVAL)

    // Store timer ID
    run.watchdog.timerId = timerId
    console.log(`[Watchdog] Started for run ${runId} (timeout: ${run.watchdog.timeoutMs}ms)`)
  }

  /**
   * Update watchdog heartbeat on WebSocket event (V8)
   * Called automatically by handleNormalizedEvent for every event
   */
  function updateWatchdogFromEvent(runId) {
    const run = runs.value.get(runId)
    if (!run || !run.watchdog) return

    // Update heartbeat timestamp
    updateWatchdogHeartbeat(run)

    // Dynamically adjust timeout based on current phase
    const phaseTimeout = getPhaseTimeout(run.workflowPhase)
    if (phaseTimeout !== run.watchdog.timeoutMs) {
      run.watchdog.timeoutMs = phaseTimeout
      console.log(
        `[Watchdog] Run ${runId} timeout adjusted to ${phaseTimeout}ms for phase ${run.workflowPhase}`
      )
    }
  }

  /**
   * Stop watchdog for a specific run (V8)
   */
  function stopWatchdog(runId) {
    const run = runs.value.get(runId)
    if (!run) return

    clearWatchdogTimer(run)
    console.log(`[Watchdog] Stopped for run ${runId}`)
  }

  /**
   * Stop all active watchdogs (cleanup on unmount/conversation change)
   */
  function stopAllWatchdogs() {
    let count = 0
    for (const [runId, run] of runs.value.entries()) {
      if (run.watchdog?.timerId) {
        clearInterval(run.watchdog.timerId)
        run.watchdog.timerId = null
        count++
      }
    }
    console.log(`[Watchdog] Stopped ${count} watchdog(s)`)
  }

  /**
   * Cleanup watchdogs for a specific conversation (navigation)
   */
  function cleanupWatchdogsForConversation(conversationId) {
    const runIds = runsByConversation.value.get(conversationId)
    if (!runIds) return

    for (const runId of runIds) {
      const run = runs.value.get(runId)
      if (run && isTerminalStatus(run.status)) {
        // Only clear completed/failed runs
        clearWatchdogTimer(run)
      }
    }
  }

  // API Methods
  async function fetchConversations() {
    conversationsLoading.value = true
    try {
      conversations.value = await api.getConversations()
    } catch (e) {
      console.error('Failed to fetch conversations:', e)
    } finally {
      conversationsLoading.value = false
    }
  }

  async function selectConversation(convId) {
    try {
      const conv = await api.getConversation(convId)
      currentConversation.value = conv
      messages.value = conv.messages || []

      // Set activeRunId to most recent run for this conversation if exists
      const conversationRuns = runsByConversation.value.get(convId)
      if (conversationRuns && conversationRuns.size > 0) {
        // Find most recent active run
        const runIds = Array.from(conversationRuns)
        const activeRuns = runIds
          .map((id) => runs.value.get(id))
          .filter((r) => r && r.status === RunStatus.RUNNING)
          .sort((a, b) => new Date(b.startedAt).getTime() - new Date(a.startedAt).getTime())

        if (activeRuns.length > 0) {
          activeRunId.value = activeRuns[0].id
        } else {
          activeRunId.value = null
        }
      } else {
        activeRunId.value = null
      }
    } catch (e) {
      console.error('Failed to load conversation:', e)
    }
  }

  async function renameConversation(convId, newTitle) {
    try {
      await api.renameConversation(convId, newTitle)
      const conv = conversations.value.find((c) => c.id === convId)
      if (conv) conv.title = newTitle
      if (currentConversation.value?.id === convId) {
        currentConversation.value.title = newTitle
      }
    } catch (e) {
      console.error('Failed to rename conversation:', e)
      throw e
    }
  }

  async function deleteConversation(convId) {
    try {
      await api.deleteConversation(convId)
      conversations.value = conversations.value.filter((c) => c.id !== convId)
      if (currentConversation.value?.id === convId) {
        newConversation()
      }
    } catch (e) {
      console.error('Failed to delete conversation:', e)
      throw e
    }
  }

  async function sendMessage(content) {
    if (!content.trim()) return

    const conversationId = currentConversation.value?.id

    // Add user message
    const userMsg = {
      id: Date.now(),
      role: 'user',
      content: content,
      run_id: null, // Will be set when run_id received
      created_at: new Date().toISOString(),
    }
    messages.value.push(userMsg)

    // Prepare assistant message placeholder
    const assistantMsg = {
      id: Date.now() + 1,
      role: 'assistant',
      content: '',
      run_id: null, // Will be set when run_id received
      streaming: true,
      created_at: new Date().toISOString(),
    }
    messages.value.push(assistantMsg)

    // Create pending entry (no run_id yet - backend will generate it)
    const tempId = `pending-${Date.now()}`
    pendingMessages.value.set(tempId, {
      tempId,
      conversationId,
      userMsg,
      assistantMsg,
      runId: null, // Will be filled when conversation_created event arrives
    })

    // Send to backend (backend will generate run_id)
    const sent = wsClient.sendMessage(content, conversationId, currentModel.value)

    if (!sent) {
      // Fallback to HTTP
      await sendMessageHTTP(content)
    }

    // Cleanup old runs
    if (conversationId) {
      cleanupOldRuns(conversationId)
    }
  }

  async function sendMessageHTTP(content) {
    try {
      const data = await api.sendMessage(content, currentConversation.value?.id, currentModel.value)

      if (!currentConversation.value) {
        currentConversation.value = { id: data.conversation_id }
        await fetchConversations()
      }

      // CRITICAL: Use backend's run_id if provided, otherwise warn and skip run creation
      const backendRunId = data.run_id
      if (!backendRunId) {
        console.error('[HTTP Fallback] Backend did not provide run_id - cannot create run')
        // Update messages directly (legacy v7 behavior)
        const lastMsg = messages.value[messages.value.length - 1]
        if (lastMsg && lastMsg.streaming) {
          lastMsg.content = data.response
          lastMsg.streaming = false
          lastMsg.tools_used = data.tools_used
        }
        return
      }

      // Find pending message
      const pending = Array.from(pendingMessages.value.values()).find((p) => !p.runId)
      if (pending) {
        // Create run with backend's run_id
        const run = createRun(
          backendRunId,
          data.conversation_id,
          pending.userMsg,
          pending.assistantMsg
        )

        // Populate tools from tools_used
        if (data.tools_used) {
          run.tools = data.tools_used.map((tool, i) => ({
            tool: typeof tool === 'string' ? tool : tool.tool,
            params: tool.params || {},
            iteration: i,
            timestamp: Date.now(),
          }))
        }

        // Mark as complete immediately (HTTP is synchronous)
        markRunComplete(backendRunId, data)

        pendingMessages.value.delete(pending.tempId)
      } else {
        // Fallback: update last message directly
        const lastMsg = messages.value[messages.value.length - 1]
        if (lastMsg && lastMsg.streaming) {
          lastMsg.content = data.response
          lastMsg.streaming = false
          lastMsg.tools_used = data.tools_used
          lastMsg.iterations = data.iterations
          lastMsg.duration_ms = data.duration_ms
          lastMsg.model = data.model_used
        }
      }
    } catch (e) {
      addErrorMessage(e.message)

      // Clean up pending message without creating run (no backend run_id)
      const pending = Array.from(pendingMessages.value.values()).find((p) => !p.runId)
      if (pending) {
        pendingMessages.value.delete(pending.tempId)
        console.warn('[HTTP Fallback] Request failed, no run created (no backend run_id)')
      }
    }
  }

  async function retryLastMessage() {
    if (messages.value.length < 2) return

    let lastUserMsgIndex = -1
    for (let i = messages.value.length - 1; i >= 0; i--) {
      if (messages.value[i].role === 'user') {
        lastUserMsgIndex = i
        break
      }
    }

    if (lastUserMsgIndex === -1) return

    const content = messages.value[lastUserMsgIndex].content
    messages.value = messages.value.slice(0, lastUserMsgIndex)
    await sendMessage(content)
  }

  async function fetchModels() {
    try {
      const data = await api.getModels()
      // Store full response with categories
      modelsData.value = data
      availableModels.value = (data.models || []).map((m) => (typeof m === 'string' ? m : m.name))
      if (data.default_model && !localStorage.getItem('preferredModel')) {
        currentModel.value = data.default_model
      }
    } catch (e) {
      console.error('Failed to fetch models:', e)
    }
  }

  /**
   * Rafraîchit la liste des modèles via WebSocket
   */
  function refreshModels() {
    const sent = wsClient.send({
      action: 'get_models',
    })
    if (!sent) {
      // Fallback HTTP
      fetchModels()
    }
  }

  function setModel(model) {
    currentModel.value = model
    localStorage.setItem('preferredModel', model)
  }

  function newConversation() {
    // Stop all active watchdogs
    stopAllWatchdogs()

    currentConversation.value = null
    messages.value = []
    activeRunId.value = null
    pendingMessages.value.clear()
    // Note: We keep runs Map for history/inspection
  }

  function updateSettings(key, value) {
    settings.value[key] = value
    localStorage.setItem(key, value.toString())
  }

  function exportConversation(format = 'json') {
    if (!currentConversation.value) return null

    const data = {
      id: currentConversation.value.id,
      title: currentConversation.value.title,
      messages: messages.value,
      exportedAt: new Date().toISOString(),
    }

    if (format === 'json') {
      return JSON.stringify(data, null, 2)
    } else if (format === 'markdown') {
      let md = `# ${data.title || 'Conversation'}\n\n`
      md += `*Exporté le ${new Date().toLocaleString()}*\n\n---\n\n`

      for (const msg of data.messages) {
        const role = msg.role === 'user' ? '👤 **Vous**' : '🤖 **Assistant**'
        md += `${role}\n\n${msg.content}\n\n`
        if (msg.tools_used?.length) {
          md += `*Outils: ${msg.tools_used.join(', ')}*\n\n`
        }
        md += `---\n\n`
      }

      return md
    }

    return null
  }

  /**
   * Relance uniquement la vérification QA (sans ré-exécuter)
   * CORRIGÉ: Maintenant câblé au backend avec run_id
   */
  async function rerunVerification() {
    const runId = activeRunId.value
    if (!runId) {
      console.warn('No active run to re-verify')
      return false
    }

    const run = runs.value.get(runId)
    if (!run) {
      console.warn('Run not found')
      return false
    }

    // Update run state
    run.workflowPhase = WorkflowPhase.VERIFY
    run.currentPhase = 'verify'

    const sent = wsClient.send({
      action: 'rerun_verify',
      run_id: runId, // CRITICAL: Include run_id
      conversation_id: currentConversation.value?.id,
      model: currentModel.value,
    })

    if (!sent) {
      console.error('Cannot send rerun_verify: WebSocket not connected')
      return false
    }

    return true
  }

  /**
   * Force un cycle de réparation
   * CORRIGÉ: Maintenant câblé au backend avec run_id
   */
  async function forceRepair() {
    const runId = activeRunId.value
    if (!runId) {
      console.warn('No active run to repair')
      return false
    }

    const run = runs.value.get(runId)
    if (!run) {
      console.warn('Run not found')
      return false
    }

    // Update run state
    run.workflowPhase = WorkflowPhase.REPAIR
    run.currentPhase = 'repair'
    run.repairCycles = (run.repairCycles || 0) + 1

    const sent = wsClient.send({
      action: 'force_repair',
      run_id: runId, // CRITICAL: Include run_id
      conversation_id: currentConversation.value?.id,
      model: currentModel.value,
    })

    if (!sent) {
      console.error('Cannot send force_repair: WebSocket not connected')
      return false
    }

    return true
  }

  /**
   * Exporte le rapport de run complet (active run)
   */
  function exportRunReport() {
    const runId = activeRunId.value
    if (!runId) return null

    const run = runs.value.get(runId)
    if (!run) return null

    const runDuration = run.endedAt
      ? new Date(run.endedAt).getTime() - new Date(run.startedAt).getTime()
      : null
    const report = {
      run_id: run.run_id,
      timestamp: new Date().toISOString(),
      duration_ms: runDuration,
      status: run.status,
      workflow_phase: run.workflowPhase,
      phases: run.phaseHistory,
      tools_used: run.tools.map((t) => ({
        tool: t.tool,
        params: t.params,
        iteration: t.iteration,
      })),
      verification: run.verification,
      verdict: run.verdict,
      repair_cycles: run.repairCycles,
      error: run.error,
    }

    return JSON.stringify(report, null, 2)
  }

  /**
   * v8: Rehydrate runs after WebSocket reconnection
   *
   * This function handles the case where the WebSocket disconnects and reconnects.
   * It marks any "stuck" running runs as failed and cleans up orphan events.
   *
   * @param {string} [reason='reconnect'] - Reason for rehydration
   */
  function rehydrateRuns(reason = 'reconnect') {
    console.log(`[Rehydrate] Starting rehydration (reason: ${reason})`)

    const now = Date.now()
    const STALE_THRESHOLD = 120000 // 2 minutes

    let staleCount = 0
    let cleanedOrphans = 0

    // Check all running runs
    for (const [runId, run] of runs.value.entries()) {
      if (run.status === RunStatus.RUNNING) {
        const elapsed = now - new Date(run.lastEventAt).getTime()

        if (elapsed > STALE_THRESHOLD) {
          // Mark as failed due to disconnect
          console.warn(
            `[Rehydrate] Run ${runId} stale (${Math.round(elapsed / 1000)}s since last event) → marking FAILED`
          )
          markRunFailed(runId, `Connection lost: no events for ${Math.round(elapsed / 1000)}s`)
          staleCount++
        } else {
          // Still potentially active - update lastEventAt to give it grace period
          console.log(`[Rehydrate] Run ${runId} still active, granting grace period`)
          run.lastEventAt = new Date(now).toISOString()
        }
      }
    }

    // Clear orphan events older than threshold
    const originalOrphanCount = orphanEvents.value.length
    orphanEvents.value = orphanEvents.value.filter((event) => {
      const age = now - event.receivedAt
      return age < STALE_THRESHOLD
    })
    cleanedOrphans = originalOrphanCount - orphanEvents.value.length

    console.log(
      `[Rehydrate] Complete: ${staleCount} runs failed, ${cleanedOrphans} orphan events cleaned`
    )

    return { staleCount, cleanedOrphans }
  }

  /**
   * v8: Get run state summary for debugging
   */
  function getRunsSummary() {
    const summary = {
      total: runs.value.size,
      byStatus: {
        running: 0,
        complete: 0,
        failed: 0,
        pending: 0,
      },
      orphanEvents: orphanEvents.value.length,
      activeRunId: activeRunId.value,
    }

    for (const run of runs.value.values()) {
      if (summary.byStatus[run.status] !== undefined) {
        summary.byStatus[run.status]++
      }
    }

    return summary
  }

  // Computed: WebSocket connection status
  const isConnected = computed(() => wsState.value === 'connected')

  // Computed: Loading state (any active run that's not completed)
  const isLoading = computed(() => {
    return Array.from(runs.value.values()).some(
      (run) => run.status === 'running' || run.status === 'pending'
    )
  })

  // Watch model changes
  watch(currentModel, (newModel) => {
    localStorage.setItem('preferredModel', newModel)
  })

  // CRQ-P0-5: Cleanup automatique toutes les 60s (memory leak prevention)
  const cleanupIntervalId = setInterval(cleanupGlobalRuns, 60000)

  return {
    // State
    conversations,
    currentConversation,
    conversationsLoading,
    searchQuery,
    filteredConversations,
    messages,
    currentModel,
    availableModels,
    modelsData,
    modelsByCategory,
    wsState,
    wsDiagnostics,
    isConnected,
    isLoading,
    settings,
    // Multi-run state (Phase 2)
    runs,
    activeRunId,
    pendingMessages,
    runsByConversation,
    runHistory,
    orphanEvents,
    watchdogConfig,
    rehydrateRuns,
    getRunsSummary,

    // Methods
    initWebSocket,
    fetchConversations,
    selectConversation,
    renameConversation,
    deleteConversation,
    sendMessage,
    retryLastMessage,
    fetchModels,
    refreshModels,
    setModel,
    newConversation,
    updateSettings,
    exportConversation,
    // Run management (Phase 2)
    createRun,
    getOrCreateRun,
    markRunComplete,
    markRunFailed,
    cleanupOldRuns,
    stopAllWatchdogs,
    // Actions workflow
    rerunVerification,
    forceRepair,
    exportRunReport,
    // Constantes
    WORKFLOW_PHASES,
  }
})
