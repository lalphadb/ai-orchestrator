import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'

export const useToolsStore = defineStore('tools', () => {
  const tools = ref([])
  const selectedTool = ref(null)
  const loading = ref(false)
  const executing = ref(false)
  const executionResult = ref(null)
  const searchQuery = ref('')
  const selectedCategory = ref('all')

  const categories = computed(() => {
    const cats = new Set(['all'])
    // CRQ-2026-0203-001 Phase 6: Safe property access with optional chaining
    tools.value?.forEach((t) => {
      if (t?.category) cats.add(t.category)
    })
    return Array.from(cats)
  })

  const filteredTools = computed(() => {
    // CRQ-2026-0203-001 Phase 6: Safe array access
    let result = tools.value ?? []

    if (selectedCategory.value !== 'all') {
      result = result.filter((t) => t?.category === selectedCategory.value)
    }

    if (searchQuery.value) {
      const q = searchQuery.value.toLowerCase()
      result = result.filter(
        (t) => t?.name?.toLowerCase().includes(q) || t?.description?.toLowerCase().includes(q)
      )
    }

    return result
  })

  const toolsByCategory = computed(() => {
    const grouped = {}
    // CRQ-2026-0203-001 Phase 6: Safe property access
    tools.value?.forEach((t) => {
      const cat = t?.category || 'Autres'
      if (!grouped[cat]) grouped[cat] = []
      grouped[cat].push(t)
    })
    return grouped
  })

  async function fetchTools() {
    loading.value = true
    try {
      const data = await api.getTools()

      // CRQ-2026-0203-001 Phase 6: Validate data structure
      if (!data) {
        console.warn('[Tools] Empty response from API')
        tools.value = []
        return
      }

      // Support both {tools: [...]} and [...] formats
      tools.value = Array.isArray(data.tools) ? data.tools : Array.isArray(data) ? data : []

      console.log(`[Tools] Loaded ${tools.value.length} tools`)
    } catch (e) {
      console.error('[Tools] Failed to fetch tools:', {
        message: e?.message,
        status: e?.status,
        data: e?.data
      })
      tools.value = []
    } finally {
      loading.value = false
    }
  }

  async function fetchTool(name) {
    loading.value = true
    try {
      const data = await api.getTool(name)

      // CRQ-2026-0203-001 Phase 6: Validate tool data
      if (!data) {
        console.warn(`[Tools] Empty response for tool ${name}`)
        selectedTool.value = null
        return
      }

      selectedTool.value = data
    } catch (e) {
      console.error(`[Tools] Failed to fetch tool ${name}:`, {
        message: e?.message,
        status: e?.status,
        data: e?.data
      })
      selectedTool.value = null
    } finally {
      loading.value = false
    }
  }

  async function executeTool(name, params) {
    executing.value = true
    executionResult.value = null

    try {
      const result = await api.executeTool(name, params)
      executionResult.value = {
        success: true,
        data: result,
      }
      console.log(`[Tools] Executed ${name} successfully`)
      return result
    } catch (e) {
      // CRQ-2026-0203-001 Phase 6: Enhanced error logging
      console.error(`[Tools] Failed to execute ${name}:`, {
        message: e?.message,
        status: e?.status,
        params,
        data: e?.data
      })
      executionResult.value = {
        success: false,
        error: e?.message || 'Unknown error',
      }
      throw e
    } finally {
      executing.value = false
    }
  }

  function clearExecutionResult() {
    executionResult.value = null
  }

  return {
    tools,
    selectedTool,
    loading,
    executing,
    executionResult,
    searchQuery,
    selectedCategory,
    categories,
    filteredTools,
    toolsByCategory,
    fetchTools,
    fetchTool,
    executeTool,
    clearExecutionResult,
  }
})
