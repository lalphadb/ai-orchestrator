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
            d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
          />
        </svg>
        Memory
      </h1>
      <p class="body-default" style="color: var(--text-secondary); margin-top: var(--space-1)">
        Mémoire d'apprentissage et expériences
      </p>
    </header>

    <!-- Search -->
    <div class="mb-6">
      <div class="flex gap-3">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Rechercher dans la mémoire..."
          class="body-default"
          style="
            flex: 1;
            background: var(--bg-surface);
            border: 1px solid var(--border-default);
            border-radius: var(--radius-lg);
            padding: var(--space-3) var(--space-4);
            color: var(--text-primary);
          "
          @keyup.enter="search"
        />
        <ModernButton
          variant="primary"
          size="md"
          :loading="searching"
          :disabled="searching"
          @click="search"
        >
          {{ searching ? 'Recherche...' : 'Rechercher' }}
        </ModernButton>
      </div>
    </div>

    <!-- Results -->
    <div class="flex-1 overflow-auto">
      <!-- Loading State -->
      <div v-if="searching" class="space-y-4">
        <SkeletonLoader v-for="i in 3" :key="i" variant="rect" :height="120" />
      </div>

      <!-- Error State -->
      <GlassCard
        v-else-if="error"
        variant="bordered"
        padding="md"
        style="border-color: var(--color-error-border); background: rgba(239, 68, 68, 0.1)"
      >
        <p class="body-default" style="color: var(--color-error)">{{ error }}</p>
        <ModernButton
          variant="danger"
          size="sm"
          style="margin-top: var(--space-3)"
          @click="fetchStats"
        >
          Réessayer
        </ModernButton>
      </GlassCard>

      <!-- No Results After Search -->
      <EmptyState
        v-else-if="results.length === 0 && hasSearched"
        title="Aucun résultat"
        :message="`Aucun résultat pour &quot;${lastQuery}&quot;`"
      >
        <template #icon>
          <svg
            width="64"
            height="64"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            style="color: var(--text-tertiary)"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="1.5"
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </template>
      </EmptyState>

      <!-- Empty State Before Search -->
      <EmptyState
        v-else-if="results.length === 0"
        title="Mémoire d'apprentissage"
        message="Entrez une requête pour rechercher dans les expériences"
      >
        <template #icon>
          <svg
            width="64"
            height="64"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            style="color: var(--text-tertiary)"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="1.5"
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
        </template>
      </EmptyState>

      <!-- Results List -->
      <div v-else class="space-y-4">
        <GlassCard v-for="(result, idx) in results" :key="idx" variant="bordered" padding="md">
          <div class="flex items-start justify-between">
            <div class="flex-1">
              <div class="flex items-center gap-2" style="margin-bottom: var(--space-2)">
                <span
                  v-if="result.score != null"
                  class="label"
                  style="
                    padding: var(--space-1) var(--space-2);
                    background: rgba(139, 92, 246, 0.2);
                    color: var(--accent-primary);
                    border-radius: var(--radius-sm);
                  "
                >
                  Score: {{ (result.score * 100).toFixed(1) }}%
                </span>
                <span
                  v-if="result.metadata?.topic || result.topic"
                  class="label"
                  style="
                    padding: var(--space-1) var(--space-2);
                    background: var(--bg-surface);
                    border-radius: var(--radius-sm);
                    color: var(--text-secondary);
                  "
                >
                  {{ result.metadata?.topic || result.topic }}
                </span>
                <span
                  v-if="result.type"
                  class="label"
                  style="
                    padding: var(--space-1) var(--space-2);
                    background: rgba(59, 130, 246, 0.2);
                    color: #60a5fa;
                    border-radius: var(--radius-sm);
                  "
                >
                  {{ result.type }}
                </span>
              </div>
              <p class="body-default">
                {{ result.document || result.content || result.query || JSON.stringify(result) }}
              </p>
              <p
                v-if="result.response"
                class="body-small line-clamp-3"
                style="color: var(--text-secondary); margin-top: var(--space-2)"
              >
                {{ result.response }}
              </p>
            </div>
          </div>

          <div
            class="label flex gap-4"
            style="margin-top: var(--space-3); color: var(--text-tertiary)"
          >
            <span v-if="result.metadata?.timestamp || result.timestamp">
              {{ new Date(result.metadata?.timestamp || result.timestamp).toLocaleString('fr-CA') }}
            </span>
            <span v-if="result.tools_used?.length">
              Outils: {{ result.tools_used.join(', ') }}
            </span>
          </div>
        </GlassCard>
      </div>
    </div>

    <!-- Stats -->
    <div class="mt-6 pt-4" style="border-top: 1px solid var(--border-subtle)">
      <div v-if="statsLoading" class="body-small" style="color: var(--text-tertiary)">
        Chargement des stats...
      </div>
      <div
        v-else
        class="flex items-center gap-6 body-small flex-wrap"
        style="color: var(--text-secondary)"
      >
        <div>
          Status:
          <span
            :style="{
              color:
                stats.status === 'active' || stats.status === 'healthy'
                  ? 'var(--color-success)'
                  : 'var(--color-warning)',
            }"
          >
            {{ stats.status || 'inconnu' }}
          </span>
        </div>
        <div>
          Expériences:
          <span style="color: var(--text-primary)">{{ stats.experiences_count ?? 'N/A' }}</span>
        </div>
        <div>
          Patterns:
          <span style="color: var(--text-primary)">{{ stats.patterns_count ?? 'N/A' }}</span>
        </div>
        <div>
          Corrections:
          <span style="color: var(--text-primary)">{{ stats.corrections_count ?? 'N/A' }}</span>
        </div>
        <div>
          Contextes:
          <span style="color: var(--text-primary)">{{ stats.user_contexts_count ?? 'N/A' }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'
import GlassCard from '@/components/ui/GlassCard.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import ModernButton from '@/components/ui/ModernButton.vue'
import SkeletonLoader from '@/components/ui/SkeletonLoader.vue'

const searchQuery = ref('')
const searching = ref(false)
const hasSearched = ref(false)
const lastQuery = ref('')
const results = ref([])
const error = ref(null)
const stats = ref({})
const statsLoading = ref(true)

const search = async () => {
  if (!searchQuery.value.trim()) return

  searching.value = true
  hasSearched.value = true
  lastQuery.value = searchQuery.value
  error.value = null
  try {
    const query = encodeURIComponent(searchQuery.value)
    // api.get() returns parsed JSON directly (not .data wrapper)
    const response = await api.get(`/learning/experiences?query=${query}&limit=10`)
    // Response could be an array or object with results
    results.value = Array.isArray(response)
      ? response
      : response.experiences || response.results || []
  } catch (err) {
    console.error('[MemoryView] search error:', err)
    error.value = 'Erreur de recherche: ' + (err.message || 'Erreur inconnue')
    results.value = []
  } finally {
    searching.value = false
  }
}

const fetchStats = async () => {
  statsLoading.value = true
  error.value = null
  try {
    // api.get() returns parsed JSON directly
    // Backend returns: {status, experiences_count, patterns_count, corrections_count, user_contexts_count}
    const response = await api.get('/learning/stats')
    stats.value = response || {}
  } catch (err) {
    console.error('[MemoryView] fetchStats error:', err)
    stats.value = {}
    // Don't show error for stats - page is still usable for search
  } finally {
    statsLoading.value = false
  }
}

onMounted(fetchStats)
</script>
