<template>
  <div ref="container" class="flex-1 overflow-y-auto p-4 space-y-4">
    <!-- Empty state -->
    <div
      v-if="messages.length === 0"
      class="h-full flex flex-col items-center justify-center text-center"
    >
      <div
        class="w-16 h-16 mb-4 rounded-2xl bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center"
      >
        <span class="text-white text-2xl font-bold">AI</span>
      </div>
      <h2 class="text-xl font-semibold text-white mb-2">AI Orchestrator v8.0</h2>
      <p class="text-gray-400 max-w-md mb-6">
        Un orchestrateur autonome avec boucle ReAct,<br />capable d'exécuter des outils et
        d'interagir avec votre système.
      </p>
      <div class="grid grid-cols-2 gap-3 max-w-md">
        <button
          v-for="example in examples"
          :key="example"
          class="px-4 py-3 bg-gray-800/50 hover:bg-gray-700/50 border border-gray-700/50 rounded-xl text-sm text-gray-300 text-left transition-colors"
          @click="$emit('send', example)"
        >
          {{ example }}
        </button>
      </div>
    </div>

    <!-- Messages -->
    <div
      v-for="(msg, index) in messages"
      :key="msg.id"
      class="flex gap-3"
      :class="msg.role === 'user' ? 'justify-end' : 'justify-start'"
    >
      <!-- Avatar Assistant -->
      <div v-if="msg.role === 'assistant'" class="flex-shrink-0">
        <div
          class="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center"
        >
          <span class="text-white text-sm font-bold">AI</span>
        </div>
      </div>

      <!-- Message content -->
      <div class="max-w-[80%] rounded-2xl px-4 py-3" :class="getMessageClass(msg)">
        <!-- Streaming indicator -->
        <div v-if="msg.streaming" class="flex items-center gap-2 mb-2 text-purple-300">
          <div
            class="animate-spin w-4 h-4 border-2 border-purple-400 border-t-transparent rounded-full"
          ></div>
          <span class="text-sm">Génération...</span>
        </div>

        <!-- Content: either ModelsDisplay OR regular markdown -->
        <template v-if="msg.role === 'assistant' && !msg.streaming">
          <ModelsDisplay
            v-if="getModelsData(msg.content).isModelsList"
            :models="getModelsData(msg.content).models"
          />
          <div
            v-else
            class="prose prose-invert prose-sm max-w-none message-content"
            v-html="renderContent(msg.content)"
          ></div>
        </template>
        <div
          v-else
          class="prose prose-invert prose-sm max-w-none message-content"
          v-html="renderContent(msg.content)"
        ></div>

        <!-- Meta info + Feedback -->
        <div
          v-if="msg.role === 'assistant' && !msg.streaming"
          class="flex flex-wrap items-center justify-between gap-2 mt-3 pt-2 border-t border-gray-700/50"
        >
          <!-- Meta gauche -->
          <div class="flex flex-wrap items-center gap-2">
            <span v-if="msg.model" class="text-xs text-gray-500">{{ msg.model }}</span>
            <span v-if="msg.duration_ms" class="text-xs text-gray-500">{{
              formatDuration(msg.duration_ms)
            }}</span>
            <span v-if="msg.iterations" class="text-xs text-gray-500"
              >{{ msg.iterations }} iter</span
            >
            <div v-if="msg.tools_used?.length" class="flex flex-wrap gap-1">
              <span
                v-for="t in msg.tools_used"
                :key="t"
                class="px-1.5 py-0.5 bg-gray-700/50 rounded text-xs text-gray-400"
              >
                {{ t }}
              </span>
            </div>
          </div>

          <!-- Feedback buttons droite -->
          <FeedbackButtons
            v-if="msg.content && !msg.isError"
            :message-id="msg.id"
            :query="getQueryForMessage(index)"
            :response="msg.content"
            :tools-used="msg.tools_used || []"
          />
        </div>

        <!-- Verdict badge (si présent) -->
        <div v-if="msg.verdict" class="mt-2 flex items-center gap-2">
          <span
            class="text-xs px-2 py-1 rounded-full"
            :class="
              msg.verdict.status === 'PASS'
                ? 'bg-green-900/50 text-green-300'
                : 'bg-red-900/50 text-red-300'
            "
          >
            {{ msg.verdict.status }}
          </span>
          <span v-if="msg.verdict.confidence" class="text-xs text-gray-500">
            {{ (msg.verdict.confidence * 100).toFixed(0) }}% confiance
          </span>
        </div>

        <!-- Learning indicator -->
        <div
          v-if="msg.learning?.context_used"
          class="mt-2 flex items-center gap-1 text-xs text-purple-400"
        >
          <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
            />
          </svg>
          <span>Enrichi par l'apprentissage</span>
        </div>
      </div>

      <!-- User avatar -->
      <div v-if="msg.role === 'user'" class="flex-shrink-0">
        <div class="w-8 h-8 rounded-lg bg-gray-700 flex items-center justify-center">
          <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
            />
          </svg>
        </div>
      </div>
    </div>

    <!-- Scroll anchor -->
    <div ref="scrollAnchor"></div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import FeedbackButtons from './FeedbackButtons.vue'
