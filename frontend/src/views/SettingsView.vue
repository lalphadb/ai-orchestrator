<template>
  <div class="max-w-3xl mx-auto p-6">
    <h1 class="text-2xl font-semibold text-white mb-6">Paramètres</h1>
    
    <!-- Model Settings -->
    <section class="mb-8 p-6 bg-gray-800/50 rounded-xl border border-gray-700/50">
      <h2 class="text-lg font-medium text-white mb-4 flex items-center gap-2">
        <svg class="w-5 h-5 text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
        </svg>
        Modèle IA
      </h2>
      
      <div class="space-y-4">
        <div>
          <label class="block text-sm text-gray-400 mb-2">Modèle par défaut</label>
          <select
            v-model="chat.currentModel"
            class="w-full px-4 py-2 bg-gray-900/50 border border-gray-700/50 rounded-lg text-gray-200 focus:outline-none focus:border-primary-500/50"
          >
            <option v-for="model in chat.availableModels" :key="model.name || model" :value="model.name || model">
              {{ model.name || model }}
            </option>
          </select>
          <p class="mt-1 text-xs text-gray-500">
            Ce modèle sera utilisé par défaut pour les nouvelles conversations
          </p>
        </div>
        
        <div>
          <label class="block text-sm text-gray-400 mb-2">Max iterations (ReAct)</label>
          <input
            type="number"
            :value="maxIterations"
            disabled
            class="w-32 px-4 py-2 bg-gray-900/50 border border-gray-700/50 rounded-lg text-gray-400 cursor-not-allowed"
          />
          <p class="mt-1 text-xs text-gray-500">
            Configuré côté serveur (env MAX_ITERATIONS)
          </p>
        </div>
      </div>
    </section>
    
    <!-- Display Settings -->
    <section class="mb-8 p-6 bg-gray-800/50 rounded-xl border border-gray-700/50">
      <h2 class="text-lg font-medium text-white mb-4 flex items-center gap-2">
        <svg class="w-5 h-5 text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
        </svg>
        Affichage
      </h2>
      
      <div class="space-y-4">
        <label class="flex items-center justify-between cursor-pointer">
          <div>
            <span class="text-gray-200">Afficher les étapes de réflexion</span>
            <p class="text-xs text-gray-500 mt-0.5">Montre le raisonnement de l'IA dans l'inspecteur</p>
          </div>
          <div class="relative">
            <input 
              type="checkbox" 
              :checked="chat.settings.showThinking"
              @change="chat.updateSettings('showThinking', $event.target.checked)"
              class="sr-only peer"
            />
            <div class="w-11 h-6 bg-gray-700 rounded-full peer peer-checked:bg-primary-600 transition-colors"></div>
            <div class="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5"></div>
          </div>
        </label>
        
        <label class="flex items-center justify-between cursor-pointer">
          <div>
            <span class="text-gray-200">Afficher les paramètres des outils</span>
            <p class="text-xs text-gray-500 mt-0.5">Montre les paramètres passés aux outils</p>
          </div>
          <div class="relative">
            <input 
              type="checkbox" 
              :checked="chat.settings.showToolParams"
              @change="chat.updateSettings('showToolParams', $event.target.checked)"
              class="sr-only peer"
            />
            <div class="w-11 h-6 bg-gray-700 rounded-full peer peer-checked:bg-primary-600 transition-colors"></div>
            <div class="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5"></div>
          </div>
        </label>
        
        <label class="flex items-center justify-between cursor-pointer">
          <div>
            <span class="text-gray-200">Mode compact</span>
            <p class="text-xs text-gray-500 mt-0.5">Réduit l'espacement pour afficher plus de contenu</p>
          </div>
          <div class="relative">
            <input 
              type="checkbox" 
              :checked="chat.settings.compactMode"
              @change="chat.updateSettings('compactMode', $event.target.checked)"
              class="sr-only peer"
            />
            <div class="w-11 h-6 bg-gray-700 rounded-full peer peer-checked:bg-primary-600 transition-colors"></div>
            <div class="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5"></div>
          </div>
        </label>
      </div>
    </section>
    
    <!-- Account -->
    <section class="mb-8 p-6 bg-gray-800/50 rounded-xl border border-gray-700/50">
      <h2 class="text-lg font-medium text-white mb-4 flex items-center gap-2">
        <svg class="w-5 h-5 text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"/>
        </svg>
        Compte
      </h2>
      
      <div v-if="auth.isAuthenticated" class="space-y-4">
        <div class="flex items-center gap-4">
          <div class="w-12 h-12 rounded-full bg-primary-600/20 flex items-center justify-center">
            <span class="text-xl font-semibold text-primary-400">
              {{ auth.user?.username?.[0]?.toUpperCase() }}
            </span>
          </div>
          <div>
            <p class="font-medium text-white">{{ auth.user?.username }}</p>
            <p class="text-sm text-gray-400">{{ auth.user?.email }}</p>
            <p v-if="auth.isAdmin" class="text-xs text-primary-400 mt-0.5">Administrateur</p>
          </div>
        </div>
        
        <button
          @click="auth.logout(); $router.push('/login')"
          class="px-4 py-2 bg-red-600/20 hover:bg-red-600/30 text-red-400 rounded-lg transition-colors"
        >
          Se déconnecter
        </button>
      </div>
      
      <div v-else>
        <router-link
          to="/login"
          class="inline-block px-4 py-2 bg-primary-600 hover:bg-primary-500 text-white rounded-lg transition-colors"
        >
          Se connecter
        </router-link>
      </div>
    </section>
    
    <!-- About -->
    <section class="p-6 bg-gray-800/50 rounded-xl border border-gray-700/50">
      <h2 class="text-lg font-medium text-white mb-4 flex items-center gap-2">
        <svg class="w-5 h-5 text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
        </svg>
        À propos
      </h2>
      
      <div class="space-y-2 text-sm">
        <p class="text-gray-300">
          <span class="text-gray-500">Version:</span> AI Orchestrator v7.0
        </p>
        <p class="text-gray-300">
          <span class="text-gray-500">Backend:</span> FastAPI + ReAct Engine
        </p>
        <p class="text-gray-300">
          <span class="text-gray-500">Frontend:</span> Vue 3 + Tailwind CSS
        </p>
        <p class="text-gray-400 mt-4 text-xs">
          Un orchestrateur IA autonome avec boucle ReAct, exécution d'outils et streaming en temps réel.
        </p>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useChatStore } from '@/stores/chat'
import { useAuthStore } from '@/stores/auth'

const chat = useChatStore()
const auth = useAuthStore()

const maxIterations = ref(10) // Default, could be fetched from backend

onMounted(() => {
  chat.fetchModels()
})
</script>
