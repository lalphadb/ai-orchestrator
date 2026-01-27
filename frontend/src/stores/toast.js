/**
 * Store Pinia pour les notifications toast
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useToastStore = defineStore('toast', () => {
  const toasts = ref([])
  let nextId = 1

  // Enregistrer globalement pour l'API client
  if (typeof window !== 'undefined') {
    window.__TOAST_STORE__ = null
  }

  function add(message, type = 'info', duration = 5000) {
    const id = nextId++
    const toast = {
      id,
      message,
      type, // 'success', 'error', 'warning', 'info'
      duration
    }

    toasts.value.push(toast)

    // Auto-remove après duration
    if (duration > 0) {
      setTimeout(() => remove(id), duration)
    }

    return id
  }

  function remove(id) {
    const index = toasts.value.findIndex(t => t.id === id)
    if (index !== -1) {
      toasts.value.splice(index, 1)
    }
  }

  function success(message, duration = 3000) {
    return add(message, 'success', duration)
  }

  function error(message, duration = 5000) {
    return add(message, 'error', duration)
  }

  function warning(message, duration = 4000) {
    return add(message, 'warning', duration)
  }

  function info(message, duration = 3000) {
    return add(message, 'info', duration)
  }

  function clear() {
    toasts.value = []
  }

  const store = {
    toasts,
    add,
    remove,
    success,
    error,
    warning,
    info,
    clear
  }

  // Enregistrer globalement après création
  if (typeof window !== 'undefined') {
    window.__TOAST_STORE__ = store
  }

  return store
})
