/**
 * Gestionnaire d'erreurs centralisé pour l'application
 * Fournit un feedback utilisateur cohérent et un logging approprié
 */

import { useToastStore } from '@/stores/toast'
import { logger } from './logger'

/**
 * Classe d'erreur personnalisée pour l'application
 */
export class AppError extends Error {
  constructor(message, code, details = {}) {
    super(message)
    this.name = 'AppError'
    this.code = code
    this.details = details
    this.timestamp = new Date().toISOString()
  }
}

/**
 * Gestionnaire d'erreurs principal
 */
export const errorHandler = {
  /**
   * Gère une erreur avec feedback utilisateur automatique
   * @param {Error} error - L'erreur à gérer
   * @param {string} context - Contexte de l'erreur (ex: 'Delete conversation')
   */
  handle(error, context = '') {
    const toast = useToastStore()

    // Log l'erreur en développement
    if (import.meta.env.DEV && context) {
      logger.error(`[${context}]`, error)
    }

    // Erreur réseau (pas de réponse serveur)
    if (error.isNetworkError) {
      toast.error('Connexion perdue. Vérifiez votre réseau.', 5000)
      return
    }

    // Gestion par code HTTP
    switch (error.status) {
      case 401:
        // Géré automatiquement par api.js (redirection /login)
        return

      case 403:
        toast.error('Accès refusé. Permissions insuffisantes.', 3000)
        return

      case 404:
        toast.warning('Ressource introuvable', 3000)
        return

      case 429:
        toast.warning('Trop de requêtes. Attendez quelques secondes.', 5000)
        return

      case 500:
      case 502:
      case 503:
        toast.error('Erreur serveur. Réessayez dans quelques instants.', 5000)
        return

      default: {
        // Erreur générique ou 4xx non géré
        const message = error.data?.detail || error.message || 'Une erreur est survenue'
        toast.error(message, 4000)
      }
    }
  },

  /**
   * Wrapper pour fonctions async avec gestion automatique d'erreurs
   * @param {Function} fn - Fonction async à exécuter
   * @param {string} context - Contexte pour le logging
   * @param {Object} options - Options de gestion
   * @returns {Promise<any>} Résultat de la fonction ou fallback
   *
   * @example
   * const result = await errorHandler.wrap(
   *   () => api.deleteConversation(id),
   *   'Delete conversation',
   *   { fallback: false }
   * )
   */
  async wrap(fn, context = '', options = {}) {
    const {
      silent = false, // Ne pas afficher de toast
      rethrow = false, // Re-throw l'erreur après handling
      fallback = null, // Valeur de retour en cas d'erreur
      onSuccess = null, // Callback en cas de succès
      onError = null, // Callback en cas d'erreur
    } = options

    try {
      const result = await fn()

      if (onSuccess) {
        onSuccess(result)
      }

      return result
    } catch (error) {
      // Callback custom
      if (onError) {
        onError(error)
      }

      // Afficher toast si pas silent
      if (!silent) {
        this.handle(error, context)
      }

      // Re-throw si demandé
      if (rethrow) {
        throw error
      }

      // Retourner fallback
      return fallback
    }
  },

  /**
   * Crée une AppError standardisée
   * @param {string} message - Message d'erreur
   * @param {string} code - Code d'erreur
   * @param {Object} details - Détails additionnels
   * @returns {AppError}
   */
  createError(message, code, details = {}) {
    return new AppError(message, code, details)
  },

  /**
   * Valide une réponse et throw si erreur
   * @param {Response} response - Réponse fetch
   * @param {string} context - Contexte
   * @throws {AppError}
   */
  async validateResponse(response, context = '') {
    if (!response.ok) {
      let errorData = {}
      try {
        errorData = await response.json()
      } catch {
        // Ignore parsing error
      }

      throw this.createError(errorData.detail || `HTTP ${response.status}`, response.status, {
        context,
        errorData,
      })
    }
    return response
  },
}

/**
 * Hook Vue pour utiliser errorHandler dans les composants
 * @example
 * import { useErrorHandler } from '@/utils/errorHandler'
 *
 * const { handleError, wrapAsync } = useErrorHandler()
 *
 * async function deleteItem(id) {
 *   await wrapAsync(
 *     () => api.delete(id),
 *     'Delete item',
 *     { onSuccess: () => toast.success('Deleted!') }
 *   )
 * }
 */
export function useErrorHandler() {
  return {
    handleError: errorHandler.handle.bind(errorHandler),
    wrapAsync: errorHandler.wrap.bind(errorHandler),
    createError: errorHandler.createError.bind(errorHandler),
  }
}

/**
 * Exemple d'utilisation dans un composant:
 *
 * <script setup>
 * import { useErrorHandler } from '@/utils/errorHandler'
 * import { useToastStore } from '@/stores/toast'
 * import api from '@/services/api'
 *
 * const { wrapAsync } = useErrorHandler()
 * const toast = useToastStore()
 *
 * // Méthode 1: Wrapper automatique
 * async function deleteConversation(id) {
 *   await wrapAsync(
 *     () => api.deleteConversation(id),
 *     'Delete conversation',
 *     {
 *       onSuccess: () => toast.success('Conversation supprimée'),
 *       fallback: false
 *     }
 *   )
 * }
 *
 * // Méthode 2: Try/catch manuel avec handle
 * async function renameConversation(id, title) {
 *   try {
 *     await api.renameConversation(id, title)
 *     toast.success('Conversation renommée')
 *   } catch (err) {
 *     errorHandler.handle(err, 'Rename conversation')
 *   }
 * }
 * </script>
 */
