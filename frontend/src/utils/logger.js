/**
 * Système de logging configurable pour l'application
 * Active les logs uniquement en mode développement avec flag debug
 */

const DEBUG = import.meta.env.DEV && localStorage.getItem('debug') === 'true'

export const logger = {
  /**
   * Logs de debug (visibles uniquement si DEBUG activé)
   * Usage: logger.debug('Run created', { runId, conversationId })
   */
  debug: (...args) => {
    if (DEBUG) {
      console.log('[DEBUG]', ...args)
    }
  },

  /**
   * Logs d'information (toujours visibles)
   * Usage: logger.info('WebSocket connected')
   */
  info: (...args) => {
    console.info('[INFO]', ...args)
  },

  /**
   * Avertissements (toujours visibles)
   * Usage: logger.warn('Retrying connection')
   */
  warn: (...args) => {
    console.warn('[WARN]', ...args)
  },

  /**
   * Erreurs (toujours visibles)
   * Usage: logger.error('Failed to fetch', error)
   */
  error: (...args) => {
    console.error('[ERROR]', ...args)
  },
}

/**
 * Pour activer les logs debug en dev:
 * localStorage.setItem('debug', 'true')
 *
 * Pour désactiver:
 * localStorage.removeItem('debug')
 */
