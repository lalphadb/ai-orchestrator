<!-- components/ui/Tooltip.vue -->
<template>
  <div class="tooltip-wrapper" @mouseenter="showTooltip" @mouseleave="hideTooltip">
    <slot />
    <div v-if="isVisible" class="tooltip" :class="`tooltip--${position}`" :style="tooltipStyle">
      {{ content }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  content: {
    type: String,
    required: true,
  },
  position: {
    type: String,
    default: 'top',
    validator: (v) => ['top', 'bottom', 'left', 'right'].includes(v),
  },
  showDelay: {
    type: Number,
    default: 500,
  },
  hideDelay: {
    type: Number,
    default: 100,
  },
})

const isVisible = ref(false)
const tooltipPosition = ref({ top: 0, left: 0 })

let showTimer = null
let hideTimer = null

const showTooltip = () => {
  clearTimeout(hideTimer)
  showTimer = setTimeout(() => {
    isVisible.value = true
    updatePosition()
  }, props.showDelay)
}

const hideTooltip = () => {
  clearTimeout(showTimer)
  hideTimer = setTimeout(() => {
    isVisible.value = false
  }, props.hideDelay)
}

const updatePosition = () => {
  const parent = document.querySelector('.tooltip-wrapper')
  if (!parent) return

  const rect = parent.getBoundingClientRect()
  const tooltipWidth = 200 // Approximate width of tooltip
  const tooltipHeight = 40 // Approximate height of tooltip

  let top = 0
  let left = 0

  switch (props.position) {
    case 'top':
      top = rect.top - tooltipHeight - 10
      left = rect.left + rect.width / 2 - tooltipWidth / 2
      break
    case 'bottom':
      top = rect.bottom + 10
      left = rect.left + rect.width / 2 - tooltipWidth / 2
      break
    case 'left':
      top = rect.top + rect.height / 2 - tooltipHeight / 2
      left = rect.left - tooltipWidth - 10
      break
    case 'right':
      top = rect.top + rect.height / 2 - tooltipHeight / 2
      left = rect.right + 10
      break
  }

  tooltipPosition.value = { top: `${top}px`, left: `${left}px` }
}

const tooltipStyle = computed(() => ({
  top: tooltipPosition.value.top,
  left: tooltipPosition.value.left,
}))
</script>

<style scoped>
.tooltip-wrapper {
  position: relative;
  display: inline-block;
}

.tooltip {
  position: fixed;
  z-index: var(--z-tooltip);
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  padding: var(--space-2) var(--space-3);
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
  color: var(--text-secondary);
  max-width: 200px;
  text-align: center;
  box-shadow: var(--shadow-md);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  animation: fadeIn 0.2s ease-out;
}

.tooltip--top {
  transform: translateY(-4px);
}

.tooltip--bottom {
  transform: translateY(4px);
}

.tooltip--left {
  transform: translateX(-4px);
}

.tooltip--right {
  transform: translateX(4px);
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(0) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}
</style>
