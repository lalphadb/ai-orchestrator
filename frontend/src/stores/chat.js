import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import api from '@/services/api'
import { wsClient } from '@/services/wsClient'

export const useChatStore = defineStore('chat', () => {
  // Conversations
  const conversations = ref([])
  const currentConversation = ref(null)
  const conversationsLoading = ref(false)
  const searchQuery = ref('')
  
  // Messages
  const messages = ref([])
  const isLoading = ref(false)
  
  // Models
  const currentModel = ref(localStorage.getItem('preferredModel') || 'kimi-k2:1t-cloud')
  const availableModels = ref([])
  
  // Run Session (traçabilité ReAct + Workflow)
  const currentRun = ref(null)
  const runHistory = ref([])

  // Watchdog timer for stuck detection
  const watchdogTimer = ref(null)

  // Phases du workflow
  const WORKFLOW_PHASES = ['spec', 'plan', 'execute', 'verify', 'repair', 'complete']

  // WebSocket state
  const wsState = ref('disconnected')
  
  // Settings
  const settings = ref({
    showThinking: localStorage.getItem('showThinking') !== 'false',
    showToolParams: localStorage.getItem('showToolParams') !== 'false',
    compactMode: localStorage.getItem('compactMode') === 'true'
  })
  
  // Computed
  const filteredConversations = computed(() => {
    if (!searchQuery.value) return conversations.value
    const q = searchQuery.value.toLowerCase()
    return conversations.value.filter(c => 
      c.title?.toLowerCase().includes(q) ||
      c.id?.toLowerCase().includes(q)
    )
  })
  
  // Initialize WebSocket listeners
  function initWebSocket() {
    // Éviter les listeners dupliqués
    if (wsClient._listenersInitialized) {
      console.log("WebSocket listeners already initialized, skipping")
      return
    }
    wsClient._listenersInitialized = true
    wsClient.on('stateChange', (state) => {
      wsState.value = state
    })

    wsClient.on('thinking', (data, runId) => {
      if (currentRun.value) {
        currentRun.value.thinking.push({
          message: data.message,
          iteration: data.iteration,
          phase: data.phase,
          timestamp: Date.now()
        })
        if (data.phase) {
          currentRun.value.workflowPhase = data.phase
        }
        currentRun.value.currentPhase = 'thinking'
        currentRun.value.currentIteration = data.iteration
      }
    })

    // Changement de phase workflow
    wsClient.on('phase', (data, runId) => {
      if (currentRun.value) {
        currentRun.value.workflowPhase = data.phase
        currentRun.value.phaseHistory.push({
          phase: data.phase,
          status: data.status,
          message: data.message,
          timestamp: Date.now()
        })
        currentRun.value.currentPhase = data.phase
      }
    })

    // Item de vérification QA
    wsClient.on('verificationItem', (data, runId) => {
      if (currentRun.value) {
        const existingIdx = currentRun.value.verificationItems.findIndex(
          v => v.check_name === data.check_name
        )
        const item = {
          check_name: data.check_name,
          status: data.status,
          output: data.output,
          error: data.error,
          timestamp: Date.now()
        }
        if (existingIdx >= 0) {
          currentRun.value.verificationItems[existingIdx] = item
        } else {
          currentRun.value.verificationItems.push(item)
        }
      }
    })

    // NOUVEAU: Résultat de re-vérification
    wsClient.on('verification_complete', (data, runId) => {
      if (currentRun.value) {
        currentRun.value.verification = data.verification
        currentRun.value.verdict = data.verdict
        currentRun.value.workflowPhase = 'complete'
        
        // Notification visuelle
        if (data.action === 'rerun_verify') {
          console.log('Re-vérification terminée:', data.verdict?.status)
        }
      }
    })

    wsClient.on('tool', (data, runId) => {
      if (currentRun.value) {
        currentRun.value.toolCalls.push({
          tool: data.tool,
          params: data.params,
          iteration: data.iteration,
          timestamp: Date.now()
        })
        currentRun.value.currentPhase = 'tool'
        currentRun.value.currentTool = data.tool
      }
    })

    wsClient.on('tokens', (tokens) => {
      if (currentRun.value) {
        currentRun.value.tokens += tokens
        currentRun.value.currentPhase = 'streaming'
        updateStreamingMessage(currentRun.value.tokens)
      }
    })

    wsClient.on('complete', (data, runId) => {
      if (currentRun.value) {
        currentRun.value.complete = data
        currentRun.value.currentPhase = 'complete'
        currentRun.value.workflowPhase = 'complete'
        currentRun.value.endTime = Date.now()
        currentRun.value.duration = currentRun.value.endTime - currentRun.value.startTime
        currentRun.value.verification = data.verification
        currentRun.value.verdict = data.verdict

        // Finalize message avec le contenu final
        finalizeMessage(data)

        // Archive run
        runHistory.value.unshift({ ...currentRun.value })
        if (runHistory.value.length > 50) {
          runHistory.value.pop()
        }
      }
      isLoading.value = false
      stopWatchdog()
    })

    wsClient.on('error', (error, runId) => {
      if (currentRun.value) {
        currentRun.value.error = error
        currentRun.value.currentPhase = 'error'
        currentRun.value.workflowPhase = 'failed'
      }
      addErrorMessage(typeof error === 'string' ? error : error.message || 'Erreur inconnue')
      isLoading.value = false
      stopWatchdog()
    })

    wsClient.on('conversationCreated', (data) => {
      currentConversation.value = { id: data.id, title: data.title }
      fetchConversations()
    })

    // NOUVEAU: Réception de la liste des modèles
    wsClient.on('models', (data) => {
      if (data.models) {
        availableModels.value = data.models
        console.log(`Modèles reçus: ${data.count}`)
      }
    })

    wsClient.connect()
  }
  
  /**
   * Met à jour le message en streaming - AMÉLIORÉ
   * Préserve le formatage et évite les remplacements intempestifs
   */
  function updateStreamingMessage(content) {
    const lastMsg = messages.value[messages.value.length - 1]
    if (lastMsg && lastMsg.role === 'assistant' && lastMsg.streaming) {
      // Préserver le contenu existant si le nouveau est vide
      if (content && content.trim()) {
        lastMsg.content = content
        lastMsg.lastUpdate = Date.now()
      }
    }
  }
  
  /**
   * Finalise le message après streaming - AMÉLIORÉ
   * Corrige le problème de lisibilité
   */
  function finalizeMessage(data) {
    const lastMsg = messages.value[messages.value.length - 1]
    console.log('[finalizeMessage] lastMsg:', lastMsg, 'data:', data)

    if (lastMsg && lastMsg.role === 'assistant') {
      // Récupérer le contenu final
      const finalContent = data.response || data.content || ''
      console.log('[finalizeMessage] finalContent:', finalContent)

      // TOUJOURS utiliser la réponse finale si elle existe
      // Cela évite d'afficher le JSON brut accumulé pendant le streaming
      if (finalContent && finalContent.trim()) {
        lastMsg.content = finalContent
        console.log('[finalizeMessage] Set content to:', lastMsg.content)
      } else if (currentRun.value?.tokens) {
        // Fallback: utiliser les tokens streamés si pas de réponse finale
        lastMsg.content = currentRun.value.tokens
        console.log('[finalizeMessage] Fallback to tokens:', lastMsg.content)
      } else {
        console.error('[finalizeMessage] NO CONTENT FOUND! data:', JSON.stringify(data))
      }

      lastMsg.streaming = false
      lastMsg.tools_used = data.tools_used || []
      lastMsg.iterations = data.iterations
      lastMsg.duration_ms = data.duration_ms
      lastMsg.model = data.model_used || data.model

      // Ajouter les métadonnées de vérification
      if (data.verification) {
        lastMsg.verification = data.verification
      }
      if (data.verdict) {
        lastMsg.verdict = data.verdict
      }

      // Timestamp de finalisation
      lastMsg.finalized_at = Date.now()
    } else {
      console.error('[finalizeMessage] No assistant message found! messages:', messages.value.length)
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
        created_at: new Date().toISOString()
      })
    }
  }

  // Watchdog functions
  function startWatchdog() {
    if (watchdogTimer.value) return // Already running

    const WATCHDOG_INTERVAL = 10000 // Check every 10s
    const STUCK_TIMEOUT = 20000 // Consider stuck after 20s

    watchdogTimer.value = setInterval(() => {
      if (!currentRun.value) {
        stopWatchdog()
        return
      }

      // Check if stuck (starting phase + no updates for >20s)
      if (currentRun.value.workflowPhase === 'starting') {
        const elapsed = Date.now() - currentRun.value.startTime
        if (elapsed > STUCK_TIMEOUT) {
          console.error(`[Watchdog] Run stuck for ${elapsed}ms → FAILED`)
          currentRun.value.workflowPhase = 'failed'
          currentRun.value.currentPhase = 'error'
          currentRun.value.error = `⏱️ Timeout: Aucun événement reçu après ${Math.round(elapsed/1000)}s`
          addErrorMessage(`Timeout: Le backend ne répond pas (${Math.round(elapsed/1000)}s)`)
          isLoading.value = false
          stopWatchdog()
        }
      }

      // Stop watchdog if run completed/failed
      if (['complete', 'failed'].includes(currentRun.value.workflowPhase)) {
        stopWatchdog()
      }
    }, WATCHDOG_INTERVAL)

    console.log('[Watchdog] Started for run', currentRun.value?.id)
  }

  function stopWatchdog() {
    if (watchdogTimer.value) {
      clearInterval(watchdogTimer.value)
      watchdogTimer.value = null
      console.log('[Watchdog] Stopped')
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
      currentRun.value = null
    } catch (e) {
      console.error('Failed to load conversation:', e)
    }
  }
  
  async function renameConversation(convId, newTitle) {
    try {
      await api.renameConversation(convId, newTitle)
      const conv = conversations.value.find(c => c.id === convId)
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
      conversations.value = conversations.value.filter(c => c.id !== convId)
      if (currentConversation.value?.id === convId) {
        newConversation()
      }
    } catch (e) {
      console.error('Failed to delete conversation:', e)
      throw e
    }
  }
  
  async function sendMessage(content) {
    if (!content.trim() || isLoading.value) return
    
    // Add user message
    messages.value.push({
      id: Date.now(),
      role: 'user',
      content: content,
      created_at: new Date().toISOString()
    })
    
    // Prepare assistant message for streaming
    messages.value.push({
      id: Date.now() + 1,
      role: 'assistant',
      content: '',
      streaming: true,
      created_at: new Date().toISOString()
    })
    
    // Create new run session with workflow support
    currentRun.value = {
      id: Date.now().toString(),
      startTime: Date.now(),
      endTime: null,
      duration: null,
      thinking: [],
      toolCalls: [],
      tokens: '',
      complete: null,
      error: null,
      currentPhase: 'starting',
      currentIteration: 0,
      currentTool: null,
      message: content,
      model: currentModel.value,
      // Champs workflow
      workflowPhase: 'starting',
      phaseHistory: [],
      verificationItems: [],
      verification: null,
      verdict: null,
      repairCycles: 0
    }

    isLoading.value = true

    // Start watchdog to detect stuck runs
    startWatchdog()

    // Try WebSocket first
    const sent = wsClient.sendMessage(content, currentConversation.value?.id, currentModel.value)
    
    if (!sent) {
      // Fallback to HTTP
      await sendMessageHTTP(content)
    }
  }
  
  async function sendMessageHTTP(content) {
    try {
      const data = await api.sendMessage(content, currentConversation.value?.id, currentModel.value)
      
      if (!currentConversation.value) {
        currentConversation.value = { id: data.conversation_id }
        await fetchConversations()
      }
      
      // Update last message
      const lastMsg = messages.value[messages.value.length - 1]
      if (lastMsg && lastMsg.streaming) {
        lastMsg.content = data.response
        lastMsg.streaming = false
        lastMsg.tools_used = data.tools_used
        lastMsg.iterations = data.iterations
        lastMsg.duration_ms = data.duration_ms
        lastMsg.model = data.model_used
      }
      
      if (currentRun.value) {
        currentRun.value.complete = data
        currentRun.value.currentPhase = 'complete'
        currentRun.value.workflowPhase = 'complete'
        currentRun.value.endTime = Date.now()
        currentRun.value.duration = currentRun.value.endTime - currentRun.value.startTime
        currentRun.value.verification = data.verification
        currentRun.value.verdict = data.verdict

        // Populate toolCalls from tools_used
        if (data.tools_used) {
          currentRun.value.toolCalls = data.tools_used.map((tool, i) => ({
            tool: typeof tool === 'string' ? tool : tool.tool,
            params: tool.params || {},
            iteration: i,
            timestamp: Date.now()
          }))
        }
      }
    } catch (e) {
      addErrorMessage(e.message)
      if (currentRun.value) {
        currentRun.value.error = e.message
        currentRun.value.currentPhase = 'error'
        currentRun.value.workflowPhase = 'failed'
      }
    } finally {
      isLoading.value = false
      stopWatchdog()
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
      availableModels.value = (data.models || []).map(m => typeof m === 'string' ? m : m.name)
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
      action: 'get_models'
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
    currentConversation.value = null
    messages.value = []
    currentRun.value = null
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
      exportedAt: new Date().toISOString()
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
   * CORRIGÉ: Maintenant câblé au backend
   */
  async function rerunVerification() {
    if (!currentRun.value?.complete) {
      console.warn('Pas de run à re-vérifier')
      return false
    }

    // Mettre à jour l'état
    currentRun.value.workflowPhase = 'verify'
    currentRun.value.currentPhase = 'verify'

    const sent = wsClient.send({
      action: 'rerun_verify',
      conversation_id: currentConversation.value?.id,
      model: currentModel.value
    })

    if (!sent) {
      console.error('Cannot send rerun_verify: WebSocket not connected')
      return false
    }
    
    return true
  }

  /**
   * Force un cycle de réparation
   * CORRIGÉ: Maintenant câblé au backend
   */
  async function forceRepair() {
    if (!currentRun.value?.complete) {
      console.warn('Pas de run à réparer')
      return false
    }

    // Mettre à jour l'état
    currentRun.value.workflowPhase = 'repair'
    currentRun.value.currentPhase = 'repair'
    currentRun.value.repairCycles++

    const sent = wsClient.send({
      action: 'force_repair',
      conversation_id: currentConversation.value?.id,
      model: currentModel.value
    })

    if (!sent) {
      console.error('Cannot send force_repair: WebSocket not connected')
      return false
    }
    
    return true
  }

  /**
   * Exporte le rapport de run complet
   */
  function exportRunReport() {
    if (!currentRun.value) return null

    const report = {
      run_id: currentRun.value.id,
      timestamp: new Date().toISOString(),
      duration_ms: currentRun.value.duration,
      model: currentRun.value.model,
      workflow_phase: currentRun.value.workflowPhase,
      phases: currentRun.value.phaseHistory,
      tools_used: currentRun.value.toolCalls.map(t => ({
        tool: t.tool,
        params: t.params,
        iteration: t.iteration
      })),
      verification: currentRun.value.verification,
      verification_items: currentRun.value.verificationItems,
      verdict: currentRun.value.verdict,
      repair_cycles: currentRun.value.repairCycles,
      error: currentRun.value.error
    }

    return JSON.stringify(report, null, 2)
  }
  
  // Watch model changes
  watch(currentModel, (newModel) => {
    localStorage.setItem('preferredModel', newModel)
  })
  
  return {
    // State
    conversations,
    currentConversation,
    conversationsLoading,
    searchQuery,
    filteredConversations,
    messages,
    isLoading,
    currentModel,
    availableModels,
    currentRun,
    runHistory,
    wsState,
    settings,
    
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
    // Actions workflow
    rerunVerification,
    forceRepair,
    exportRunReport,
    // Constantes
    WORKFLOW_PHASES
  }
})
