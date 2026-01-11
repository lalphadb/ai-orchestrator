import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'

export const useSystemStore = defineStore('system', () => {
  const health = ref(null)
  const stats = ref(null)
  const models = ref([])
  const loading = ref(false)
  const lastCheck = ref(null)
  
  const isHealthy = computed(() => health.value?.status === 'healthy')
  const ollamaStatus = computed(() => health.value?.ollama || 'unknown')
  const dbStatus = computed(() => health.value?.database || 'unknown')
  
  async function fetchHealth() {
    try {
      health.value = await api.getHealth()
      lastCheck.value = Date.now()
    } catch (e) {
      health.value = { status: 'error', error: e.message }
    }
  }
  
  async function fetchStats() {
    loading.value = true
    try {
      stats.value = await api.getStats()
    } catch (e) {
      console.error('Failed to fetch stats:', e)
    } finally {
      loading.value = false
    }
  }
  
  async function fetchModels() {
    try {
      const data = await api.getModels()
      models.value = data.models || []
      return data
    } catch (e) {
      console.error('Failed to fetch models:', e)
      return { models: [] }
    }
  }
  
  function startHealthCheck(interval = 30000) {
    fetchHealth()
    return setInterval(fetchHealth, interval)
  }
  
  return {
    health,
    stats,
    models,
    loading,
    lastCheck,
    isHealthy,
    ollamaStatus,
    dbStatus,
    fetchHealth,
    fetchStats,
    fetchModels,
    startHealthCheck
  }
})
