<!-- components/ui/SkeletonLoader.vue -->
<template>
  <div class="skeleton" :class="`skeleton--${variant}`">
    <div
      v-for="i in lines"
      :key="i"
      class="skeleton__line"
      :style="{ width: getLineWidth(i) }"
    />
  </div>
</template>

<script setup>
const props = defineProps({
  variant: {
    type: String,
    default: 'text',
    validator: (v) => ['text', 'card', 'avatar', 'button'].includes(v)
  },
  lines: {
    type: Number,
    default: 3
  }
})

const getLineWidth = (index) => {
  if (props.variant === 'card') return '100%'
  const widths = ['100%', '80%', '60%', '90%', '70%']
  return widths[(index - 1) % widths.length]
}
</script>

<style scoped>
.skeleton__line {
  height: 16px;
  background: linear-gradient(
    90deg,
    var(--bg-surface) 25%,
    var(--bg-surface-hover) 50%,
    var(--bg-surface) 75%
  );
  background-size: 200% 100%;
  border-radius: var(--radius-sm);
  animation: skeleton-shimmer 1.5s infinite;
  margin-bottom: var(--space-2);
}

.skeleton__line:last-child {
  margin-bottom: 0;
}

.skeleton--card .skeleton__line {
  height: 120px;
  border-radius: var(--radius-lg);
}

.skeleton--avatar .skeleton__line {
  width: 48px !important;
  height: 48px;
  border-radius: var(--radius-full);
}

.skeleton--button .skeleton__line {
  width: 120px !important;
  height: 40px;
  border-radius: var(--radius-lg);
}

@keyframes skeleton-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>