import ModelsDisplay from './ModelsDisplay.vue'

const props = defineProps({
  messages: { type: Array, default: () => [] },
})

defineEmits(['send'])

const container = ref(null)
const scrollAnchor = ref(null)

// SECURITY: Configure DOMPurify once for HTML sanitization
DOMPurify.setConfig({
  ALLOWED_TAGS: [
    'p',
    'br',
    'strong',
    'em',
    'u',
    'code',
    'pre',
    'a',
    'ul',
    'ol',
    'li',
    'blockquote',
    'h1',
    'h2',
    'h3',
    'h4',
    'h5',
    'h6',
    'table',
    'thead',
    'tbody',
    'tr',
    'th',
    'td',
    'hr',
    'img',
    'span',
    'div',
    'del',
    'ins',
  ],
  ALLOWED_ATTR: ['href', 'target', 'rel', 'src', 'alt', 'title', 'class', 'id'],
  ALLOWED_URI_REGEXP: /^(?:(?:https?|mailto|tel):)/i, // Block javascript:
  FORBID_TAGS: ['script', 'style', 'iframe', 'object', 'embed', 'form', 'input'],
  FORBID_ATTR: ['onerror', 'onload', 'onclick', 'onmouseover', 'onfocus', 'onblur'],
  KEEP_CONTENT: true,
  RETURN_TRUSTED_TYPE: false,
})

// Cache pour detectModels avec TTL de 5 minutes
const modelsCache = new Map()
const MODEL_CACHE_TTL = 5 * 60 * 1000

/**
 * Version mémorisée de detectModels pour éviter les appels multiples
 */
function getModelsData(content) {
  if (!content) return { isModelsList: false, models: [] }

  // Créer une clé de cache basée sur le contenu (hash simple)
  const cacheKey = content.substring(0, 100) + content.length

  const cached = modelsCache.get(cacheKey)
  if (cached && Date.now() - cached.ts < MODEL_CACHE_TTL) {
    return cached.data
  }

  const result = detectModels(content)
  modelsCache.set(cacheKey, { data: result, ts: Date.now() })

  // Nettoyer le cache s'il devient trop grand
  if (modelsCache.size > 50) {
    const firstKey = modelsCache.keys().next().value
    modelsCache.delete(firstKey)
  }

  return result
}

// Exemples plus orientés workflow
const examples = [
  'Crée un script de monitoring CPU',
  'Liste les conteneurs Docker actifs',
  'Analyse les logs du serveur',
  'Quels modèles LLM sont disponibles ?',
]

// Auto-scroll on new messages
watch(
  () => props.messages,
  () => {
    nextTick(() => {
      scrollAnchor.value?.scrollIntoView({ behavior: 'smooth' })
    })
  },
  { deep: true }
)

