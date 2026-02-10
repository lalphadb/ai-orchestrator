<!-- components/ui/AgentCard.vue -->
<template>
  <GlassCard class="agent-card" hoverable @click="$emit('click')">
    <div class="agent-card__header">
      <div class="agent-card__icon">
        <svg
          width="32"
          height="32"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
        </svg>
      </div>
      <div class="agent-card__status">
        <StatusOrb :status="status" size="sm" :pulse="statusPulse" />
      </div>
    </div>

    <div class="agent-card__content">
      <h3 class="agent-card__title">{{ name }}</h3>
      <p class="agent-card__description">{{ description }}</p>
    </div>

    <div v-if="metrics && metrics.length" class="agent-card__footer">
      <div class="agent-card__metrics">
        <span v-for="metric in metrics" :key="metric.label" class="agent-card__metric">
          {{ metric.label }}: {{ metric.value }}
        </span>
      </div>
    </div>
  </GlassCard>
</template>

<script setup>
import GlassCard from './GlassCard.vue'
import StatusOrb from './StatusOrb.vue'

defineProps({
  name: {
    type: String,
    required: true,
  },
  description: {
    type: String,
    default: '',
  },
  status: {
    type: String,
    default: 'default',
  },
  statusPulse: {
    type: Boolean,
    default: false,
  },
  metrics: {
    type: Array,
    default: () => [],
  },
  interactive: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['click'])
</script>

<style scoped>
.agent-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.agent-card__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--space-4);
}

.agent-card__icon {
  width: 40px;
  height: 40px;
  border-radius: var(--radius-lg);
  background: var(--accent-primary-gradient);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-on-accent);
}

.agent-card__content {
  flex: 1;
  margin-bottom: var(--space-4);
}

.agent-card__title {
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
  margin-bottom: var(--space-2);
}

.agent-card__description {
  font-size: var(--text-sm);
  color: var(--text-tertiary);
  line-height: var(--leading-relaxed);
}

.agent-card__footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: var(--space-4);
}

.agent-card__metrics {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.agent-card__metric {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  font-weight: var(--font-medium);
}
</style>
