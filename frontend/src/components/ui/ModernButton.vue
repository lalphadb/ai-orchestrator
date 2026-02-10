<!-- components/ui/ModernButton.vue -->
<template>
  <button
    class="modern-btn"
    :class="[
      `modern-btn--${variant}`,
      `modern-btn--${size}`,
      { 'modern-btn--loading': loading },
      { 'modern-btn--icon-only': iconOnly },
    ]"
    :disabled="disabled || loading"
    @click="$emit('click')"
  >
    <span v-if="loading" class="modern-btn__loader">
      <span></span>
      <span></span>
      <span></span>
    </span>
    <span v-else class="modern-btn__content">
      <slot name="icon-left" />
      <span v-if="!iconOnly" class="modern-btn__text">
        <slot />
      </span>
      <slot name="icon-right" />
    </span>
  </button>
</template>

<script setup>
defineProps({
  variant: {
    type: String,
    default: 'primary',
    validator: (v) => ['primary', 'secondary', 'ghost', 'danger'].includes(v),
  },
  size: {
    type: String,
    default: 'md',
    validator: (v) => ['sm', 'md', 'lg'].includes(v),
  },
  loading: Boolean,
  disabled: Boolean,
  iconOnly: Boolean,
})

defineEmits(['click'])
</script>

<style scoped>
.modern-btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  font-family: var(--font-sans);
  font-weight: var(--font-medium);
  border: none;
  cursor: pointer;
  transition: all var(--transition-fast);
  overflow: hidden;
}

/* Sizes */
.modern-btn--sm {
  height: 32px;
  padding: 0 var(--space-3);
  font-size: var(--text-sm);
  border-radius: var(--radius-md);
}

.modern-btn--md {
  height: 40px;
  padding: 0 var(--space-5);
  font-size: var(--text-sm);
  border-radius: var(--radius-lg);
}

.modern-btn--lg {
  height: 48px;
  padding: 0 var(--space-6);
  font-size: var(--text-base);
  border-radius: var(--radius-lg);
}

/* Primary */
.modern-btn--primary {
  background: var(--accent-primary-gradient);
  color: var(--text-on-accent);
  box-shadow: var(--accent-glow-soft);
}

.modern-btn--primary:hover:not(:disabled) {
  box-shadow: var(--accent-glow-medium);
  transform: translateY(-1px);
}

/* Secondary */
.modern-btn--secondary {
  background: var(--bg-surface);
  color: var(--text-primary);
  border: 1px solid var(--border-default);
}

.modern-btn--secondary:hover:not(:disabled) {
  background: var(--bg-surface-hover);
  border-color: var(--border-strong);
}

/* Ghost */
.modern-btn--ghost {
  background: transparent;
  color: var(--text-secondary);
}

.modern-btn--ghost:hover:not(:disabled) {
  background: var(--bg-surface);
  color: var(--text-primary);
}

/* Danger */
.modern-btn--danger {
  background: var(--color-error);
  color: var(--text-on-accent);
}

.modern-btn--danger:hover:not(:disabled) {
  box-shadow: var(--color-error-glow);
}

/* Loading */
.modern-btn__loader {
  display: flex;
  gap: 4px;
}

.modern-btn__loader span {
  width: 6px;
  height: 6px;
  background: currentColor;
  border-radius: 50%;
  animation: btn-loading 1.4s infinite ease-in-out both;
}

.modern-btn__loader span:nth-child(1) {
  animation-delay: -0.32s;
}
.modern-btn__loader span:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes btn-loading {
  0%,
  80%,
  100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}

/* Disabled */
.modern-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none !important;
}

/* Icon only */
.modern-btn--icon-only.modern-btn--sm {
  width: 32px;
  padding: 0;
}
.modern-btn--icon-only.modern-btn--md {
  width: 40px;
  padding: 0;
}
.modern-btn--icon-only.modern-btn--lg {
  width: 48px;
  padding: 0;
}
</style>
