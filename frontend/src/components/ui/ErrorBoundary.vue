<!-- components/ui/ErrorBoundary.vue -->
<template>
  <div v-if="error" class="error-boundary">
    <GlassCard variant="bordered">
      <div class="error-boundary__content">
        <div class="error-boundary__icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
            <path d="M12 8v4m0 4h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </div>
        <h3 class="error-boundary__title">Une erreur est survenue</h3>
        <p class="error-boundary__message">{{ error.message }}</p>
        <div class="error-boundary__actions">
          <ModernButton variant="primary" @click="retry">
            Réessayer
          </ModernButton>
          <ModernButton variant="ghost" @click="showDetails = !showDetails">
            {{ showDetails ? 'Masquer' : 'Détails' }}
          </ModernButton>
        </div>
        <pre v-if="showDetails" class="error-boundary__stack">{{ error.stack }}</pre>
      </div>
    </GlassCard>
  </div>
  <slot v-else />
</template>

<script setup>
import { ref, onErrorCaptured } from 'vue'
import GlassCard from './GlassCard.vue'
import ModernButton from './ModernButton.vue'

const error = ref(null)
const showDetails = ref(false)

onErrorCaptured((err) => {
  error.value = err
  console.error('ErrorBoundary caught:', err)
  return false // Prevent propagation
})

const retry = () => {
  error.value = null
  showDetails.value = false
}
</script>

<style scoped>
.error-boundary__content {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: var(--space-8);
}

.error-boundary__icon {
  color: var(--color-error);
  margin-bottom: var(--space-4);
}

.error-boundary__title {
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
  margin-bottom: var(--space-2);
}

.error-boundary__message {
  color: var(--text-secondary);
  margin-bottom: var(--space-6);
}

.error-boundary__actions {
  display: flex;
  gap: var(--space-3);
}

.error-boundary__stack {
  margin-top: var(--space-6);
  padding: var(--space-4);
  background: var(--bg-surface);
  border-radius: var(--radius-md);
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  color: var(--text-tertiary);
  text-align: left;
  overflow-x: auto;
  max-width: 100%;
}
</style>