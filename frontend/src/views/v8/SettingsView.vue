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
            d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
          />
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
          />
        </svg>
        Settings
      </h1>
      <p class="body-default" style="color: var(--text-secondary); margin-top: var(--space-1)">
        Configuration du modele et de l'affichage
      </p>
    </header>

    <div class="flex-1 overflow-auto" style="max-width: 800px">
      <!-- Model Settings -->
      <GlassCard variant="bordered" padding="lg" style="margin-bottom: var(--space-6)">
        <h2 class="heading-3 flex items-center gap-2" style="margin-bottom: var(--space-4)">
          <svg
            class="w-5 h-5"
            style="color: var(--accent-primary)"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
            />
          </svg>
          Modele IA
        </h2>

        <div class="space-y-4">
          <div>
            <label
              class="label block"
              style="color: var(--text-secondary); margin-bottom: var(--space-2)"
              >Modele par defaut</label
            >
            <select
              v-model="chat.currentModel"
              class="body-default w-full px-4 py-2"
              style="
                background: var(--bg-deep);
                border: 1px solid var(--border-default);
                border-radius: var(--radius-lg);
                color: var(--text-primary);
              "
            >
              <option
                v-for="model in chat.availableModels"
                :key="model.name || model"
                :value="model.name || model"
              >
                {{ model.name || model }}
              </option>
            </select>
            <p class="label" style="margin-top: var(--space-1); color: var(--text-tertiary)">
              Ce modele sera utilise par defaut pour les nouvelles conversations
            </p>
          </div>

          <div>
            <label
              class="label block"
              style="color: var(--text-secondary); margin-bottom: var(--space-2)"
              >Max iterations (ReAct)</label
            >
            <input
              type="number"
              :value="maxIterations"
              disabled
              class="body-default w-32 px-4 py-2"
              style="
                background: var(--bg-deep);
                border: 1px solid var(--border-default);
                border-radius: var(--radius-lg);
                color: var(--text-secondary);
                cursor: not-allowed;
              "
            />
            <p class="label" style="margin-top: var(--space-1); color: var(--text-tertiary)">
              Configure cote serveur (env MAX_ITERATIONS)
            </p>
          </div>
        </div>
      </GlassCard>

      <!-- Display Settings -->
      <GlassCard variant="bordered" padding="lg" style="margin-bottom: var(--space-6)">
        <h2 class="heading-3 flex items-center gap-2" style="margin-bottom: var(--space-4)">
          <svg
            class="w-5 h-5"
            style="color: var(--accent-primary)"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
            />
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
            />
          </svg>
          Affichage
        </h2>

        <div class="space-y-4">
          <label class="flex items-center justify-between cursor-pointer">
            <div>
              <span class="body-default" style="color: var(--text-primary)"
                >Afficher les etapes de reflexion</span
              >
              <p class="label" style="color: var(--text-tertiary); margin-top: var(--space-1)">
                Montre le raisonnement de l'IA dans l'inspecteur
              </p>
            </div>
            <div class="relative">
              <input
                type="checkbox"
                :checked="chat.settings.showThinking"
                class="sr-only peer"
                @change="chat.updateSettings('showThinking', $event.target.checked)"
              />
              <div
                class="w-11 h-6 rounded-full transition-colors"
                style="background: var(--bg-deep)"
                :style="chat.settings.showThinking && { background: 'var(--accent-primary)' }"
              ></div>
              <div
                class="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform"
                :style="chat.settings.showThinking && { transform: 'translateX(1.25rem)' }"
              ></div>
            </div>
          </label>

          <label class="flex items-center justify-between cursor-pointer">
            <div>
              <span class="body-default" style="color: var(--text-primary)"
                >Afficher les parametres des outils</span
              >
              <p class="label" style="color: var(--text-tertiary); margin-top: var(--space-1)">
                Montre les parametres passes aux outils
              </p>
            </div>
            <div class="relative">
              <input
                type="checkbox"
                :checked="chat.settings.showToolParams"
                class="sr-only peer"
                @change="chat.updateSettings('showToolParams', $event.target.checked)"
              />
              <div
                class="w-11 h-6 rounded-full transition-colors"
                style="background: var(--bg-deep)"
                :style="chat.settings.showToolParams && { background: 'var(--accent-primary)' }"
              ></div>
              <div
                class="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform"
                :style="chat.settings.showToolParams && { transform: 'translateX(1.25rem)' }"
              ></div>
            </div>
          </label>

          <label class="flex items-center justify-between cursor-pointer">
            <div>
              <span class="body-default" style="color: var(--text-primary)">Mode compact</span>
              <p class="label" style="color: var(--text-tertiary); margin-top: var(--space-1)">
                Reduit l'espacement pour afficher plus de contenu
              </p>
            </div>
            <div class="relative">
              <input
                type="checkbox"
                :checked="chat.settings.compactMode"
                class="sr-only peer"
                @change="chat.updateSettings('compactMode', $event.target.checked)"
              />
              <div
                class="w-11 h-6 rounded-full transition-colors"
                style="background: var(--bg-deep)"
                :style="chat.settings.compactMode && { background: 'var(--accent-primary)' }"
              ></div>
              <div
                class="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform"
                :style="chat.settings.compactMode && { transform: 'translateX(1.25rem)' }"
              ></div>
            </div>
          </label>
        </div>
      </GlassCard>

      <!-- Account -->
      <GlassCard variant="bordered" padding="lg" style="margin-bottom: var(--space-6)">
        <h2 class="heading-3 flex items-center gap-2" style="margin-bottom: var(--space-4)">
          <svg
            class="w-5 h-5"
            style="color: var(--accent-primary)"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
            />
          </svg>
          Compte
        </h2>

        <div v-if="auth.isAuthenticated" class="space-y-4">
          <div class="flex items-center gap-4">
            <div
              class="w-12 h-12 rounded-full flex items-center justify-center"
              style="background: rgba(139, 92, 246, 0.2)"
            >
              <span class="heading-3" style="color: var(--accent-primary)">
                {{ auth.user?.username?.[0]?.toUpperCase() }}
              </span>
            </div>
            <div>
              <p class="body-default" style="color: var(--text-primary)">{{ auth.user?.username }}</p>
              <p class="body-small" style="color: var(--text-secondary)">{{ auth.user?.email }}</p>
              <p
                v-if="auth.isAdmin"
                class="label"
                style="color: var(--accent-primary); margin-top: var(--space-1)"
              >
                Administrateur
              </p>
            </div>
          </div>

          <ModernButton variant="danger" size="md" @click="handleLogout">
            Se deconnecter
          </ModernButton>
        </div>

        <div v-else>
          <router-link to="/login">
            <ModernButton variant="primary" size="md"> Se connecter </ModernButton>
          </router-link>
        </div>
      </GlassCard>

      <!-- About -->
      <GlassCard variant="bordered" padding="lg">
        <h2 class="heading-3 flex items-center gap-2" style="margin-bottom: var(--space-4)">
          <svg
            class="w-5 h-5"
            style="color: var(--accent-primary)"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          A propos
        </h2>

        <div class="space-y-2 body-small">
          <p style="color: var(--text-primary)">
            <span style="color: var(--text-tertiary)">Version:</span> AI Orchestrator v8.1
          </p>
          <p style="color: var(--text-primary)">
            <span style="color: var(--text-tertiary)">Backend:</span> FastAPI + ReAct Engine
          </p>
          <p style="color: var(--text-primary)">
            <span style="color: var(--text-tertiary)">Frontend:</span> Vue 3 + Neural Glow
          </p>
          <p style="color: var(--text-primary)">
            <span style="color: var(--text-tertiary)">Embeddings:</span> bge-m3 (1024 dims)
          </p>
          <p class="label" style="margin-top: var(--space-4); color: var(--text-secondary)">
            Un orchestrateur IA autonome avec boucle ReAct, execution d'outils et streaming en temps
            reel.
          </p>
        </div>
      </GlassCard>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useChatStore } from '@/stores/chat'
import { useAuthStore } from '@/stores/auth'
import GlassCard from '@/components/ui/GlassCard.vue'
import ModernButton from '@/components/ui/ModernButton.vue'

const chat = useChatStore()
const auth = useAuthStore()

const maxIterations = ref(10)

onMounted(() => {
  chat.fetchModels()
})

const handleLogout = () => {
  auth.logout()
  window.location.href = '/login'
}
</script>
