<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 p-6">
    <div class="max-w-7xl mx-auto">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-white mb-2">🧠 Apprentissage IA</h1>
        <p class="text-gray-400">Statistiques et patterns appris par le système</p>
      </div>

      <!-- Loading State -->
      <div v-if="loading" class="flex items-center justify-center py-20">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="bg-red-900/20 border border-red-500/50 rounded-xl p-6 mb-8">
        <p class="text-red-400">❌ {{ error }}</p>
        <button
          class="mt-4 px-4 py-2 bg-red-600 hover:bg-red-500 rounded-lg text-white"
          @click="loadData"
        >
          Réessayer
        </button>
      </div>

      <!-- Main Content -->
      <div v-else>
        <!-- Stats Cards -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <!-- Total Feedback -->
          <div
            class="bg-gray-900/50 border border-gray-800 rounded-xl p-6 hover:border-gray-700 transition-colors"
          >
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-sm font-medium text-gray-400">Total Feedbacks</h3>
              <span class="text-2xl">📊</span>
            </div>
            <div class="text-3xl font-bold text-white">
              {{ feedbackStats?.total || 0 }}
            </div>
            <p class="text-xs text-gray-500 mt-2">Dernières 24h</p>
          </div>

          <!-- Positive Rate -->
          <div
            class="bg-gray-900/50 border border-gray-800 rounded-xl p-6 hover:border-gray-700 transition-colors"
          >
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-sm font-medium text-gray-400">Taux Positif</h3>
              <span class="text-2xl">👍</span>
            </div>
            <div class="text-3xl font-bold text-green-400">
              {{ Math.round((feedbackStats?.positive_rate || 0) * 100) }}%
            </div>
            <p class="text-xs text-gray-500 mt-2">{{ feedbackStats?.positive || 0 }} positifs</p>
          </div>

          <!-- Patterns Appris -->
          <div
            class="bg-gray-900/50 border border-gray-800 rounded-xl p-6 hover:border-gray-700 transition-colors"
          >
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-sm font-medium text-gray-400">Patterns</h3>
              <span class="text-2xl">🔍</span>
            </div>
            <div class="text-3xl font-bold text-blue-400">
              {{ learningStats?.patterns_count || 0 }}
            </div>
            <p class="text-xs text-gray-500 mt-2">Patterns stockés</p>
          </div>

          <!-- Corrections -->
          <div
            class="bg-gray-900/50 border border-gray-800 rounded-xl p-6 hover:border-gray-700 transition-colors"
          >
            <div class="flex items-center justify-between mb-4">
              <h3 class="text-sm font-medium text-gray-400">Corrections</h3>
              <span class="text-2xl">✏️</span>
            </div>
            <div class="text-3xl font-bold text-orange-400">
              {{ feedbackStats?.corrections || 0 }}
            </div>
            <p class="text-xs text-gray-500 mt-2">Corrections utilisateur</p>
          </div>
        </div>

        <!-- Feedback Timeline -->
        <div class="bg-gray-900/50 border border-gray-800 rounded-xl p-6 mb-8">
          <h2 class="text-xl font-bold text-white mb-4">📈 Activité (24h)</h2>
          <div class="space-y-3">
            <div class="flex items-center justify-between text-sm">
              <span class="text-gray-400 w-24">Positifs</span>
              <div class="flex items-center gap-2 flex-1">
                <div class="flex-1 bg-gray-800 rounded-full h-3">
                  <div
                    class="bg-green-500 h-3 rounded-full transition-all duration-500"
                    :style="{ width: `${getPercentage(feedbackStats?.positive)}%` }"
                  ></div>
                </div>
                <span class="text-white font-medium w-16 text-right">
                  {{ feedbackStats?.positive || 0 }}
                </span>
              </div>
            </div>

            <div class="flex items-center justify-between text-sm">
              <span class="text-gray-400 w-24">Négatifs</span>
              <div class="flex items-center gap-2 flex-1">
                <div class="flex-1 bg-gray-800 rounded-full h-3">
                  <div
                    class="bg-red-500 h-3 rounded-full transition-all duration-500"
                    :style="{ width: `${getPercentage(feedbackStats?.negative)}%` }"
                  ></div>
                </div>
                <span class="text-white font-medium w-16 text-right">
                  {{ feedbackStats?.negative || 0 }}
                </span>
              </div>
            </div>

            <div class="flex items-center justify-between text-sm">
              <span class="text-gray-400 w-24">Corrections</span>
              <div class="flex items-center gap-2 flex-1">
                <div class="flex-1 bg-gray-800 rounded-full h-3">
                  <div
                    class="bg-orange-500 h-3 rounded-full transition-all duration-500"
                    :style="{ width: `${getPercentage(feedbackStats?.corrections)}%` }"
                  ></div>
                </div>
                <span class="text-white font-medium w-16 text-right">
                  {{ feedbackStats?.corrections || 0 }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Top Patterns -->
        <div class="bg-gray-900/50 border border-gray-800 rounded-xl p-6 mb-8">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-xl font-bold text-white">🎯 Patterns les Plus Utilisés</h2>
            <button
              class="text-sm text-blue-400 hover:text-blue-300 transition-colors"
              @click="loadPatterns"
            >
              🔄 Actualiser
            </button>
          </div>

          <div v-if="topPatterns.length === 0" class="text-center py-12 text-gray-500">
            <div class="text-4xl mb-4">🤷</div>
            <p>Aucun pattern appris pour le moment</p>
            <p class="text-xs mt-2">
              Les patterns seront créés automatiquement lors des interactions
            </p>
          </div>

          <div v-else class="space-y-3">
            <div
              v-for="(pattern, index) in topPatterns"
              :key="index"
              class="bg-gray-800/50 border border-gray-700 rounded-lg p-4 hover:border-gray-600 transition-all cursor-pointer"
              @click="expandedPattern = expandedPattern === index ? null : index"
            >
              <div class="flex items-start justify-between">
                <div class="flex-1">
                  <div class="flex items-center gap-2 mb-2">
                    <span class="text-xs font-mono bg-blue-500/20 text-blue-300 px-2 py-1 rounded">
                      {{ pattern.problem_type || 'Pattern' }}
                    </span>
                    <span v-if="pattern.success_rate" class="text-xs text-gray-400">
                      {{ Math.round(pattern.success_rate * 100) }}% succès
                    </span>
                  </div>

                  <div v-if="expandedPattern === index" class="mt-3 space-y-2">
                    <div v-if="pattern.solution_steps?.length" class="text-xs text-gray-400">
                      <span class="font-semibold">Étapes:</span>
                      <ol class="list-decimal list-inside mt-1 space-y-1">
                        <li v-for="(step, i) in pattern.solution_steps" :key="i">{{ step }}</li>
                      </ol>
                    </div>
                    <div v-if="pattern.tools_sequence?.length" class="text-xs text-gray-400">
                      <span class="font-semibold">Outils:</span>
                      <div class="flex flex-wrap gap-1 mt-1">
                        <span
                          v-for="(tool, i) in pattern.tools_sequence"
                          :key="i"
                          class="bg-gray-700 px-2 py-0.5 rounded"
                        >
                          {{ tool }}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div v-else class="text-sm text-gray-300 line-clamp-2">
                    {{ pattern.pattern || 'Pattern sans description' }}
                  </div>
                </div>

                <div class="flex items-center gap-3 ml-4">
                  <div class="text-right">
                    <div class="text-xs text-gray-400">Utilisé</div>
                    <div class="text-lg font-bold text-blue-400">{{ pattern.usage_count }}×</div>
                  </div>
                  <svg
                    class="w-5 h-5 text-gray-500 transition-transform"
                    :class="{ 'rotate-180': expandedPattern === index }"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M19 9l-7 7-7-7"
                    />
                  </svg>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- System Stats -->
        <div class="bg-gray-900/50 border border-gray-800 rounded-xl p-6">
          <h2 class="text-xl font-bold text-white mb-4">⚙️ Statistiques Système</h2>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div class="bg-gray-800/50 rounded-lg p-4">
              <div class="text-xs text-gray-400 mb-1">Expériences</div>
              <div class="text-2xl font-bold text-white">
                {{ learningStats?.experiences_count || 0 }}
              </div>
            </div>
            <div class="bg-gray-800/50 rounded-lg p-4">
              <div class="text-xs text-gray-400 mb-1">Patterns</div>
              <div class="text-2xl font-bold text-white">
                {{ learningStats?.patterns_count || 0 }}
              </div>
            </div>
            <div class="bg-gray-800/50 rounded-lg p-4">
              <div class="text-xs text-gray-400 mb-1">Corrections</div>
              <div class="text-2xl font-bold text-white">
                {{ learningStats?.corrections_count || 0 }}
              </div>
            </div>
            <div class="bg-gray-800/50 rounded-lg p-4">
              <div class="text-xs text-gray-400 mb-1">État ChromaDB</div>
              <div
                class="text-sm font-bold"
                :class="learningStats?.status === 'connected' ? 'text-green-400' : 'text-red-400'"
              >
                {{ learningStats?.status === 'connected' ? '✓ Connecté' : '✗ Déconnecté' }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/services/api'

const loading = ref(true)
const error = ref(null)
const learningStats = ref(null)
const feedbackStats = ref(null)
const topPatterns = ref([])
const expandedPattern = ref(null)

function getPercentage(value) {
  const total = feedbackStats.value?.total || 0
  if (total === 0) return 0
  return Math.round((value / total) * 100)
}

async function loadData() {
  loading.value = true
  error.value = null

  try {
    // Charger stats en parallèle
    const [statsRes, feedbackRes] = await Promise.all([
      api.get('/learning/stats'),
      api.get('/learning/feedback/stats?hours=24'),
    ])

    learningStats.value = statsRes
    feedbackStats.value = feedbackRes

    console.log('Learning stats loaded:', learningStats.value)
    console.log('Feedback stats loaded:', feedbackStats.value)

    // Charger patterns
    await loadPatterns()
  } catch (err) {
    console.error('Erreur chargement données learning:', err)
    error.value = err.response?.data?.detail || err.message || 'Erreur de chargement'
  } finally {
    loading.value = false
  }
}

async function loadPatterns() {
  try {
    const response = await api.get('/learning/patterns?limit=10')
    topPatterns.value = response.patterns || []
  } catch (err) {
    console.error('Erreur chargement patterns:', err)
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
