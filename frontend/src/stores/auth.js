import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { jwtDecode } from 'jwt-decode'
import api from '@/services/api'

export const useAuthStore = defineStore('auth', () => {
  // SECURITY: Use sessionStorage instead of localStorage (expires on browser close)
  const token = ref(sessionStorage.getItem('token') || null)
  const refreshToken = ref(sessionStorage.getItem('refresh_token') || null) // CRQ-2026-0203-001
  const user = ref(JSON.parse(sessionStorage.getItem('user') || 'null'))
  const loading = ref(false)
  const error = ref(null)
  const sessionExpiring = ref(false) // CRQ-2026-0203-001: Notification state
  const autoRefreshTimer = ref(null) // CRQ-2026-0203-001: Timer for auto-refresh

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
      refreshToken.value = data.refresh_token // CRQ-2026-0203-001
      user.value = data.user

      // SECURITY: Use sessionStorage (expires on browser close)
      sessionStorage.setItem('token', data.access_token)
      sessionStorage.setItem('refresh_token', data.refresh_token) // CRQ-2026-0203-001
      sessionStorage.setItem('user', JSON.stringify(data.user))

      // CRQ-2026-0203-001: Setup auto-refresh on login
      setupAutoRefresh()

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
      refreshToken.value = data.refresh_token // CRQ-2026-0203-001
      user.value = data.user

      // SECURITY: Use sessionStorage (expires on browser close)
      sessionStorage.setItem('token', data.access_token)
      sessionStorage.setItem('refresh_token', data.refresh_token) // CRQ-2026-0203-001
      sessionStorage.setItem('user', JSON.stringify(data.user))

      // CRQ-2026-0203-001: Setup auto-refresh on register
      setupAutoRefresh()

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
    // CRQ-2026-0203-001: Clear auto-refresh timer
    if (autoRefreshTimer.value) {
      clearTimeout(autoRefreshTimer.value)
      autoRefreshTimer.value = null
    }

    token.value = null
    refreshToken.value = null // CRQ-2026-0203-001
    user.value = null
    sessionExpiring.value = false // CRQ-2026-0203-001
    sessionStorage.removeItem('token')
    sessionStorage.removeItem('refresh_token') // CRQ-2026-0203-001
    sessionStorage.removeItem('user')
  }

  /**
   * CRQ-2026-0203-001: Refresh the access token using the refresh token
   */
  async function refreshSession() {
    if (!refreshToken.value) {
      console.warn('[Auth] No refresh token available')
      sessionExpiring.value = true
      return false
    }

    try {
      console.log('[Auth] Refreshing access token...')
      const data = await api.refreshToken(refreshToken.value)

      // Update tokens
      token.value = data.access_token
      refreshToken.value = data.refresh_token

      sessionStorage.setItem('token', data.access_token)
      sessionStorage.setItem('refresh_token', data.refresh_token)

      // Clear expiring warning
      sessionExpiring.value = false

      // Setup next refresh
      setupAutoRefresh()

      console.log('[Auth] Access token refreshed successfully')
      return true
    } catch (err) {
      console.error('[Auth] Failed to refresh token:', err)
      sessionExpiring.value = true

      // If refresh fails, user needs to login again
      // Don't auto-logout immediately, let user see the warning
      return false
    }
  }

  /**
   * CRQ-2026-0203-001: Setup auto-refresh timer
   * Refreshes token 2 minutes before expiration
   */
  function setupAutoRefresh() {
    // Clear existing timer
    if (autoRefreshTimer.value) {
      clearTimeout(autoRefreshTimer.value)
      autoRefreshTimer.value = null
    }

    if (!token.value || isTokenExpired(token.value)) {
      return
    }

    try {
      const decoded = jwtDecode(token.value)
      const expiresIn = decoded.exp * 1000 - Date.now()

      // Refresh 2 minutes before expiration (or immediately if < 2 min left)
      const refreshIn = Math.max(0, expiresIn - 120000) // 2 minutes = 120000ms

      console.log(`[Auth] Auto-refresh scheduled in ${Math.round(refreshIn / 1000)}s`)

      autoRefreshTimer.value = setTimeout(async () => {
        console.log('[Auth] Auto-refresh triggered')
        const success = await refreshSession()

        if (!success) {
          // Show warning that session is expiring
          sessionExpiring.value = true
          console.warn('[Auth] Session expiring - user needs to refresh manually or login')
        }
      }, refreshIn)
    } catch (err) {
      console.error('[Auth] Failed to setup auto-refresh:', err)
    }
  }

  // CRQ-2026-0203-001: Setup auto-refresh on store initialization if token exists
  watch(
    token,
    (newToken) => {
      if (newToken && !isTokenExpired(newToken)) {
        setupAutoRefresh()
      }
    },
    { immediate: true }
  )

  return {
    token,
    refreshToken, // CRQ-2026-0203-001
    user,
    loading,
    error,
    sessionExpiring, // CRQ-2026-0203-001
    isAuthenticated,
    isAdmin,
    login,
    register,
    checkSession,
    refreshSession, // CRQ-2026-0203-001
    logout,
    isTokenExpired,
  }
})
