/**
 * WebSocket Client robuste avec reconnection et buffering
 */

export class WSClient {
  constructor(options = {}) {
    this.ws = null
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = options.maxReconnectAttempts || 10
    this.reconnectDelay = options.reconnectDelay || 1000
    this.maxReconnectDelay = options.maxReconnectDelay || 30000
    this.tokenBuffer = ''
    this.tokenBufferTimeout = null
    this.tokenBufferDelay = options.tokenBufferDelay || 50
    this.listeners = new Map()
    this.state = 'disconnected' // disconnected, connecting, connected, reconnecting
    this.pendingMessages = []
  }
  
  getUrl() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const token = localStorage.getItem('token')
    let url = `${protocol}//${window.location.host}/api/v1/chat/ws`
    if (token) {
      url += `?token=${token}`
    }
    return url
  }
  
  connect() {
    if (this.ws && (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)) {
      return
    }
    
    this.state = this.reconnectAttempts > 0 ? 'reconnecting' : 'connecting'
    this.emit('stateChange', this.state)
    
    try {
      this.ws = new WebSocket(this.getUrl())
      
      this.ws.onopen = () => {
        console.log('🔌 WebSocket connected')
        this.state = 'connected'
        this.reconnectAttempts = 0
        this.emit('stateChange', this.state)
        this.emit('connected')
        
        // Send pending messages
        while (this.pendingMessages.length > 0) {
          const msg = this.pendingMessages.shift()
          this.send(msg)
        }
      }
      
      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          this.handleMessage(data)
        } catch (e) {
          console.error('Failed to parse WS message:', e)
        }
      }
      
      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        this.emit('error', error)
      }
      
      this.ws.onclose = (event) => {
        console.log('🔌 WebSocket closed:', event.code, event.reason)
        this.state = 'disconnected'
        this.emit('stateChange', this.state)
        this.emit('disconnected', event)
        
        // Auto-reconnect if not intentional close
        if (event.code !== 1000) {
          this.scheduleReconnect()
        }
      }
    } catch (error) {
      console.error('Failed to create WebSocket:', error)
      this.scheduleReconnect()
    }
  }
  
  scheduleReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnect attempts reached')
      this.emit('maxReconnectReached')
      return
    }
    
    const delay = Math.min(
      this.reconnectDelay * Math.pow(2, this.reconnectAttempts),
      this.maxReconnectDelay
    )
    
    this.reconnectAttempts++
    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`)
    
    setTimeout(() => this.connect(), delay)
  }
  
  handleMessage(data) {
    switch (data.type) {
      case 'token':
        // Buffer tokens to reduce re-renders
        this.tokenBuffer += data.data
        if (!this.tokenBufferTimeout) {
          this.tokenBufferTimeout = setTimeout(() => {
            this.emit('tokens', this.tokenBuffer)
            this.tokenBuffer = ''
            this.tokenBufferTimeout = null
          }, this.tokenBufferDelay)
        }
        break
        
      case 'thinking':
        this.emit('thinking', data.data)
        break
        
      case 'tool':
        this.emit('tool', data.data)
        break
        
      case 'complete':
        // Flush any remaining tokens
        if (this.tokenBuffer) {
          this.emit('tokens', this.tokenBuffer)
          this.tokenBuffer = ''
        }
        if (this.tokenBufferTimeout) {
          clearTimeout(this.tokenBufferTimeout)
          this.tokenBufferTimeout = null
        }
        this.emit('complete', data.data)
        break
        
      case 'error':
        this.emit('error', data.data)
        break
        
      case 'conversation_created':
        this.emit('conversationCreated', data.data)
        break
        
      default:
        this.emit('message', data)
    }
  }
  
  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
      return true
    } else {
      // Queue message for when connected
      this.pendingMessages.push(data)
      // Try to reconnect if disconnected
      if (this.state === 'disconnected') {
        this.connect()
      }
      return false
    }
  }
  
  sendMessage(message, conversationId, model) {
    return this.send({
      message,
      conversation_id: conversationId,
      model
    })
  }
  
  disconnect() {
    if (this.ws) {
      this.ws.close(1000, 'User disconnect')
      this.ws = null
    }
    this.state = 'disconnected'
    this.reconnectAttempts = this.maxReconnectAttempts // Prevent auto-reconnect
  }
  
  // Event emitter methods
  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, [])
    }
    this.listeners.get(event).push(callback)
    return () => this.off(event, callback)
  }
  
  off(event, callback) {
    if (!this.listeners.has(event)) return
    const callbacks = this.listeners.get(event)
    const index = callbacks.indexOf(callback)
    if (index > -1) {
      callbacks.splice(index, 1)
    }
  }
  
  emit(event, data) {
    if (!this.listeners.has(event)) return
    this.listeners.get(event).forEach(cb => {
      try {
        cb(data)
      } catch (e) {
        console.error(`Error in WS event handler for ${event}:`, e)
      }
    })
  }
  
  get isConnected() {
    return this.ws && this.ws.readyState === WebSocket.OPEN
  }
}

// Singleton instance
export const wsClient = new WSClient()
export default wsClient
