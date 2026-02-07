<!-- components/ui/AgentCard.vue -->
<template>
  <GlassCard class="agent-card" hoverable @click="$emit('click', agent)">
    <div class="agent-card__header">
      <div class="agent-card__icon">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
        </svg>
      </div>
      <div class="agent-card__status">
        <StatusOrb :status="agent.status" size="sm" />
      </div>
    </div>
    
    <div class="agent-card__content">
      <h3 class="agent-card__title">{{ agent.name }}</h3>
      <p class="agent-card__description">{{ agent.description }}</p>
    </div>
    
    <div class="agent-card__footer">
      <div class="agent-card__capabilities">
        <span 
          v-for="capability in agent.capabilities" 
          :key="capability"
          class="agent-card__capability"
        >
          {{ capability }}
        </span>
      </div>
      <div class="agent-card__tools">
        <span class="agent-card__tools-count">{{ agent.tools.length }} outils</span>
      </div>
    </div>
  </GlassCard>
</template>

<script setup>
import GlassCard from './GlassCard.vue'
import StatusOrb from './StatusOrb.vue'

defineProps({
  agent: {
    type: Object,
    required: true,
    validator: (v) => 
      typeof v.id === 'string' && 
      typeof v.name === 'string' && 
      typeof v.description === 'string' &&
      Array.isArray(v.capabilities) &&
      Array.isArray(v.tools)
  }
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

.agent-card__capabilities {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
}

.agent-card__capability {
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
  color: var(--text-on-accent);
  background: var(--accent-primary-gradient);
  padding: var(--space-1) var(--space-2);
  border-radius: var(--radius-full);
}

.agent-card__tools-count {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  font-weight: var(--font-medium);
}
</style>