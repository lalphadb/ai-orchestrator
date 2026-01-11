import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/services/api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || null)
  const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
  const loading = ref(false)
  const error = ref(null)
  
  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.is_admin || false)
  
  async function login(username, password) {
    loading.value = true
    error.value = null
    
    try {
      const data = await api.login(username, password)
      
      token.value = data.access_token
      user.value = data.user
      
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('user', JSON.stringify(data.user))
      
      return data
    } catch (e) {
      error.value = e.message
      throw e
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
      
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('user', JSON.stringify(data.user))
      
      return data
    } catch (e) {
      error.value = e.message
      throw e
    } finally {
      loading.value = false
    }
  }
  
  async function checkSession() {
    if (!token.value) return false
    
    try {
      const data = await api.getMe()
      user.value = data
      localStorage.setItem('user', JSON.stringify(data))
      return true
    } catch (e) {
      // Token invalid, logout
      logout()
      return false
    }
  }
  
  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }
  
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
    logout
  }
})
