<!-- components/ui/Toast.vue -->
<template>
  <div
    class="toast"
    :class="[`toast--${type}`, { 'toast--visible': visible }]"
    :aria-live="type === 'error' ? 'assertive' : 'polite'"
    role="alert"
  >
    <div class="toast__icon">
      <svg v-if="type === 'success'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
      </svg>
      <svg v-else-if="type === 'error'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M6 18L18 6M6 6l12 12"
        />
      </svg>
      <svg v-else-if="type === 'warning'" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.464 0L4.34 16c-.77.833.192 2.5 1.732 2.5z"
        />
      </svg>
      <svg v-else fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
    </div>
    <div class="toast__content">
      <div class="toast__title">{{ title }}</div>
      <div v-if="description" class="toast__description">{{ description }}</div>
    </div>
    <button class="toast__close" @click="close">
      <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M6 18L18 6M6 6l12 12"
        />
      </svg>
    </button>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'

const props = defineProps({
  type: {
    type: String,
    default: 'info',
    validator: (v) => ['success', 'error', 'warning', 'info'].includes(v),
  },
  title: {
    type: String,
    required: true,
  },
  description: {
    type: String,
    default: null,
  },
  duration: {
    type: Number,
    default: 5000,
  },
  visible: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['close'])

const close = () => {
  emit('close')
}

let timeoutId = null

onMounted(() => {
  if (props.duration > 0) {
    timeoutId = setTimeout(() => {
      close()
    }, props.duration)
  }
})

// Cleanup timeout on unmount
onUnmounted(() => {
  if (timeoutId) {
    clearTimeout(timeoutId)
  }
})
</script>

<script>
import { onUnmounted } from 'vue'
</script>

<style scoped>
.toast {
  position: fixed;
  top: var(--space-6);
  right: var(--space-6);
  z-index: var(--z-toast);
  min-width: 320px;
  max-width: 400px;
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  padding: var(--space-4);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  opacity: 0;
  transform: translateX(100%);
  transition: all var(--transition-normal);
  background: var(--bg-surface);
  border-left: 4px solid;
}

.toast--visible {
  opacity: 1;
  transform: translateX(0);
}

.toast--success {
  border-left-color: var(--color-success);
}

.toast--error {
  border-left-color: var(--color-error);
}

.toast--warning {
  border-left-color: var(--color-warning);
}

.toast--info {
  border-left-color: var(--accent-primary);
}

.toast__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-md);
  flex-shrink: 0;
}

.toast--success .toast__icon {
  background: var(--color-success-bg);
  color: var(--color-success);
}

.toast--error .toast__icon {
  background: var(--color-error-bg);
  color: var(--color-error);
}

.toast--warning .toast__icon {
  background: var(--color-warning-bg);
  color: var(--color-warning);
}

.toast--info .toast__icon {
  background: var(--accent-primary-gradient);
  color: var(--text-on-accent);
}

.toast__content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.toast__title {
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.toast__description {
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.toast__close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  border-radius: var(--radius-md);
  background: transparent;
  border: none;
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.toast__close:hover {
  background: var(--bg-surface-hover);
  color: var(--text-secondary);
}

@media (max-width: 768px) {
  .toast {
    left: var(--space-4);
    right: var(--space-4);
    min-width: auto;
  }
}
</style>
