import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useChatStore } from '@/stores/chat'

describe('Chat Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('initializes with empty state', () => {
    const store = useChatStore()
    expect(store.conversations).toEqual([])
    expect(store.currentConversation).toBeNull()
    expect(store.isLoading).toBe(false)
  })

  it('sets current model', () => {
    const store = useChatStore()
    store.currentModel = 'mistral:latest'
    expect(store.currentModel).toBe('mistral:latest')
  })

  it('tracks streaming state', () => {
    const store = useChatStore()
    expect(store.isStreaming).toBe(false)

    store.isStreaming = true
    expect(store.isStreaming).toBe(true)
  })

  it('manages WebSocket state', () => {
    const store = useChatStore()
    expect(store.wsState).toBe('disconnected')

    store.wsState = 'connected'
    expect(store.wsState).toBe('connected')
  })

  it('creates new conversation with message', () => {
    const store = useChatStore()

    // Simuler création conversation
    const newConv = {
      id: '123',
      title: 'Test Conversation',
      messages: []
    }

    store.conversations.push(newConv)
    expect(store.conversations).toHaveLength(1)
    expect(store.conversations[0].id).toBe('123')
  })

  it('selects conversation by ID', () => {
    const store = useChatStore()

    store.conversations = [
      { id: '1', title: 'Conv 1', messages: [] },
      { id: '2', title: 'Conv 2', messages: [] }
    ]

    store.currentConversation = store.conversations[0]
    expect(store.currentConversation?.id).toBe('1')
  })

  it('exports conversation as JSON', () => {
    const store = useChatStore()

    store.currentConversation = {
      id: '1',
      title: 'Test',
      messages: [
        { role: 'user', content: 'Hello' },
        { role: 'assistant', content: 'Hi!' }
      ]
    }

    const json = store.exportConversation('json')
    expect(json).toBeTruthy()

    const parsed = JSON.parse(json)
    expect(parsed.title).toBe('Test')
    expect(parsed.messages).toHaveLength(2)
  })
})