// Also watch streaming content
watch(
  () => props.messages[props.messages.length - 1]?.content,
  () => {
    if (props.messages[props.messages.length - 1]?.streaming) {
      nextTick(() => {
        scrollAnchor.value?.scrollIntoView({ behavior: 'smooth' })
      })
    }
  }
)

/**
 * Classes CSS pour le message selon son type
 */
function getMessageClass(msg) {
  if (msg.role === 'user') {
    return 'bg-purple-600 text-white'
  }
  if (msg.isError) {
    return 'bg-red-500/10 border border-red-500/30 text-red-200'
  }
  return 'bg-gray-800/80 text-gray-200'
}

/**
 * NOUVELLE FONCTION: Détection robuste et parsing unifié des modèles
 * Retourne { isModelsList: boolean, models: Array }
 */
function detectModels(content) {
  const result = { isModelsList: false, models: [] }

  if (!content || typeof content !== 'string') return result

  console.log('[DetectModels] Input content:', content.substring(0, 200))

  let cleaned = content.trim()
  const models = []
  const seen = new Set()

  // IMPORTANT: Ne pas détecter si le contenu ressemble à une réponse conversationnelle
  // avec du texte narratif (pas seulement du JSON)
  const hasNarrativeText = /[a-zA-Z]{10,}/.test(
    cleaned.replace(/```[\s\S]*?```/g, '').replace(/\{[\s\S]*?\}/g, '')
  )
  if (hasNarrativeText && cleaned.length > 500) {
    console.log('[DetectModels] ⚠️ Skipping: looks like narrative response, not pure model list')
    return result
  }

  // 1. Try extracting JSON from code blocks first
  const codeBlockMatch = cleaned.match(/```(?:json)?\s*([\s\S]*?)\s*```/)
  if (codeBlockMatch) {
    cleaned = codeBlockMatch[1].trim()
    console.log('[DetectModels] Extracted from code block')
  }

  // 2. Try parsing full JSON object (most robust method)
  try {
    // Find the first { and last } to ignore potential conversational text around JSON
    const start = cleaned.indexOf('{')
    const end = cleaned.lastIndexOf('}')

    console.log('[DetectModels] JSON bounds:', { start, end, length: cleaned.length })

    if (start !== -1 && end !== -1) {
      const jsonStr = cleaned.substring(start, end + 1)
      console.log('[DetectModels] Extracted JSON:', jsonStr.substring(0, 300))
      const parsed = JSON.parse(jsonStr)
      console.log('[DetectModels] Parsed successfully:', Object.keys(parsed))

      // SKIP tool output format - these should be displayed as regular text, not as ModelsDisplay
      if (parsed.tool || parsed.output?.tool) {
        console.log('[DetectModels] ⚠️ Skipping: tool output format detected')
        return result
      }

      // Format 1: { models: [...] }
      if (parsed.models && Array.isArray(parsed.models)) {
        for (const m of parsed.models) {
          if (m.name && !seen.has(m.name)) {
            seen.add(m.name)
            models.push({
              name: m.name,
              size: m.size || 0,
              modified_at: m.modified_at || null,
              available: m.available !== false,
            })
          }
        }
      }
      // Format 2: Direct array of models [...]
      else if (Array.isArray(parsed)) {
        for (const m of parsed) {
          if (m.name && !seen.has(m.name)) {
            seen.add(m.name)
            models.push({
              name: m.name,
              size: m.size || 0,
              modified_at: m.modified_at || null,
              available: m.available !== false,
            })
          }
        }
      }

      if (models.length > 0) {
        console.log('[DetectModels] ✅ Found models:', models.length)
        result.isModelsList = true
        result.models = models
        return result
      }
      console.log('[DetectModels] ⚠️ Parsed JSON but no models found')
    }
  } catch (_e) {
    // JSON parse error, continue to fallbacks
  }

  // MÉTHODE 3: Détection de lignes JSON individuelles (fallback)
  // Pattern: { "name": "xxx", "size": 123, ... } sur chaque ligne
  const linePattern =
    /\{\s*"name"\s*:\s*"([^"]+)"\s*,\s*"size"\s*:\s*(\d+)\s*,\s*"modified_at"\s*:\s*"?([^",}]*)"?\s*,\s*"available"\s*:\s*(true|false)\s*\}/gi
  let match
  while ((match = linePattern.exec(cleaned)) !== null) {
    const name = match[1]
    if (!seen.has(name)) {
      seen.add(name)
      models.push({
        name: name,
        size: parseInt(match[2]),
        modified_at: match[3] === 'null' ? null : match[3],
        available: match[4].toLowerCase() === 'true',
      })
    }
  }

  if (models.length >= 3) {
    result.isModelsList = true
    result.models = models
    return result
  }

  // MÉTHODE 4: Détection par noms de modèles connus (dernier recours)
  const knownModelPatterns = [
    /llama\d*\.?\d*[:-]?[\w-]*/gi,
    /qwen\d*\.?\d*[:-]?[\w-]*/gi,
    /deepseek[:-]?[\w-]*/gi,
    /gemini[:-]?[\w-]*/gi,
    /kimi[:-]?[\w-]*/gi,
    /nomic[:-]?[\w-]*/gi,
    /bge[:-]?[\w-]*/gi,
    /mxbai[:-]?[\w-]*/gi,
    /safeguard[:-]?[\w-]*/gi,
  ]

  for (const pattern of knownModelPatterns) {
    const matches = cleaned.match(pattern)
    if (matches) {
      for (const m of matches) {
        const normalized = m.toLowerCase()
        if (!seen.has(normalized) && normalized.length > 3) {
          seen.add(normalized)
          models.push({
            name: m,
            size: 0,
            modified_at: null,
            available: true,
          })
        }
      }
    }
  }

  // MÉTHODE 5: Extraction simple name/size si beaucoup de paires trouvées
  if (models.length < 3) {
    const simpleNamePattern = /"name"\s*:\s*"([^"]+)"/g
    const simpleSizePattern = /"size"\s*:\s*(\d+)/g

    const names = []
    const sizes = []

    while ((match = simpleNamePattern.exec(cleaned)) !== null) {
      names.push(match[1])
    }
    while ((match = simpleSizePattern.exec(cleaned)) !== null) {
      sizes.push(parseInt(match[1]))
    }

    // Si on a au moins 5 noms, c'est probablement une liste de modèles
    if (names.length >= 5) {
      models.length = 0 // Reset
      seen.clear()
      for (let i = 0; i < names.length; i++) {
        if (!seen.has(names[i])) {
          seen.add(names[i])
          models.push({
            name: names[i],
            size: sizes[i] || 0,
            modified_at: null,
            available: true,
          })
        }
      }
    }
  }

  // Décision finale: au moins 5 modèles ou présence de mots-clés LLM spécifiques
  if (models.length >= 5) {
    result.isModelsList = true
    result.models = models
  } else if (
    models.length >= 1 &&
    (cleaned.includes('ollama') ||
      cleaned.includes('modèle') ||
      cleaned.includes('LLM') ||
      cleaned.includes('available'))
  ) {
    result.isModelsList = true
    result.models = models
  }

  console.log('[DetectModels] Final result:', result.isModelsList, 'models:', result.models.length)
  return result
}

