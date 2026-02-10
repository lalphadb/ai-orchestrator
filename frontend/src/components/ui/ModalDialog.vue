<!-- components/ui/ModalDialog.vue -->
<template>
  <Teleport to="body">
    <div v-if="isOpen" class="modal-overlay" @click="closeOnOverlayClick ? closeModal() : null">
      <div class="modal-dialog" :class="`modal-dialog--${size}`" @click.stop>
        <div class="modal-header">
          <slot name="header">
            <h2 class="modal-title">{{ title }}</h2>
          </slot>
          <button class="modal-close" @click="closeModal">
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>

        <div class="modal-body">
          <slot />
        </div>

        <div v-if="$slots.footer" class="modal-footer">
          <slot name="footer" />
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { onMounted, onUnmounted } from 'vue'

const props = defineProps({
  isOpen: {
    type: Boolean,
    default: false,
  },
  title: {
    type: String,
    default: '',
  },
  size: {
    type: String,
    default: 'md', // sm, md, lg, xl
    validator: (v) => ['sm', 'md', 'lg', 'xl'].includes(v),
  },
  closeOnOverlayClick: {
    type: Boolean,
    default: true,
  },
})

const emit = defineEmits(['close'])

const closeModal = () => {
  emit('close')
}

const handleEscape = (e) => {
  if (e.key === 'Escape' && props.isOpen) {
    closeModal()
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleEscape)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleEscape)
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  animation: fadeIn 0.3s ease-out;
}

.modal-dialog {
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-xl);
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  animation: slideUp 0.3s ease-out;
}

.modal-dialog--sm {
  width: 400px;
  max-width: 90vw;
}

.modal-dialog--md {
  width: 500px;
  max-width: 90vw;
}

.modal-dialog--lg {
  width: 700px;
  max-width: 90vw;
}

.modal-dialog--xl {
  width: 900px;
  max-width: 95vw;
  height: 80vh;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-6);
  border-bottom: 1px solid var(--border-default);
}

.modal-title {
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.modal-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-md);
  background: transparent;
  border: none;
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.modal-close:hover {
  background: var(--bg-surface-hover);
  color: var(--text-secondary);
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: var(--space-6);
}

.modal-footer {
  padding: var(--space-6);
  border-top: 1px solid var(--border-default);
  display: flex;
  justify-content: flex-end;
  gap: var(--space-3);
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (max-width: 768px) {
  .modal-dialog {
    width: 95vw;
    max-height: 90vh;
  }

  .modal-header,
  .modal-body,
  .modal-footer {
    padding: var(--space-4);
  }
}
</style>
