/**
 * API Client unifié avec gestion JWT
 */

const API_BASE = '/api/v1'

class ApiError extends Error {
  constructor(message, status, data) {
    super(message)
    this.status = status
    this.data = data
  }
}

function getToken() {
  return localStorage.getItem('token')
}

async function request(endpoint, options = {}) {
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
