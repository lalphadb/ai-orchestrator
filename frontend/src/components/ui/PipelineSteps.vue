<!-- components/ui/PipelineSteps.vue -->
<template>
  <div class="pipeline-steps">
    <div 
      v-for="(step, index) in steps" 
      :key="step.id"
      class="pipeline-step"
      :class="{
        'pipeline-step--active': step.id === currentStep,
        'pipeline-step--completed': isCompleted(step.id),
        'pipeline-step--pending': isPending(step.id)
      }"
    >
      <div class="pipeline-step__connector" v-if="index > 0">
        <div class="pipeline-step__connector-line" />
      </div>
      
      <div class="pipeline-step__content">
        <div class="pipeline-step__icon">
          <div v-if="isCompleted(step.id)" class="pipeline-step__icon-check">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
              <polyline points="20,6 9,17 4,12"></polyline>
            </svg>
          </div>
          <div v-else-if="step.id === currentStep" class="pipeline-step__icon-current">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"></circle>
              <polyline points="12,8 12,12 15,15"></polyline>
            </svg>
          </div>
          <div v-else class="pipeline-step__icon-default">
            {{ index + 1 }}
          </div>
        </div>
        
        <div class="pipeline-step__label">
          <span class="pipeline-step__title">{{ step.title }}</span>
          <span v-if="step.description" class="pipeline-step__description">{{ step.description }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  steps: {
    type: Array,
    required: true,
    default: () => []
  },
  currentStep: {
    type: String,
    required: true
  },
  completedSteps: {
    type: Array,
    default: () => []
  }
})

const isCompleted = (stepId) => {
  return props.completedSteps.includes(stepId)
}

const isPending = (stepId) => {
  return !isCompleted(stepId) && stepId !== props.currentStep
}
</script>

<style scoped>
.pipeline-steps {
  display: flex;
  align-items: stretch;
  width: 100%;
  background: var(--bg-surface);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  gap: 0;
}

.pipeline-step {
  flex: 1;
  display: flex;
  align-items: center;
  position: relative;
}

.pipeline-step__connector {
  position: relative;
  width: 50%;
  display: flex;
  align-items: center;
}

.pipeline-step__connector-line {
  height: 2px;
  width: 100%;
  background: var(--border-default);
  position: relative;
}

.pipeline-step--completed .pipeline-step__connector-line {
  background: var(--accent-primary);
}

.pipeline-step:first-child .pipeline-step__connector {
  display: none;
}

.pipeline-step__content {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 0 var(--space-3);
}

.pipeline-step__icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: var(--space-2);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
  position: relative;
  z-index: 1;
}

.pipeline-step__icon-default {
  background: var(--bg-surface);
  border: 2px solid var(--border-default);
}

.pipeline-step__icon-check {
  background: var(--color-success);
  border: 2px solid var(--color-success);
}

.pipeline-step__icon-current {
  background: var(--accent-primary);
  border: 2px solid var(--accent-primary);
  animation: pulse 2s infinite;
}

.pipeline-step--completed .pipeline-step__icon {
  background: var(--color-success);
  border: 2px solid var(--color-success);
  color: var(--text-on-accent);
}

.pipeline-step--active .pipeline-step__icon {
  background: var(--accent-primary);
  border: 2px solid var(--accent-primary);
  color: var(--text-on-accent);
  animation: pulse 2s infinite;
}

.pipeline-step__label {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.pipeline-step__title {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--text-primary);
}

.pipeline-step__description {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

@keyframes pulse {
  0%, 100% { box-shadow: 0 0 0 0 rgba(139, 92, 246, 0.4); }
  50% { box-shadow: 0 0 0 8px rgba(139, 92, 246, 0); }
}

@media (max-width: 768px) {
  .pipeline-steps {
    flex-direction: column;
    align-items: stretch;
  }
  
  .pipeline-step {
    flex-direction: row;
    align-items: center;
    text-align: left;
  }
  
  .pipeline-step__content {
    align-items: flex-start;
    text-align: left;
    padding: var(--space-2);
  }
  
  .pipeline-step__connector {
    width: 36px;
    height: 50%;
    position: absolute;
    left: 18px;
    top: 46px;
    flex-direction: column;
  }
  
  .pipeline-step__connector-line {
    width: 2px;
    height: 100%;
    margin-left: 17px;
  }
  
  .pipeline-step:first-child .pipeline-step__connector {
    display: flex;
  }
}
</style>