<!-- components/ui/Dropdown.vue -->
<template>
  <div ref="dropdownRef" class="dropdown">
    <button class="dropdown-trigger" @click="toggleDropdown">
      <slot name="trigger" />
      <svg
        class="dropdown-arrow"
        :class="{ 'dropdown-arrow--open': isOpen }"
        width="16"
        height="16"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
      >
        <polyline points="6,9 12,15 18,9"></polyline>
      </svg>
    </button>

    <div v-show="isOpen" class="dropdown-menu" :class="`dropdown-menu--${position}`">
      <slot name="items" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

defineProps({
  position: {
    type: String,
    default: 'bottom-start',
    validator: (v) => ['bottom-start', 'bottom-end', 'top-start', 'top-end'].includes(v),
  },
})

const isOpen = ref(false)
const dropdownRef = ref(null)

const toggleDropdown = () => {
  isOpen.value = !isOpen.value
}

const handleClickOutside = (event) => {
  if (dropdownRef.value && !dropdownRef.value.contains(event.target)) {
    isOpen.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.dropdown {
  position: relative;
  display: inline-block;
}

.dropdown-trigger {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.dropdown-trigger:hover {
  background: var(--bg-surface-hover);
  color: var(--text-primary);
  border-color: var(--border-strong);
}

.dropdown-arrow {
  transition: transform var(--transition-fast);
}

.dropdown-arrow--open {
  transform: rotate(180deg);
}

.dropdown-menu {
  position: absolute;
  z-index: var(--z-dropdown);
  min-width: 160px;
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-lg);
  overflow: hidden;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.dropdown-menu--bottom-start {
  top: calc(100% + var(--space-2));
  left: 0;
}

.dropdown-menu--bottom-end {
  top: calc(100% + var(--space-2));
  right: 0;
}

.dropdown-menu--top-start {
  bottom: calc(100% + var(--space-2));
  left: 0;
}

.dropdown-menu--top-end {
  bottom: calc(100% + var(--space-2));
  right: 0;
}

/* Dropdown items */
.dropdown-item {
  display: block;
  width: 100%;
  padding: var(--space-3) var(--space-4);
  text-decoration: none;
  color: var(--text-secondary);
  background: transparent;
  border: none;
  text-align: left;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.dropdown-item:hover {
  background: var(--bg-surface-hover);
  color: var(--text-primary);
}

.dropdown-divider {
  height: 1px;
  background: var(--border-default);
  margin: var(--space-1) 0;
}
</style>
