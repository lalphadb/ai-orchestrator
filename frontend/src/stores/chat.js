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
  
  // Run Session (traçabilité ReAct)
  const currentRun = ref(null)
  const runHistory = ref([])
  
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
    wsClient.on('stateChange', (state) => {
      wsState.value = state
    })
    
    wsClient.on('thinking', (data) => {
      if (currentRun.value) {
        currentRun.value.thinking.push({
          message: data.message,
          iteration: data.iteration,
          timestamp: Date.now()
        })
        currentRun.value.currentPhase = 'thinking'
        currentRun.value.currentIteration = data.iteration
      }
    })
    
    wsClient.on('tool', (data) => {
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
    
    wsClient.on('complete', (data) => {
      if (currentRun.value) {
        currentRun.value.complete = data
        currentRun.value.currentPhase = 'complete'
        currentRun.value.endTime = Date.now()
        currentRun.value.duration = currentRun.value.endTime - currentRun.value.startTime
        
        // Finalize message
        finalizeMessage(data)
        
        // Archive run
        runHistory.value.unshift({ ...currentRun.value })
        if (runHistory.value.length > 50) {
          runHistory.value.pop()
        }
      }
      isLoading.value = false
    })
    
    wsClient.on('error', (error) => {
      if (currentRun.value) {
        currentRun.value.error = error
        currentRun.value.currentPhase = 'error'
      }
      addErrorMessage(typeof error === 'string' ? error : error.message || 'Erreur inconnue')
      isLoading.value = false
    })
    
    wsClient.on('conversationCreated', (data) => {
      currentConversation.value = { id: data.id, title: data.title }
      fetchConversations()
    })
    
    wsClient.connect()
  }
  
  function updateStreamingMessage(content) {
    const lastMsg = messages.value[messages.value.length - 1]
    if (lastMsg && lastMsg.role === 'assistant' && lastMsg.streaming) {
      lastMsg.content = content
    }
  }
  
  function finalizeMessage(data) {
    const lastMsg = messages.value[messages.value.length - 1]
    if (lastMsg && lastMsg.role === 'assistant') {
      lastMsg.content = data.response
      lastMsg.streaming = false
      lastMsg.tools_used = data.tools_used
      lastMsg.iterations = data.iterations
      lastMsg.duration_ms = data.duration_ms
      lastMsg.model = data.model_used
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
    
    // Create new run session
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
      model: currentModel.value
    }
    
    isLoading.value = true
    
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
        currentRun.value.endTime = Date.now()
      }
    } catch (e) {
      addErrorMessage(e.message)
      if (currentRun.value) {
        currentRun.value.error = e.message
        currentRun.value.currentPhase = 'error'
      }
    } finally {
      isLoading.value = false
    }
  }
  
  async function retryLastMessage() {
    if (messages.value.length < 2) return
    
    // Find last user message
    let lastUserMsgIndex = -1
    for (let i = messages.value.length - 1; i >= 0; i--) {
      if (messages.value[i].role === 'user') {
        lastUserMsgIndex = i
        break
      }
    }
    
    if (lastUserMsgIndex === -1) return
    
    const content = messages.value[lastUserMsgIndex].content
    
    // Remove messages after (and including) last user message
    messages.value = messages.value.slice(0, lastUserMsgIndex)
    
    // Resend
    await sendMessage(content)
  }
  
  async function fetchModels() {
    try {
      const data = await api.getModels()
      availableModels.value = data.models || []
      if (data.default_model && !localStorage.getItem('preferredModel')) {
        currentModel.value = data.default_model
      }
    } catch (e) {
      console.error('Failed to fetch models:', e)
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
    setModel,
    newConversation,
    updateSettings,
    exportConversation
  }
})
