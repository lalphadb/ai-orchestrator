/**
 * WebSocket Client robuste avec reconnection et buffering
 * v6.2 - Support Re-verify, Force Repair, Models
 */

import { normalizeEvent } from './ws/normalizeEvent'

export class WSClient {
  constructor(options = {}) {
    this.ws = null
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = options.maxReconnectAttempts || 10
    this.reconnectDelay = options.reconnectDelay || 1000
    this.maxReconnectDelay = options.maxReconnectDelay || 30000
    this.tokenBuffers = new Map()
    this.tokenBufferTimers = new Map()
    this.tokenBufferMeta = new Map()
    this.tokenBufferDelay = options.tokenBufferDelay || 50
    this.listeners = new Map()
    this.state = 'disconnected' // disconnected, connecting, connected, reconnecting
    this.pendingMessages = []
    this.lastCloseEvent = null
  }

  getDiagnostics() {
    return {
      url: this.getUrl(),
      state: this.state,
      reconnectAttempts: this.reconnectAttempts,
      lastCloseCode: this.lastCloseEvent?.code || null,
      lastCloseReason: this.lastCloseEvent?.reason || null,
      tokenPresent: !!sessionStorage.getItem('token'),
    }
  }

  getUrl() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    let url = `${protocol}//${window.location.host}/api/v1/chat/ws`
    return url
  }

  connect() {
    if (
      this.ws &&
      (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CONNECTING)
    ) {
      return
    }

    this.state = this.reconnectAttempts > 0 ? 'reconnecting' : 'connecting'
    this.emit('stateChange', this.state)

    try {
      // SECURITY: Pass JWT via Sec-WebSocket-Protocol instead of query string
      const token = sessionStorage.getItem('token')
      const protocols = token ? [`Bearer.${token}`] : []

      this.ws = new WebSocket(this.getUrl(), protocols)

      this.ws.onopen = () => {
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
        this.lastCloseEvent = event
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
    if (data?.type === 'models') {
      this.emit('models', data.data)
      return
    }

    const normalized = normalizeEvent(data)
    if (!normalized) {
      console.log('Unknown WS message type:', data?.type)
      this.emit('message', data)
      return
    }

    if (normalized.type === 'thinking' && normalized.data?.kind === 'token') {
      this._bufferTokenEvent(normalized)
      return
    }

    if ((normalized.type === 'complete' || normalized.type === 'error') && normalized.run_id) {
      this._flushTokenBuffer(normalized.run_id)
    }

    this.emit('event', normalized)
  }

  _bufferTokenEvent(event) {
    const runId = event.run_id
    if (!runId) {
      this.emit('event', event)
      return
    }

    const current = this.tokenBuffers.get(runId) || ''
    const next = current + (event.data?.content || '')
    this.tokenBuffers.set(runId, next)
    this.tokenBufferMeta.set(runId, {
      timestamp: event.timestamp,
      iteration: event.data?.iteration,
    })

    if (!this.tokenBufferTimers.has(runId)) {
      const timer = setTimeout(() => this._flushTokenBuffer(runId), this.tokenBufferDelay)
      this.tokenBufferTimers.set(runId, timer)
    }
  }

  _flushTokenBuffer(runId) {
    const buffered = this.tokenBuffers.get(runId)
    if (!buffered) {
      this._clearTokenTimer(runId)
      return
    }

    const meta = this.tokenBufferMeta.get(runId) || {}
    this.emit('event', {
      type: 'thinking',
      timestamp: meta.timestamp || new Date().toISOString(),
      run_id: runId,
      data: {
        kind: 'token',
        content: buffered,
        iteration: meta.iteration,
      },
    })

    this.tokenBuffers.delete(runId)
    this.tokenBufferMeta.delete(runId)
    this._clearTokenTimer(runId)
  }

  _clearTokenTimer(runId) {
    const timer = this.tokenBufferTimers.get(runId)
    if (timer) clearTimeout(timer)
    this.tokenBufferTimers.delete(runId)
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
      model,
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

  emit(event, ...args) {
    if (!this.listeners.has(event)) return
    this.listeners.get(event).forEach((cb) => {
      try {
        cb(...args)
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
