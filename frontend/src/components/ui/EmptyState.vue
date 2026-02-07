<!-- components/ui/EmptyState.vue -->
<template>
  <div class="empty-state">
    <div class="empty-state__icon">
      <slot name="icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.66 0 3-4.47 3-10S14.66 2 13 2H9a7 7 0 000 14z" />
        </svg>
      </slot>
    </div>
    <h3 class="empty-state__title">{{ title }}</h3>
    <p class="empty-state__description">{{ description }}</p>
    <div v-if="$slots.actions" class="empty-state__actions">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    default: 'Aucun élément'
  },
  description: {
    type: String,
    default: 'Il n\'y a rien à afficher ici pour le moment.'
  }
})
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: var(--space-12);
  color: var(--text-tertiary);
}

.empty-state__icon {
  margin-bottom: var(--space-6);
  color: var(--text-muted);
}

.empty-state__title {
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  color: var(--text-secondary);
  margin-bottom: var(--space-2);
}

.empty-state__description {
  font-size: var(--text-base);
  color: var(--text-tertiary);
  margin-bottom: var(--space-6);
  max-width: 320px;
}

.empty-state__actions {
  display: flex;
  gap: var(--space-3);
}
</style>