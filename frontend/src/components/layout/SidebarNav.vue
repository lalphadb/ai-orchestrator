<!-- components/layout/SidebarNav.vue -->
<template>
  <nav class="sidebar-nav">
    <div class="sidebar-nav__logo">
      <div class="logo-icon">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" />
        </svg>
      </div>
      <span class="logo-text">Orchestrator</span>
    </div>
    
    <div class="sidebar-nav__menu">
      <router-link
        v-for="item in menuItems"
        :key="item.route"
        :to="item.route"
        class="sidebar-nav__item"
        :class="{ 'sidebar-nav__item--active': isActive(item.route) }"
      >
        <div class="sidebar-nav__icon">
          <component :is="item.icon" />
        </div>
        <span class="sidebar-nav__label">{{ item.label }}</span>
        <div v-if="item.badge" class="sidebar-nav__badge">{{ item.badge }}</div>
      </router-link>
    </div>
    
    <div class="sidebar-nav__footer">
      <div class="sidebar-nav__user">
        <div class="user-avatar">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
            <circle cx="12" cy="7" r="4"></circle>
          </svg>
        </div>
        <div class="user-info">
          <div class="user-name">Utilisateur</div>
          <div class="user-status">
            <StatusOrb status="active" size="sm" />
            <span>En ligne</span>
          </div>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { useRoute } from 'vue-router'
import StatusOrb from '../ui/StatusOrb.vue'

const route = useRoute()

defineProps({
  menuItems: {
    type: Array,
    required: true
  }
})

const isActive = (path) => {
  return route.path.startsWith(path)
}
</script>

<style scoped>
.sidebar-nav {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: var(--sidebar-width);
  background: var(--bg-sidebar);
  border-right: 1px solid var(--border-default);
  padding: var(--space-6) 0;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.sidebar-nav__logo {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: 0 var(--space-6) var(--space-6);
  border-bottom: 1px solid var(--border-subtle);
}

.logo-icon {
  width: 32px;
  height: 32px;
  border-radius: var(--radius-md);
  background: var(--accent-primary-gradient);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-on-accent);
}

.logo-text {
  font-size: var(--text-lg);
  font-weight: var(--font-bold);
  background: var(--text-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.sidebar-nav__menu {
  flex: 1;
  padding: var(--space-4) 0;
}

.sidebar-nav__item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-6);
  text-decoration: none;
  color: var(--text-secondary);
  transition: all var(--transition-fast);
  position: relative;
}

.sidebar-nav__item:hover {
  background: var(--bg-sidebar-item-hover);
  color: var(--text-primary);
}

.sidebar-nav__item--active {
  background: var(--bg-sidebar-item-active);
  color: var(--text-primary);
}

.sidebar-nav__item--active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background: var(--accent-primary);
}

.sidebar-nav__icon {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sidebar-nav__label {
  flex: 1;
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
}

.sidebar-nav__badge {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 var(--space-2);
  background: var(--accent-primary);
  color: var(--text-on-accent);
  border-radius: var(--radius-full);
  font-size: var(--text-xs);
  font-weight: var(--font-semibold);
}

.sidebar-nav__footer {
  padding: var(--space-4) var(--space-6);
  border-top: 1px solid var(--border-subtle);
}

.sidebar-nav__user {
  display: flex;
  align-items: center;
  gap: var(--space-3);
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

.user-info {
  flex: 1;
}

.user-name {
  font-size: var(--text-sm);
  font-weight: var(--font-medium);
  color: var(--text-primary);
}

.user-status {
  display: flex;
  align-items: center;
  gap: var(--space-1);
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

@media (max-width: 1024px) {
  .sidebar-nav {
    width: var(--sidebar-width-collapsed);
  }
  
  .logo-text,
  .sidebar-nav__label,
  .user-name,
  .user-status span {
    display: none;
  }
  
  .sidebar-nav__item {
    justify-content: center;
    padding: var(--space-4) var(--space-3);
  }
  
  .sidebar-nav__badge {
    position: absolute;
    top: 4px;
    right: 4px;
    min-width: 16px;
    height: 16px;
    font-size: var(--text-xs);
  }
}
</style>