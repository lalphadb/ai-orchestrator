/**
 * Composable pour la détection et l'analyse des listes de modèles
 * Extrait de MessageList.vue pour réduire la complexité
 */

import { ref } from 'vue'

export function useModelDetection() {
  // Cache pour éviter les appels multiples (LRU simple)
  const modelsCache = new Map()
  const MAX_CACHE_SIZE = 50

  /**
   * Version mémorisée de detectModels pour éviter les appels multiples
   */
  function getModelsData(content) {
    if (!content) return { isModelsList: false, models: [] }

    // Créer une clé de cache basée sur le contenu (hash simple)
    const cacheKey = content.substring(0, 100) + content.length

    if (modelsCache.has(cacheKey)) {
      return modelsCache.get(cacheKey)
    }

    const result = detectModels(content)
    modelsCache.set(cacheKey, result)

    // Nettoyer le cache s'il devient trop grand
    if (modelsCache.size > MAX_CACHE_SIZE) {
      const firstKey = modelsCache.keys().next().value
      modelsCache.delete(firstKey)
    }

    return result
  }

  /**
   * Détection robuste et parsing unifié des modèles
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
      const start = cleaned.indexOf('{')
      const end = cleaned.lastIndexOf('}')

      if (start !== -1 && end !== -1) {
        const jsonStr = cleaned.substring(start, end + 1)
        const parsed = JSON.parse(jsonStr)

        // SKIP tool output format
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
        // Format 2: Direct array [...]
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
      }
    } catch (_e) {
      // JSON parse error, continue to fallbacks
    }

    // MÉTHODE 3: Détection de lignes JSON individuelles
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

    // MÉTHODE 4: Détection par noms de modèles connus
    const knownModelPatterns = [
      /llama\d*\.?\d*[:-]?[\w-]*/gi,
      /qwen\d*\.?\d*[:-]?[\w-]*/gi,
      /deepseek[:-]?[\w-]*/gi,
      /gemini[:-]?[\w-]*/gi,
      /kimi[:-]?[\w-]*/gi,
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

    // Décision finale
    if (models.length >= 5) {
      result.isModelsList = true
      result.models = models
    } else if (
      models.length >= 1 &&
      (cleaned.includes('ollama') || cleaned.includes('modèle') || cleaned.includes('LLM'))
    ) {
      result.isModelsList = true
      result.models = models
    }

    console.log(
      '[DetectModels] Final result:',
      result.isModelsList,
      'models:',
      result.models.length
    )
    return result
  }

  return {
    getModelsData,
    detectModels,
  }
}
