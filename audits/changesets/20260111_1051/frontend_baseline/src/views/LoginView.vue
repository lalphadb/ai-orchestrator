<template>
  <div class="min-h-[calc(100vh-3.5rem)] flex items-center justify-center p-4">
    <div class="w-full max-w-md">
      <!-- Logo -->
      <div class="text-center mb-8">
        <div class="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-primary-500 to-purple-600 flex items-center justify-center">
          <span class="text-white text-2xl font-bold">AI</span>
        </div>
        <h1 class="text-2xl font-semibold text-white">AI Orchestrator</h1>
        <p class="text-gray-400 mt-2">Connectez-vous pour continuer</p>
      </div>
      
      <!-- Tabs -->
      <div class="flex mb-6 bg-gray-800/50 rounded-lg p-1">
        <button
          @click="mode = 'login'"
          class="flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors"
          :class="mode === 'login' ? 'bg-primary-600 text-white' : 'text-gray-400 hover:text-white'"
        >
          Connexion
        </button>
        <button
          @click="mode = 'register'"
          class="flex-1 py-2 px-4 rounded-md text-sm font-medium transition-colors"
          :class="mode === 'register' ? 'bg-primary-600 text-white' : 'text-gray-400 hover:text-white'"
        >
          Inscription
        </button>
      </div>
      
      <!-- Form -->
      <form @submit.prevent="submit" class="space-y-4">
        <div>
          <label class="block text-sm text-gray-400 mb-1">Nom d'utilisateur</label>
          <input
            v-model="username"
            type="text"
            required
            class="w-full px-4 py-3 bg-gray-800/50 border border-gray-700/50 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-primary-500/50"
            placeholder="Entrez votre nom d'utilisateur"
          />
        </div>
        
        <div v-if="mode === 'register'">
          <label class="block text-sm text-gray-400 mb-1">Email</label>
          <input
            v-model="email"
            type="email"
            required
            class="w-full px-4 py-3 bg-gray-800/50 border border-gray-700/50 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-primary-500/50"
            placeholder="Entrez votre email"
          />
        </div>
        
        <div>
          <label class="block text-sm text-gray-400 mb-1">Mot de passe</label>
          <input
            v-model="password"
            type="password"
            required
            class="w-full px-4 py-3 bg-gray-800/50 border border-gray-700/50 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-primary-500/50"
            placeholder="Entrez votre mot de passe"
          />
        </div>
        
        <!-- Error -->
        <div v-if="error" class="p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
          {{ error }}
        </div>
        
        <!-- Submit -->
        <button
          type="submit"
          :disabled="auth.loading"
          class="w-full py-3 bg-primary-600 hover:bg-primary-500 disabled:opacity-50 text-white font-medium rounded-lg transition-colors flex items-center justify-center gap-2"
        >
          <div v-if="auth.loading" class="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          <span>{{ mode === 'login' ? 'Se connecter' : "S'inscrire" }}</span>
        </button>
      </form>
      
      <!-- Demo hint -->
      <p class="mt-6 text-center text-sm text-gray-500">
        Première utilisation ? <br/>
        <span class="text-gray-400">Créez un compte via l'inscription</span>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const mode = ref('login')
const username = ref('')
const email = ref('')
const password = ref('')
const error = ref('')

async function submit() {
  error.value = ''
  
  try {
    if (mode.value === 'login') {
      await auth.login(username.value, password.value)
    } else {
      await auth.register(username.value, password.value, email.value)
    }
    router.push('/')
  } catch (e) {
    error.value = e.message
  }
}
</script>
