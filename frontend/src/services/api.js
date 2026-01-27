/**
 * API Client unifié avec gestion JWT, retry automatique et gestion 401
 */

const API_BASE = '/api/v1'

class ApiError extends Error {
  constructor(message, status, data) {
    super(message)
    this.status = status
    this.data = data
    this.isNetworkError = !status
  }
}

function getToken() {
  return sessionStorage.getItem('token')
}

/**
 * Gère les erreurs 401 (token expiré)
 */
function handleUnauthorized() {
  // Clear auth data
  sessionStorage.removeItem('token')
  sessionStorage.removeItem('user')

  // Show toast notification
  const toastStore = window.__TOAST_STORE__
  if (toastStore) {
    toastStore.warning('Session expirée. Veuillez vous reconnecter.', 5000)
  }

  // Redirect to login after a short delay
  setTimeout(() => {
    if (window.location.pathname !== '/login') {
      window.location.href = '/login'
    }
  }, 1000)
}

/**
 * Requête avec retry automatique sur erreurs réseau + loading state global
 */
async function requestWithRetry(endpoint, options = {}, retries = 3) {
  let lastError
  let requestId = null

  // Start loading tracking
  const loadingStore = window.__LOADING_STORE__
  if (loadingStore) {
    requestId = loadingStore.startRequest(endpoint)
  }

  try {
    for (let attempt = 0; attempt < retries; attempt++) {
      try {
        const token = getToken()

        const headers = {
          'Content-Type': 'application/json',
          ...options.headers
        }

        if (token) {
          headers['Authorization'] = `Bearer ${token}`
        }

        const response = await fetch(`${API_BASE}${endpoint}`, {
          ...options,
          headers
        })

        // Handle 401 Unauthorized (token expired)
        if (response.status === 401) {
          handleUnauthorized()
          throw new ApiError('Session expirée', 401, {})
        }

        if (!response.ok) {
          let errorData = {}
          try {
            errorData = await response.json()
          } catch {}
          throw new ApiError(
            errorData.detail || `HTTP ${response.status}`,
            response.status,
            errorData
          )
        }

        // Handle empty responses
        const text = await response.text()
        return text ? JSON.parse(text) : null

      } catch (error) {
        lastError = error

        // Don't retry on client errors (4xx) except network errors
        if (error.status && error.status < 500) {
          throw error
        }

        // Don't retry on last attempt
        if (attempt === retries - 1) {
          throw error
        }

        // Retry only on server errors (5xx) or network errors
        if (error.status >= 500 || error.isNetworkError) {
          console.log(`Retry ${attempt + 1}/${retries} for ${endpoint}`)
          // Exponential backoff
          await new Promise(resolve => setTimeout(resolve, 1000 * (attempt + 1)))
          continue
        }

        throw error
      }
    }

    throw lastError
  } finally {
    // End loading tracking
    if (loadingStore && requestId) {
      loadingStore.endRequest(requestId)
    }
  }
}

// Alias for backward compatibility
async function request(endpoint, options = {}) {
  return requestWithRetry(endpoint, options, 3)
}

export const api = {
  // Méthodes génériques
  async get(endpoint) {
    return request(endpoint)
  },
  
  async post(endpoint, data) {
    return request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data)
    })
  },
  
  async put(endpoint, data) {
    return request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data)
    })
  },
  
  async patch(endpoint, data) {
    return request(endpoint, {
      method: 'PATCH',
      body: JSON.stringify(data)
    })
  },
  
  async delete(endpoint) {
    return request(endpoint, {
      method: 'DELETE'
    })
  },
  
  // Auth
  async login(username, password) {
    return request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    })
  },
  
  async register(username, password, email) {
    return request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, password, email })
    })
  },
  
  async getMe() {
    return request('/auth/me')
  },
  
  // Conversations
  async getConversations() {
    return request('/conversations')
  },
  
  async getConversation(id) {
    return request(`/conversations/${id}`)
  },
  
  async renameConversation(id, title) {
    return request(`/conversations/${id}`, {
      method: 'PATCH',
      body: JSON.stringify({ title })
    })
  },
  
  async deleteConversation(id) {
    return request(`/conversations/${id}`, {
      method: 'DELETE'
    })
  },
  
  // Chat (HTTP fallback)
  async sendMessage(message, conversationId, model) {
    return request('/chat', {
      method: 'POST',
      body: JSON.stringify({
        message,
        conversation_id: conversationId,
        model
      })
    })
  },
  
  // Tools
  async getTools() {
    return request('/tools')
  },
  
  async getTool(name) {
    return request(`/tools/${name}`)
  },
  
  async executeTool(name, params) {
    return request(`/tools/${name}/execute`, {
      method: 'POST',
      body: JSON.stringify(params)
    })
  },
  
  // System
  async getHealth() {
    return request('/system/health')
  },
  
  async getStats() {
    return request('/system/stats')
  },
  
  async getModels() {
    return request('/system/models')
  }
}

export { ApiError }
export default api
