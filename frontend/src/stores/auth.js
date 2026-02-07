import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { jwtDecode } from 'jwt-decode'
import api from '@/services/api'

export const useAuthStore = defineStore('auth', () => {
  // SECURITY: Use sessionStorage instead of localStorage (expires on browser close)
  const token = ref(sessionStorage.getItem('token') || null)
  const user = ref(JSON.parse(sessionStorage.getItem('user') || 'null'))
  const loading = ref(false)
  const error = ref(null)

  const isAuthenticated = computed(() => !!token.value && !isTokenExpired(token.value))
  const isAdmin = computed(() => user.value?.is_admin || false)

  /**
   * SECURITY: Vérifie si un JWT est expiré
   */
  function isTokenExpired(token) {
    if (!token) return true

    try {
      const decoded = jwtDecode(token)
      const now = Date.now() / 1000

      // Vérifier l'expiration (avec 30s de marge)
      if (decoded.exp && decoded.exp < now + 30) {
        return true
      }

      return false
    } catch (_err) {
      console.error('Invalid token format:', _err)
      return true
    }
  }

  async function login(username, password) {
    loading.value = true
    error.value = null

    try {
      const data = await api.login(username, password)

      token.value = data.access_token
      user.value = data.user

      // SECURITY: Use sessionStorage (expires on browser close)
      sessionStorage.setItem('token', data.access_token)
      sessionStorage.setItem('user', JSON.stringify(data.user))

      return data
    } catch (_err) {
      error.value = _err.message
      throw _err
    } finally {
      loading.value = false
    }
  }

  async function register(username, password, email) {
    loading.value = true
    error.value = null

    try {
      const data = await api.register(username, password, email)

      token.value = data.access_token
      user.value = data.user

      // SECURITY: Use sessionStorage (expires on browser close)
      sessionStorage.setItem('token', data.access_token)
      sessionStorage.setItem('user', JSON.stringify(data.user))

      return data
    } catch (_err) {
      error.value = _err.message
      throw _err
    } finally {
      loading.value = false
    }
  }

  async function checkSession() {
    if (!token.value) return false

    // SECURITY: Check token expiration client-side first
    if (isTokenExpired(token.value)) {
      console.log('Token expired, logging out')
      logout()
      return false
    }

    try {
      const data = await api.getMe()
      user.value = data
      sessionStorage.setItem('user', JSON.stringify(data))
      return true
    } catch (_err) {
      // Token invalid, logout
      logout()
      return false
    }
  }

  function logout() {
    token.value = null
    user.value = null
    sessionStorage.removeItem('token')
    sessionStorage.removeItem('user')
  }

  // SECURITY: Auto-logout before token expiration
  watch(
    token,
    (newToken) => {
      if (newToken && !isTokenExpired(newToken)) {
        try {
          const decoded = jwtDecode(newToken)
          const expiresIn = decoded.exp * 1000 - Date.now()

          // Logout automatically 10s before expiration
          if (expiresIn > 10000) {
            setTimeout(() => {
              if (token.value === newToken) {
                // Check token hasn't changed
                console.log('Token about to expire, logging out')
                logout()
              }
            }, expiresIn - 10000)
          }
        } catch (_err) {
          console.error('Failed to setup auto-logout:', _err)
        }
      }
    },
    { immediate: true }
  )

  return {
    token,
    user,
    loading,
    error,
    isAuthenticated,
    isAdmin,
    login,
    register,
    checkSession,
    logout,
    isTokenExpired,
  }
})
