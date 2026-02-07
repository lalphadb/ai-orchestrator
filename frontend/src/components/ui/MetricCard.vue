<!-- components/ui/MetricCard.vue -->
<template>
  <GlassCard class="metric-card">
    <div class="metric-card__header">
      <div class="metric-card__icon">
        <slot name="icon">
          <div v-if="icon" class="metric-card__icon-placeholder">
            <component :is="icon" v-if="typeof icon === 'object'" />
            <i v-else :class="icon" />
          </div>
        </slot>
      </div>
      <div class="metric-card__status" v-if="status">
        <StatusOrb :status="status" size="sm" />
      </div>
    </div>

    <div class="metric-card__content">
      <h3 class="metric-card__title">{{ title }}</h3>
      <div class="metric-card__value">{{ displayValue }}</div>
      <div class="metric-card__trend" v-if="trend">
        <span :class="trendClass">{{ trend }}</span>
        <svg v-if="trend.startsWith('+')" class="trend-icon up" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7" />
        </svg>
        <svg v-else class="trend-icon down" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
        </svg>
      </div>
    </div>
  </GlassCard>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  label: {
    type: String,
    required: true
  },
  value: {
    type: [String, Number],
    required: true
  },
  unit: {
    type: String,
    default: ''
  },
  color: {
    type: String,
    default: 'primary',
    validator: (v) => ['primary', 'success', 'warning', 'error', 'info'].includes(v)
  },
  icon: {
    type: [String, Object],
    default: null
  },
  trend: {
    type: String,
    default: null
  },
  status: {
    type: String,
    default: null,
    validator: (v) => ['default', 'active', 'success', 'warning', 'error', 'processing'].includes(v)
  }
})

const title = computed(() => props.label)
const colorClass = computed(() => `color-${props.color}`)
const displayValue = computed(() => `${props.value}${props.unit ? ` ${props.unit}` : ''}`)

const trendClass = computed(() => ({
  'trend-up': props.trend?.startsWith('+'),
  'trend-down': props.trend?.startsWith('-'),
  'trend-neutral': !props.trend?.startsWith('+') && !props.trend?.startsWith('-')
}))
</script>

<style scoped>
.metric-card {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.metric-card__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--space-4);
}

.metric-card__icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: var(--radius-lg);
  background: var(--bg-surface);
}

.metric-card__icon-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--accent-primary);
}

.metric-card__status {
  align-self: flex-start;
}

.metric-card__content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.metric-card__title {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
  margin-bottom: var(--space-2);
}

.metric-card__value {
  font-size: var(--text-3xl);
  font-weight: var(--font-bold);
  color: var(--text-primary);
  margin-bottom: var(--space-2);
}

.metric-card__trend {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
}

.trend-up {
  color: var(--color-success);
}

.trend-down {
  color: var(--color-error);
}

.trend-icon {
  width: 14px;
  height: 14px;
}

.trend-icon.up {
  color: var(--color-success);
}

.trend-icon.down {
  color: var(--color-error);
}
</style>