<!-- components/ui/ChatInput.vue -->
<template>
  <div class="chat-input-container">
    <div class="chat-input">
      <div class="chat-input__avatar">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
          <circle cx="12" cy="7" r="4"></circle>
        </svg>
      </div>
      <div class="chat-input__wrapper">
        <textarea
          ref="textareaRef"
          v-model="inputValue"
          class="chat-input__textarea"
          :placeholder="placeholder"
          rows="1"
          @keydown="handleKeydown"
          @input="adjustHeight"
        />
        <div class="chat-input__actions">
          <button
            class="chat-input__send-button"
            :disabled="!inputValue.trim() || props.disabled || props.loading"
            @click="handleSubmit"
          >
            <svg v-if="props.loading" class="spinner" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, computed } from 'vue'

const props = defineProps({
  placeholder: {
    type: String,
    default: 'Tapez votre message...'
  },
  sending: {
    type: Boolean,
    default: false
  },
  disabled: {
    type: Boolean,
    default: false
  },
  loading: {
    type: Boolean,
    default: false
  },
  submitOnEnter: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['submit'])

const modelValue = defineModel('modelValue', { type: String, default: '' })

const inputValue = computed({
  get() {
    return modelValue.value
  },
  set(value) {
    modelValue.value = value
  }
})
const textareaRef = ref(null)

const adjustHeight = () => {
  const el = textareaRef.value
  if (el) {
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 150) + 'px'
  }
}

const handleSubmit = () => {
  if (inputValue.value.trim() && !props.disabled && !props.loading) {
    emit('submit', inputValue.value)
    // Only clear if not loading (to preserve user input during processing)
    if (!props.loading) {
      inputValue.value = ''
      adjustHeight()
    }
  }
}

const handleKeydown = (e) => {
  if (e.key === 'Enter' && !e.shiftKey && props.submitOnEnter) {
    e.preventDefault()
    handleSubmit()
  }
}

// Adjust height on mount
nextTick(() => {
  adjustHeight()
})
</script>

<style scoped>
.chat-input-container {
  padding: var(--space-4);
  background: var(--bg-surface);
  border-top: 1px solid var(--border-default);
}

.chat-input {
  display: flex;
  gap: var(--space-3);
  align-items: flex-end;
}

.chat-input__avatar {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-full);
  background: var(--accent-primary-gradient);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-on-accent);
  flex-shrink: 0;
}

.chat-input__wrapper {
  flex: 1;
  position: relative;
  display: flex;
  background: var(--bg-glass);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-xl);
  overflow: hidden;
  backdrop-filter: blur(10px);
}

.chat-input__textarea {
  flex: 1;
  padding: var(--space-4);
  padding-right: 50px;
  border: none;
  background: transparent;
  color: var(--text-primary);
  font-family: var(--font-sans);
  font-size: var(--text-base);
  resize: none;
  outline: none;
  max-height: 150px;
  min-height: 40px;
}

.chat-input__textarea::placeholder {
  color: var(--text-tertiary);
}

.chat-input__actions {
  position: absolute;
  right: var(--space-2);
  bottom: var(--space-2);
  display: flex;
  gap: var(--space-1);
}

.chat-input__send-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: var(--radius-full);
  background: var(--accent-primary-gradient);
  border: none;
  color: var(--text-on-accent);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.chat-input__send-button:hover:not(:disabled) {
  transform: scale(1.05);
  box-shadow: var(--accent-glow-medium);
}

.chat-input__send-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.spinner {
  width: 20px;
  height: 20px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>