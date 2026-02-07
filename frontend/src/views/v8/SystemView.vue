<template>
  <div class="h-full flex flex-col p-6">
    <header class="mb-6">
      <h1 class="heading-2 flex items-center gap-3">
        <svg
          width="28"
          height="28"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          style="color: var(--accent-primary)"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01"
          />
        </svg>
        System Status
      </h1>
      <p class="body-default" style="color: var(--text-secondary); margin-top: var(--space-1)">
        État du système et des services
      </p>
    </header>

    <!-- System Metrics -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <GlassCard variant="bordered" padding="md">
        <div class="flex items-center justify-between">
          <div class="label" style="color: var(--text-secondary)">CPU</div>
          <span
            class="body-small"
            :style="{ color: cpuUsage > 80 ? 'var(--color-error)' : 'var(--color-success)' }"
          >
            {{ cpuUsage }}%
          </span>
        </div>
        <div
          style="
            margin-top: var(--space-2);
            height: 8px;
            background: var(--bg-surface);
            border-radius: var(--radius-full);
            overflow: hidden;
          "
        >
          <div
            style="
              height: 100%;
              border-radius: var(--radius-full);
              transition: width var(--transition-normal);
            "
            :style="{
              width: cpuUsage + '%',
              background: cpuUsage > 80 ? 'var(--color-error)' : 'var(--color-success)',
            }"
          ></div>
        </div>
      </GlassCard>

      <GlassCard variant="bordered" padding="md">
        <div class="flex items-center justify-between">
          <div class="label" style="color: var(--text-secondary)">RAM</div>
          <span
            class="body-small"
            :style="{ color: ramUsage > 80 ? 'var(--color-error)' : 'var(--color-success)' }"
          >
            {{ ramUsage }}%
          </span>
        </div>
        <div
          style="
            margin-top: var(--space-2);
            height: 8px;
            background: var(--bg-surface);
            border-radius: var(--radius-full);
            overflow: hidden;
          "
        >
          <div
            style="
              height: 100%;
              border-radius: var(--radius-full);
              transition: width var(--transition-normal);
            "
            :style="{
              width: ramUsage + '%',
              background: ramUsage > 80 ? 'var(--color-error)' : 'var(--color-success)',
            }"
          ></div>
        </div>
      </GlassCard>

      <GlassCard variant="bordered" padding="md">
        <div class="flex items-center justify-between">
          <div class="label" style="color: var(--text-secondary)">Disk</div>
          <span
            class="body-small"
            :style="{ color: diskUsage > 80 ? 'var(--color-error)' : 'var(--color-success)' }"
          >
            {{ diskUsage }}%
          </span>
        </div>
        <div
          style="
            margin-top: var(--space-2);
            height: 8px;
            background: var(--bg-surface);
            border-radius: var(--radius-full);
            overflow: hidden;
          "
        >
          <div
            style="
              height: 100%;
              border-radius: var(--radius-full);
              transition: width var(--transition-normal);
            "
            :style="{
              width: diskUsage + '%',
              background: diskUsage > 80 ? 'var(--color-error)' : 'var(--color-success)',
            }"
          ></div>
        </div>
      </GlassCard>

      <GlassCard variant="bordered" padding="md">
        <div class="flex items-center justify-between">
          <div class="label" style="color: var(--text-secondary)">GPU VRAM</div>
          <span
            class="body-small"
            :style="{ color: gpuUsage > 80 ? 'var(--color-error)' : 'var(--color-success)' }"
          >
            {{ gpuUsage }}%
          </span>
        </div>
        <div
          style="
            margin-top: var(--space-2);
            height: 8px;
            background: var(--bg-surface);
            border-radius: var(--radius-full);
            overflow: hidden;
          "
        >
          <div
            style="
              height: 100%;
              border-radius: var(--radius-full);
              transition: width var(--transition-normal);
            "
            :style="{
              width: gpuUsage + '%',
              background: gpuUsage > 80 ? 'var(--color-error)' : 'var(--color-success)',
            }"
          ></div>
        </div>
      </GlassCard>
    </div>

    <!-- Services -->
    <div class="flex-1 overflow-auto">
      <h3 class="heading-4" style="margin-bottom: var(--space-4)">Services</h3>

      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <GlassCard v-for="service in services" :key="service.name" variant="bordered" padding="md">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-3">
              <StatusOrb
                :status="service.status === 'running' ? 'success' : 'error'"
                :pulse="service.status === 'running'"
                size="sm"
              />
              <span class="heading-4">{{ service.name }}</span>
            </div>
            <StatusOrb
              :status="service.status === 'running' ? 'success' : 'error'"
              :label="service.status"
              size="sm"
            />
          </div>
          <div class="body-small" style="color: var(--text-secondary); margin-top: var(--space-2)">
            {{ service.description }}
          </div>
          <div
            v-if="service.url"
            class="label"
            style="color: var(--accent-primary); margin-top: var(--space-2)"
          >
            {{ service.url }}
          </div>
        </GlassCard>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import api from '@/services/api'
import GlassCard from '@/components/ui/GlassCard.vue'
import StatusOrb from '@/components/ui/StatusOrb.vue'

const cpuUsage = ref(35)
const ramUsage = ref(62)
const diskUsage = ref(45)
const gpuUsage = ref(28)

const services = ref([
  {
    name: 'AI Orchestrator Backend',
    status: 'running',
    description: 'FastAPI + WebSocket server',
    url: 'http://localhost:8000',
  },
  {
    name: 'AI Orchestrator Frontend',
    status: 'running',
    description: 'Vue 3 application',
    url: 'http://localhost:3000',
  },
  {
    name: 'Ollama',
    status: 'running',
    description: 'Local LLM inference',
    url: 'http://localhost:11434',
  },
  {
    name: 'ChromaDB',
    status: 'running',
    description: 'Vector database for memory',
    url: 'http://chromadb:8000',
  },
  {
    name: 'PostgreSQL',
    status: 'running',
    description: 'Primary database',
    url: 'postgres://localhost:5432',
  },
  {
    name: 'Redis',
    status: 'running',
    description: 'Cache and session store',
    url: 'redis://localhost:6379',
  },
])

let interval = null

const fetchMetrics = async () => {
  try {
    const response = await api.get('/system/metrics')
    cpuUsage.value = response.data.cpu || cpuUsage.value
    ramUsage.value = response.data.ram || ramUsage.value
    diskUsage.value = response.data.disk || diskUsage.value
    gpuUsage.value = response.data.gpu || gpuUsage.value
  } catch {
    // Keep current values on error
  }
}

onMounted(() => {
  fetchMetrics()
  interval = setInterval(fetchMetrics, 5000)
})

onUnmounted(() => {
  if (interval) clearInterval(interval)
})
</script>
