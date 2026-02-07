<template>
  <Teleport to="body">
    <div
      v-if="loading.isLoading"
      class="fixed top-0 left-0 right-0 z-[9999] h-1 bg-gradient-to-r from-primary-500 via-purple-500 to-primary-500 loading-bar"
    ></div>
  </Teleport>
</template>

<script setup>
import { useLoadingStore } from '@/stores/loading'

const loading = useLoadingStore()
</script>

<style scoped>
.loading-bar {
  animation: loading-shimmer 2s linear infinite;
  background-size: 200% 100%;
}

@keyframes loading-shimmer {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}
</style>
