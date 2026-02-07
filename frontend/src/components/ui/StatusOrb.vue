<!-- components/ui/StatusOrb.vue -->
<template>
  <div
    class="status-orb"
    :class="[
      `status-orb--${status}`,
      `status-orb--${size}`,
      { 'status-orb--pulse': pulse }
    ]"
  >
    <span class="status-orb__core" />
    <span v-if="pulse" class="status-orb__ring" />
    <span v-if="label" class="status-orb__label">{{ label }}</span>
  </div>
</template>

<script setup>
defineProps({
  status: {
    type: String,
    default: 'default',
    validator: (v) => ['default', 'active', 'success', 'warning', 'error', 'processing'].includes(v)
  },
  size: {
    type: String,
    default: 'md',
    validator: (v) => ['sm', 'md', 'lg'].includes(v)
  },
  pulse: Boolean,
  label: String,
})
</script>

<style scoped>
.status-orb {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
}

.status-orb__core {
  position: relative;
  border-radius: 50%;
  transition: all var(--transition-normal);
}

.status-orb__ring {
  position: absolute;
  border-radius: 50%;
  animation: pulse-ring 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

/* Sizes */
.status-orb--sm .status-orb__core { width: 8px; height: 8px; }
.status-orb--md .status-orb__core { width: 10px; height: 10px; }
.status-orb--lg .status-orb__core { width: 14px; height: 14px; }

.status-orb--sm .status-orb__ring { width: 16px; height: 16px; top: -4px; left: -4px; }
.status-orb--md .status-orb__ring { width: 20px; height: 20px; top: -5px; left: -5px; }
.status-orb--lg .status-orb__ring { width: 28px; height: 28px; top: -7px; left: -7px; }

/* Status colors */
.status-orb--active .status-orb__core,
.status-orb--success .status-orb__core {
  background: var(--color-success);
  box-shadow: 0 0 12px var(--color-success);
}

.status-orb--active .status-orb__ring,
.status-orb--success .status-orb__ring {
  border: 2px solid var(--color-success);
}

.status-orb--processing .status-orb__core {
  background: var(--accent-primary);
  box-shadow: 0 0 12px var(--accent-primary);
}

.status-orb--processing .status-orb__ring {
  border: 2px solid var(--accent-primary);
}

.status-orb--error .status-orb__core {
  background: var(--color-error);
  box-shadow: 0 0 12px var(--color-error);
}

.status-orb--error .status-orb__ring {
  border: 2px solid var(--color-error);
}

.status-orb--warning .status-orb__core {
  background: var(--color-warning);
  box-shadow: 0 0 12px var(--color-warning);
}

.status-orb--default .status-orb__core {
  background: var(--text-muted);
}

/* Label */
.status-orb__label {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--text-secondary);
}

.status-orb--active .status-orb__label,
.status-orb--success .status-orb__label { color: var(--color-success); }
.status-orb--error .status-orb__label { color: var(--color-error); }
.status-orb--processing .status-orb__label { color: var(--accent-primary); }
.status-orb--warning .status-orb__label { color: var(--color-warning); }

/* Pulse animation */
@keyframes pulse-ring {
  0% {
    transform: scale(0.8);
    opacity: 1;
  }
  100% {
    transform: scale(1.5);
    opacity: 0;
  }
}
</style>