<!-- components/ui/ThinkingDots.vue -->
<template>
  <div class="thinking-dots">
    <div class="dot" />
    <div class="dot" />
    <div class="dot" />
  </div>
</template>

<style scoped>
.thinking-dots {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  height: 24px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent-primary);
  animation: thinking-dots 1.4s infinite ease-in-out both;
}

.dot:nth-child(1) {
  animation-delay: -0.32s;
}

.dot:nth-child(2) {
  animation-delay: -0.16s;
}

@keyframes thinking-dots {
  0%, 80%, 100% {
    transform: scale(0);
  }
  40% {
    transform: scale(1);
  }
}
</style>