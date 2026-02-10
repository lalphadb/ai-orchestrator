<!-- components/ui/GlassCard.vue -->
<template>
  <div
    class="glass-card"
    :class="[
      `glass-card--${variant}`,
      { 'glass-card--hoverable': hoverable },
      { 'glass-card--active': active },
    ]"
    @click="hoverable && $emit('click')"
  >
    <div v-if="glow" class="glass-card__glow" />
    <div v-if="$slots.header" class="glass-card__header">
      <slot name="header" />
    </div>
    <div class="glass-card__content" :class="`glass-card__content--${padding}`">
      <slot />
    </div>
  </div>
</template>

<script setup>
defineProps({
  variant: {
    type: String,
    default: 'default',
    validator: (v) => ['default', 'elevated', 'bordered', 'interactive'].includes(v),
  },
  hoverable: Boolean,
  active: Boolean,
  glow: Boolean,
  padding: {
    type: String,
    default: 'md', // default padding
    validator: (v) => ['none', 'sm', 'md', 'lg'].includes(v),
  },
})

defineEmits(['click'])
</script>

<style scoped>
.glass-card {
  position: relative;
  background: var(--bg-glass);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--bg-glass-border);
  border-radius: var(--radius-xl);
  overflow: hidden;
  transition: all var(--transition-normal);
}

.glass-card__content {
  position: relative;
  z-index: 1;
}

.glass-card__content--none {
  padding: 0;
}

.glass-card__content--sm {
  padding: var(--space-3);
}

.glass-card__content--md {
  padding: var(--space-6);
}

.glass-card__content--lg {
  padding: var(--space-8);
}

.glass-card__header {
  border-bottom: 1px solid var(--border-default);
  padding: var(--space-4) var(--space-6);
  margin-bottom: var(--space-4);
}

.glass-card__glow {
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle at center, rgba(139, 92, 246, 0.1) 0%, transparent 50%);
  opacity: 0;
  transition: opacity var(--transition-normal);
  pointer-events: none;
}

/* Variants */
.glass-card--elevated {
  box-shadow: var(--shadow-lg);
}

.glass-card--bordered {
  border: 1px solid var(--border-default);
}

.glass-card--interactive {
  cursor: pointer;
}

.glass-card--interactive:hover {
  background: var(--bg-surface-hover);
  border-color: var(--border-strong);
  transform: translateY(-2px);
  box-shadow: var(--shadow-glow);
}

/* States */
.glass-card--hoverable {
  cursor: pointer;
}

.glass-card--hoverable:hover {
  background: var(--bg-surface-hover);
  border-color: var(--border-strong);
  transform: translateY(-2px);
  box-shadow: var(--shadow-glow);
}

.glass-card--hoverable:hover .glass-card__glow {
  opacity: 1;
}

.glass-card--active {
  border-color: var(--border-accent);
  box-shadow: var(--accent-glow-medium);
}
</style>
