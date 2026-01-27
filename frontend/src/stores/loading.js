/**
 * Store Pinia pour l'état de chargement global
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useLoadingStore = defineStore('loading', () => {
  const activeRequests = ref(0)
  const requestDetails = ref(new Map())

  const isLoading = computed(() => activeRequests.value > 0)

  // Enregistrer globalement pour l'API client
  if (typeof window !== 'undefined') {
    window.__LOADING_STORE__ = null
  }

  function startRequest(id = null) {
    const requestId = id || `req_${Date.now()}_${Math.random()}`
    activeRequests.value++
    requestDetails.value.set(requestId, {
      startTime: Date.now()
    })
    return requestId
  }

  function endRequest(id) {
    if (requestDetails.value.has(id)) {
      requestDetails.value.delete(id)
    }
    if (activeRequests.value > 0) {
      activeRequests.value--
    }
  }

  function reset() {
    activeRequests.value = 0
    requestDetails.value.clear()
  }

  const store = {
    activeRequests,
    isLoading,
    startRequest,
    endRequest,
    reset
  }

  // Enregistrer globalement après création
  if (typeof window !== 'undefined') {
    window.__LOADING_STORE__ = store
  }

  return store
})
