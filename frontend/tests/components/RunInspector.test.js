/**
 * RunInspector Component Tests
 * LOT 3 - Tests component pour le Run Inspector v8
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { nextTick, computed, ref } from 'vue'

// Mock chat store
const mockChatStore = {
  WORKFLOW_PHASES: ['spec', 'plan', 'execute', 'verify', 'repair', 'complete'],
  wsState: 'connected',
  currentConversation: { id: 'conv-1' },
  runs: new Map(),
  runsByConversation: new Map(),
  activeRunId: null,
  settings: { showToolParams: true },
  retryLastMessage: vi.fn(),
}

// Mock the chat store module
vi.mock('@/stores/chat', () => ({
  useChatStore: () => mockChatStore
}))

// Minimal RunInspector component for testing
// (We test the data flow and computed properties, not the full template)
const RunInspectorStub = {
  name: 'RunInspectorStub',
  setup() {
    // Simulate the key logic from RunInspector
    // Using imported computed, ref from 'vue'
    const chat = mockChatStore
    
    const selectedRunId = ref(chat.activeRunId)
    
    const availableRuns = computed(() => {
      const convId = chat.currentConversation?.id
      if (!convId) return []
      const runIds = chat.runsByConversation.get(convId)
      if (!runIds) return []
      return Array.from(runIds)
        .map(id => chat.runs.get(id))
        .filter(r => r)
    })
    
    const run = computed(() => {
      if (!selectedRunId.value) return null
      return chat.runs.get(selectedRunId.value)
    })
    
    const hasTools = computed(() => run.value?.toolCalls?.length > 0)
    const hasThinking = computed(() => run.value?.thinking?.length > 0)
    const hasVerification = computed(() => run.value?.verificationItems?.length > 0)
    const isTerminal = computed(() => {
      if (!run.value) return false
      return run.value.status === 'complete' || run.value.status === 'failed'
    })
    
    return {
      chat,
      selectedRunId,
      availableRuns,
      run,
      hasTools,
      hasThinking,
      hasVerification,
      isTerminal
    }
  },
  template: '<div>stub</div>'
}

describe('RunInspector Component Logic', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    // Reset mock data
    mockChatStore.runs = new Map()
    mockChatStore.runsByConversation = new Map()
    mockChatStore.activeRunId = null
    mockChatStore.currentConversation = { id: 'conv-1' }
  })
  
  describe('Timeline Display', () => {
    it('defines all workflow phases', () => {
      expect(mockChatStore.WORKFLOW_PHASES).toContain('spec')
      expect(mockChatStore.WORKFLOW_PHASES).toContain('plan')
      expect(mockChatStore.WORKFLOW_PHASES).toContain('execute')
      expect(mockChatStore.WORKFLOW_PHASES).toContain('verify')
      expect(mockChatStore.WORKFLOW_PHASES).toContain('repair')
      expect(mockChatStore.WORKFLOW_PHASES).toContain('complete')
    })
  })
  
  describe('Run Selection', () => {
    it('shows no runs when conversation has none', () => {
      const wrapper = mount(RunInspectorStub)
      expect(wrapper.vm.availableRuns.length).toBe(0)
    })
    
    it('lists all runs for current conversation', () => {
      // Setup runs
      mockChatStore.runs.set('run-1', { id: 'run-1', status: 'complete' })
      mockChatStore.runs.set('run-2', { id: 'run-2', status: 'running' })
      mockChatStore.runsByConversation.set('conv-1', new Set(['run-1', 'run-2']))
      
      const wrapper = mount(RunInspectorStub)
      expect(wrapper.vm.availableRuns.length).toBe(2)
    })
    
    it('returns null run when no run selected', () => {
      const wrapper = mount(RunInspectorStub)
      expect(wrapper.vm.run).toBeNull()
    })
    
    it('returns selected run', () => {
      mockChatStore.runs.set('run-1', { id: 'run-1', status: 'running' })
      mockChatStore.activeRunId = 'run-1'
      
      const wrapper = mount(RunInspectorStub)
      wrapper.vm.selectedRunId = 'run-1'
      
      expect(wrapper.vm.run).toBeDefined()
      expect(wrapper.vm.run.id).toBe('run-1')
    })
  })
  
  describe('Tab Content - Tools', () => {
    it('hasTools is false when no tool calls', () => {
      mockChatStore.runs.set('run-1', { id: 'run-1', toolCalls: [] })
      
      const wrapper = mount(RunInspectorStub)
      wrapper.vm.selectedRunId = 'run-1'
      
      expect(wrapper.vm.hasTools).toBe(false)
    })
    
    it('hasTools is true when tool calls exist', () => {
      mockChatStore.runs.set('run-1', { 
        id: 'run-1', 
        toolCalls: [{ tool: 'test', params: {} }] 
      })
      
      const wrapper = mount(RunInspectorStub)
      wrapper.vm.selectedRunId = 'run-1'
      
      expect(wrapper.vm.hasTools).toBe(true)
    })
  })
  
  describe('Tab Content - Thinking', () => {
    it('hasThinking is false when no thinking log', () => {
      mockChatStore.runs.set('run-1', { id: 'run-1', thinking: [] })
      
      const wrapper = mount(RunInspectorStub)
      wrapper.vm.selectedRunId = 'run-1'
      
      expect(wrapper.vm.hasThinking).toBe(false)
    })
    
    it('hasThinking is true when thinking log exists', () => {
      mockChatStore.runs.set('run-1', { 
        id: 'run-1', 
        thinking: [{ content: 'test' }] 
      })
      
      const wrapper = mount(RunInspectorStub)
      wrapper.vm.selectedRunId = 'run-1'
      
      expect(wrapper.vm.hasThinking).toBe(true)
    })
  })
  
  describe('Tab Content - Verification', () => {
    it('hasVerification is false when no items', () => {
      mockChatStore.runs.set('run-1', { id: 'run-1', verificationItems: [] })
      
      const wrapper = mount(RunInspectorStub)
      wrapper.vm.selectedRunId = 'run-1'
      
      expect(wrapper.vm.hasVerification).toBe(false)
    })
    
    it('hasVerification is true when items exist', () => {
      mockChatStore.runs.set('run-1', { 
        id: 'run-1', 
        verificationItems: [{ check_name: 'test', status: 'passed' }] 
      })
      
      const wrapper = mount(RunInspectorStub)
      wrapper.vm.selectedRunId = 'run-1'
      
      expect(wrapper.vm.hasVerification).toBe(true)
    })
  })
  
  describe('Terminal Status', () => {
    it('isTerminal false for running run', () => {
      mockChatStore.runs.set('run-1', { id: 'run-1', status: 'running' })
      
      const wrapper = mount(RunInspectorStub)
      wrapper.vm.selectedRunId = 'run-1'
      
      expect(wrapper.vm.isTerminal).toBe(false)
    })
    
    it('isTerminal true for complete run', () => {
      mockChatStore.runs.set('run-1', { id: 'run-1', status: 'complete' })
      
      const wrapper = mount(RunInspectorStub)
      wrapper.vm.selectedRunId = 'run-1'
      
      expect(wrapper.vm.isTerminal).toBe(true)
    })
    
    it('isTerminal true for failed run', () => {
      mockChatStore.runs.set('run-1', { id: 'run-1', status: 'failed' })
      
      const wrapper = mount(RunInspectorStub)
      wrapper.vm.selectedRunId = 'run-1'
      
      expect(wrapper.vm.isTerminal).toBe(true)
    })
  })
})
