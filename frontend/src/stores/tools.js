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
    tools.value.forEach((t) => {
      if (t.category) cats.add(t.category)
    })
    return Array.from(cats)
  })

  const filteredTools = computed(() => {
    let result = tools.value

    if (selectedCategory.value !== 'all') {
      result = result.filter((t) => t.category === selectedCategory.value)
    }

    if (searchQuery.value) {
      const q = searchQuery.value.toLowerCase()
      result = result.filter(
        (t) => t.name?.toLowerCase().includes(q) || t.description?.toLowerCase().includes(q)
      )
    }

    return result
  })

  const toolsByCategory = computed(() => {
    const grouped = {}
    tools.value.forEach((t) => {
      const cat = t.category || 'Autres'
      if (!grouped[cat]) grouped[cat] = []
      grouped[cat].push(t)
    })
    return grouped
  })

  async function fetchTools() {
    loading.value = true
    try {
      const data = await api.getTools()
      tools.value = data.tools || data || []
    } catch (e) {
      console.error('Failed to fetch tools:', e)
    } finally {
      loading.value = false
    }
  }

  async function fetchTool(name) {
    loading.value = true
    try {
      selectedTool.value = await api.getTool(name)
    } catch (e) {
      console.error('Failed to fetch tool:', e)
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
      return result
    } catch (e) {
      executionResult.value = {
        success: false,
        error: e.message,
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
