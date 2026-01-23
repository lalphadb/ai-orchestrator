<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-gray-100">
    <!-- Header -->
    <header class="fixed top-0 left-0 right-0 z-50 bg-gray-900/80 backdrop-blur-md border-b border-gray-700/50">
      <div class="max-w-full mx-auto px-4 h-14 flex items-center justify-between">
        <!-- Logo -->
        <div class="flex items-center gap-3">
          <router-link to="/" class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-primary-500 to-purple-600 flex items-center justify-center">
              <span class="text-white font-bold text-lg">AI</span>
            </div>
            <span class="font-semibold text-lg bg-gradient-to-r from-white to-gray-400 bg-clip-text text-transparent">
              Orchestrator v7.0
            </span>
          </router-link>
        </div>
        
        <!-- Navigation -->
        <nav class="flex items-center gap-2">
          <router-link 
            to="/" 
            class="px-3 py-1.5 rounded-lg text-sm hover:bg-gray-700/50 transition-colors"
            :class="$route.path === '/' ? 'bg-gray-700/50 text-white' : 'text-gray-400'"
          >
            <span class="flex items-center gap-1.5">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"/>
              </svg>
              Chat
            </span>
          </router-link>
          
          <router-link
            to="/tools"
            class="px-3 py-1.5 rounded-lg text-sm hover:bg-gray-700/50 transition-colors"
            :class="$route.path === '/tools' ? 'bg-gray-700/50 text-white' : 'text-gray-400'"
          >
            <span class="flex items-center gap-1.5">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"/>
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
              </svg>
              Outils
            </span>
          </router-link>

          <router-link
            to="/learning"
            class="px-3 py-1.5 rounded-lg text-sm hover:bg-gray-700/50 transition-colors"
            :class="$route.path === '/learning' ? 'bg-gray-700/50 text-white' : 'text-gray-400'"
          >
            <span class="flex items-center gap-1.5">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/>
              </svg>
              Apprentissage
            </span>
          </router-link>

          <router-link
            to="/settings"
            class="px-3 py-1.5 rounded-lg text-sm hover:bg-gray-700/50 transition-colors"
            :class="$route.path === '/settings' ? 'bg-gray-700/50 text-white' : 'text-gray-400'"
          >
            <span class="flex items-center gap-1.5">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"/>
              </svg>
              Paramètres
            </span>
          </router-link>
        </nav>
        
        <!-- Right side -->
        <div class="flex items-center gap-4">
          <!-- Status -->
          <StatusBar />
          
          <!-- User -->
          <div v-if="auth.isAuthenticated" class="flex items-center gap-2 pl-4 border-l border-gray-700">
            <div class="w-7 h-7 rounded-full bg-primary-600/20 flex items-center justify-center">
              <span class="text-sm font-medium text-primary-400">
                {{ auth.user?.username?.[0]?.toUpperCase() }}
              </span>
            </div>
            <span class="text-sm text-gray-400 hidden sm:inline">{{ auth.user?.username }}</span>
            <button 
              @click="handleLogout"
              class="p-1 text-gray-500 hover:text-red-400 transition-colors"
              title="Déconnexion"
            >
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/>
              </svg>
            </button>
          </div>
          <router-link 
            v-else
            to="/login"
            class="px-3 py-1.5 rounded-lg text-sm bg-primary-600 text-white hover:bg-primary-500 transition-colors"
          >
            Connexion
          </router-link>
        </div>
      </div>
    </header>
    
    <!-- Main Content -->
    <main class="pt-14">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useChatStore } from '@/stores/chat'
import StatusBar from '@/components/common/StatusBar.vue'

const router = useRouter()
const auth = useAuthStore()
const chat = useChatStore()

onMounted(async () => {
  // Check session validity
  if (auth.isAuthenticated) {
    await auth.checkSession()
  }
  
  // Load models
  chat.fetchModels()
})

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>
