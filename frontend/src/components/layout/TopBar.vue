<!-- components/layout/TopBar.vue -->
<template>
  <header class="top-bar">
    <div class="top-bar__left">
      <button class="top-bar__menu-toggle" @click="toggleSidebar">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="3" y1="12" x2="21" y2="12"></line>
          <line x1="3" y1="6" x2="21" y2="6"></line>
          <line x1="3" y1="18" x2="21" y2="18"></line>
        </svg>
      </button>
      <h1 class="top-bar__title">{{ title }}</h1>
    </div>
    
    <div class="top-bar__center">
      <slot name="breadcrumbs" />
    </div>
    
    <div class="top-bar__right">
      <div class="top-bar__status">
        <StatusOrb :status="status" :label="statusLabel" pulse size="md" />
      </div>
      <div class="top-bar__actions">
        <slot name="actions" />
      </div>
      <div class="top-bar__user">
        <div class="user-menu">
          <div class="user-avatar">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
              <circle cx="12" cy="7" r="4"></circle>
            </svg>
          </div>
          <span class="user-name">Utilisateur</span>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
import StatusOrb from '../ui/StatusOrb.vue'

defineProps({
  title: {
    type: String,
    required: true
  },
  status: {
    type: String,
    default: 'active',
    validator: (v) => ['default', 'active', 'success', 'warning', 'error', 'processing'].includes(v)
  },
  statusLabel: {
    type: String,
    default: 'En ligne'
  }
})

const emit = defineEmits(['toggle-sidebar'])

const toggleSidebar = () => {
  emit('toggle-sidebar')
}
</script>

<style scoped>
.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: var(--header-height);
  padding: 0 var(--space-6);
  background: var(--bg-surface);
  border-bottom: 1px solid var(--border-default);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.top-bar__left {
  display: flex;
  align-items: center;
  gap: var(--space-4);
}

.top-bar__menu-toggle {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-md);
  background: transparent;
  border: 1px solid var(--border-default);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.top-bar__menu-toggle:hover {
  background: var(--bg-surface-hover);
  color: var(--text-primary);
  border-color: var(--border-strong);
}

.top-bar__title {
  font-size: var(--text-xl);
  font-weight: var(--font-semibold);
  color: var(--text-primary);
}

.top-bar__center {
  flex: 1;
  display: flex;
  justify-content: center;
}

.top-bar__right {
  display: flex;
  align-items: center;
  gap: var(--space-6);
}

.top-bar__status {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.top-bar__actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.top-bar__user {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.user-menu {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-lg);
  background: var(--bg-surface-hover);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.user-menu:hover {
  background: var(--bg-surface-active);
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-full);
  background: var(--accent-primary-gradient);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-on-accent);
}

.user-name {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--text-secondary);
}

@media (max-width: 768px) {
  .top-bar {
    padding: 0 var(--space-4);
  }
  
  .top-bar__center {
    display: none;
  }
  
  .top-bar__right {
    gap: var(--space-3);
  }
}
</style>