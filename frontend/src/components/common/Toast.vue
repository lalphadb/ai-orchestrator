<template>
  <Transition name="toast">
    <div
      v-if="show"
      class="fixed bottom-6 right-6 z-50 px-6 py-4 rounded-xl shadow-2xl border backdrop-blur-sm flex items-center gap-3 max-w-md"
      :class="typeClasses"
    >
      <div class="flex-shrink-0">
        <component :is="iconComponent" class="w-5 h-5" />
      </div>
      <div class="flex-1">
        <p class="font-medium text-sm">{{ message }}</p>
        <p v-if="description" class="text-xs opacity-80 mt-1">{{ description }}</p>
      </div>
      <button class="flex-shrink-0 opacity-70 hover:opacity-100 transition-opacity" @click="close">
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </button>
    </div>
  </Transition>
</template>

<script setup>
import { computed, watch, onMounted } from 'vue'

const props = defineProps({
  show: {
    type: Boolean,
    default: false,
  },
  type: {
    type: String,
    default: 'success', // success, error, warning, info
    validator: (value) => ['success', 'error', 'warning', 'info'].includes(value),
  },
  message: {
    type: String,
    required: true,
  },
  description: {
    type: String,
    default: '',
  },
  duration: {
    type: Number,
    default: 3000,
  },
})

const emit = defineEmits(['close'])

let timeout = null

const typeClasses = computed(() => {
  const classes = {
    success: 'bg-green-500/20 border-green-500/50 text-green-300',
    error: 'bg-red-500/20 border-red-500/50 text-red-300',
    warning: 'bg-orange-500/20 border-orange-500/50 text-orange-300',
    info: 'bg-blue-500/20 border-blue-500/50 text-blue-300',
  }
  return classes[props.type]
})

const iconComponent = computed(() => {
  const icons = {
    success: {
      template: `
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
      `,
    },
    error: {
      template: `
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
      `,
    },
    warning: {
      template: `
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
        </svg>
      `,
    },
    info: {
      template: `
        <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
      `,
    },
  }
  return icons[props.type]
})

function close() {
  if (timeout) {
    clearTimeout(timeout)
  }
  emit('close')
}

watch(
  () => props.show,
  (newValue) => {
    if (newValue && props.duration > 0) {
      timeout = setTimeout(() => {
        close()
      }, props.duration)
    }
  }
)

onMounted(() => {
  if (props.show && props.duration > 0) {
    timeout = setTimeout(() => {
      close()
    }, props.duration)
  }
})
</script>

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.toast-enter-from {
  opacity: 0;
  transform: translateX(100%) scale(0.95);
}

.toast-leave-to {
  opacity: 0;
  transform: translateY(-20px) scale(0.95);
}
</style>