/**
 * Détection améliorée du Markdown
 */
function isMarkdown(content) {
  if (!content) return false

  const mdPatterns = [
    /```[\s\S]*?```/,
    /\*\*[^*]+\*\*/,
    /\*[^*]+\*/,
    /^#{1,6}\s/m,
    /^\s*[-*+]\s/m,
    /^\s*\d+\.\s/m,
    /\[([^\]]+)\]\([^)]+\)/,
    /`[^`]+`/,
    /^\s*>/m,
    /\|.+\|/,
  ]

  return mdPatterns.some((pattern) => pattern.test(content))
}

/**
 * Rendu du contenu avec Markdown ou texte brut
 * SECURITY: Sanitized with DOMPurify to prevent XSS
 */
const MAX_RENDER_LENGTH = 100000 // 100KB max pour le rendu markdown

function renderContent(content) {
  if (!content) return ''

  // Protection performance: tronquer les contenus trop longs
  if (content.length > MAX_RENDER_LENGTH) {
    content =
      content.substring(0, MAX_RENDER_LENGTH) +
      '\n\n*[Contenu tronqué — trop volumineux pour le rendu]*'
  }

  // Si c'est une liste de modèles, ne pas render (sera géré par ModelsDisplay)
  if (getModelsData(content).isModelsList) {
    console.log('[RenderContent] Liste de modèles détectée - rendu vide')
    return ''
  }

  // NETTOYAGE AMÉLIORÉ du JSON brut
  let cleanedContent = content

  // 1. Enlever les gros blocs JSON finaux (>200 caractères)
  const lastJsonBlockMatch = cleanedContent.match(/^([\s\S]*?)(\n\n+|\n)(\{[\s\S]{200,}\})\s*$/m)
  if (lastJsonBlockMatch) {
    cleanedContent = lastJsonBlockMatch[1].trim()
  }

  // 2. Enlever les blocs JSON multi-lignes complets (objets avec accolades imbriquées)
  cleanedContent = cleanedContent.replace(
    /\{[\s\S]*?"(?:models|data|output|success|tool|error|meta)"\s*:[\s\S]*?\}(?:\s*[,}\]])?/g,
    (match) => {
      // Supprimer si c'est du JSON structuré (>80 chars OU plusieurs lignes)
      if (match.length > 80 || match.split('\n').length > 3) {
        console.log('[RenderContent] JSON bloc supprimé:', match.substring(0, 50) + '...')
        return ''
      }
      return match
    }
  )

  // 3. Enlever les blocs JSON bruts de type {"tool": "...", "output": {...}}
  cleanedContent = cleanedContent.replace(/\{\s*"tool"\s*:\s*"[^"]*"[\s\S]*?\}(?:\s*[,}\]])+/g, '')

  // 4. Enlever les lignes JSON individuelles (format {"name": "...", "size": ...})
  cleanedContent = cleanedContent.replace(
    /^\s*\{\s*"(?:name|tool|success|data|error|meta|duration|size|available|modified_at)"[^\n]*\}\s*,?\s*$/gm,
    ''
  )

  // 5. Enlever les blocs de code JSON (```json ... ```)
  cleanedContent = cleanedContent.replace(/```json[\s\S]*?```/g, '')

  // 6. NOUVEAU: Enlever les tableaux JSON compacts sur une seule ligne
  cleanedContent = cleanedContent.replace(/\[(?:\{[^}]{20,}\},?\s*){3,}\]/g, '')

  // 7. Enlever les objets JSON inline restants qui ressemblent à des données brutes
  cleanedContent = cleanedContent.replace(
    /"(?:name|size|available|modified_at|tool|success|error|data)"\s*:\s*(?:"[^"]*"|\d+|true|false|null)/g,
    ''
  )

  // 8. Nettoyer les virgules orphelines, accolades et crochets isolés
  // eslint-disable-next-line no-useless-escape
  cleanedContent = cleanedContent.replace(/[{}\[\]],?\s*[{}\[\]]/g, '')
  cleanedContent = cleanedContent.replace(/^[\s,{}[\]:]+$/gm, '')
  // eslint-disable-next-line no-useless-escape
  cleanedContent = cleanedContent.replace(/[,\s]*[{}\[\]]\s*$/gm, '')

  // 9. Nettoyer les lignes vides multiples
  cleanedContent = cleanedContent.replace(/\n{3,}/g, '\n\n').trim()

  // 9b. CRITIQUE: Nettoyer les \n échappés et autre contenu échappé
  // Remplacer les \n littéraux par de vrais retours à la ligne
  cleanedContent = cleanedContent.replace(/\\n/g, '\n')
  // Nettoyer les \" échappés
  cleanedContent = cleanedContent.replace(/\\"/g, '"')
  // Nettoyer les \\ échappés
  cleanedContent = cleanedContent.replace(/\\\\/g, '')

  // 9c. CRITIQUE: Supprimer les gros blocs JSON tool avec du contenu échappé
  // Pattern: {"tool": "write_file", "params": {"path": "...", "content": "...\n...\n..."}}
  cleanedContent = cleanedContent.replace(
    /\{\s*"tool"\s*:\s*"[^"]*"\s*,\s*"params"\s*:\s*\{[^}]{100,}\}\s*\}/g,
    ''
  )

  // 9d. Supprimer les lignes qui sont juste des échappements ou du JSON partiel
  cleanedContent = cleanedContent.replace(/^[\s\\n]+$/gm, '')

  // 9e. Nettoyer à nouveau les lignes vides après tous ces remplacements
  cleanedContent = cleanedContent.replace(/\n{3,}/g, '\n\n').trim()

  // 10. Si après nettoyage il ne reste rien ou que du bruit
  if (!cleanedContent.trim() || cleanedContent.trim().length < 10) {
    return '<em class="text-gray-500">Tâche exécutée avec succès</em>'
  }

  // Traitement Markdown
  if (isMarkdown(cleanedContent)) {
    marked.setOptions({
      breaks: true,
      gfm: true,
      headerIds: false,
      mangle: false,
      sanitize: false,
    })

    const rawHtml = marked.parse(cleanedContent)

    // SECURITY: Sanitize HTML to prevent XSS attacks
    const sanitized = DOMPurify.sanitize(rawHtml)

    if (import.meta.env.DEV) {
      // Debug: log if DOMPurify modified the HTML
      if (rawHtml !== sanitized) {
        console.warn('[SECURITY] DOMPurify sanitized HTML:', {
          original: rawHtml.substring(0, 100),
          sanitized: sanitized.substring(0, 100),
        })
      }
    }

    return sanitized
  }

  // Texte brut: échapper HTML et préserver les sauts de ligne
  return escapeHtml(cleanedContent).replace(/\n/g, '<br>')
}

/**
 * Échapper le HTML pour éviter les injections
 */
function escapeHtml(text) {
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}

function formatDuration(ms) {
  if (!ms) return ''
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

/**
 * Récupère la question utilisateur correspondant à une réponse assistant
 */
function getQueryForMessage(assistantIndex) {
  for (let i = assistantIndex - 1; i >= 0; i--) {
    if (props.messages[i].role === 'user') {
      return props.messages[i].content
    }
  }
  return ''
}
</script>

<style>
.message-content {
  line-height: 1.6;
  word-wrap: break-word;
  overflow-wrap: break-word;
}

.prose pre {
  @apply bg-gray-900/80 rounded-lg p-3 overflow-x-auto my-2;
}

.prose code {
  @apply bg-gray-700/50 px-1.5 py-0.5 rounded text-sm;
}

.prose pre code {
  @apply bg-transparent p-0;
}

.prose p {
  @apply mb-2;
}

.prose ul,
.prose ol {
  @apply pl-5 mb-2;
}

.prose li {
  @apply mb-1;
}

.prose blockquote {
  @apply border-l-4 border-gray-600 pl-4 italic text-gray-400;
}

.prose a {
  @apply text-purple-400 hover:text-purple-300 underline;
}

.prose table {
  @apply w-full border-collapse my-2;
}

.prose th,
.prose td {
  @apply border border-gray-700 px-2 py-1 text-sm;
}

.prose th {
  @apply bg-gray-800;
}
</style>
// Build 1767987964
