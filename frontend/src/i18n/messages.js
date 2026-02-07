/**
 * Internationalization messages
 * Centralized message constants for consistent UI text
 */

export const messages = {
  // Common actions
  common: {
    save: 'Enregistrer',
    cancel: 'Annuler',
    delete: 'Supprimer',
    edit: 'Modifier',
    create: 'Créer',
    close: 'Fermer',
    open: 'Ouvrir',
    refresh: 'Rafraîchir',
    loading: 'Chargement...',
    error: 'Erreur',
    success: 'Succès',
    warning: 'Attention',
    confirm: 'Confirmer',
    back: 'Retour',
    next: 'Suivant',
    search: 'Rechercher',
    filter: 'Filtrer',
    reset: 'Réinitialiser',
    apply: 'Appliquer',
    clear: 'Effacer',
    done: 'Terminé',
    retry: 'Réessayer',
    copy: 'Copier',
    export: 'Exporter',
    import: 'Importer',
    download: 'Télécharger',
    upload: 'Téléverser',
    settings: 'Paramètres',
    help: 'Aide',
    logout: 'Déconnexion',
    login: 'Connexion',
    register: 'Inscription',
  },

  // Chat / Conversation
  chat: {
    newConversation: 'Nouvelle conversation',
    placeholder: 'Envoyer un message...',
    send: 'Envoyer',
    thinking: 'Réflexion en cours...',
    streaming: 'Génération en cours...',
    errorSending: "Erreur lors de l'envoi du message",
    errorLoading: 'Erreur lors du chargement des conversations',
    emptyState: 'Commencez une nouvelle conversation',
    noMessages: 'Aucun message',
    loadMore: 'Charger plus',
    retryMessage: 'Réessayer',
    editMessage: 'Modifier le message',
    deleteMessage: 'Supprimer le message',
    copyMessage: 'Copier le message',
    conversationDeleted: 'Conversation supprimée',
    conversationRenamed: 'Conversation renommée',
    exportConversation: 'Exporter la conversation',
    importConversation: 'Importer une conversation',
  },

  // Run / Workflow
  run: {
    title: 'Exécution',
    runs: 'Exécutions',
    status: {
      running: 'En cours',
      complete: 'Terminée',
      failed: 'Échouée',
      pending: 'En attente',
      cancelled: 'Annulée',
    },
    phase: {
      spec: 'Spécification',
      plan: 'Planification',
      execute: 'Exécution',
      verify: 'Vérification',
      repair: 'Réparation',
      complete: 'Terminé',
      error: 'Erreur',
    },
    toolsUsed: 'Outils utilisés',
    iterations: 'Itérations',
    duration: 'Durée',
    startedAt: 'Début',
    completedAt: 'Fin',
    viewDetails: 'Voir les détails',
    rerun: 'Relancer',
    rerunVerify: 'Relancer la vérification',
    forceRepair: 'Forcer la réparation',
    exportReport: 'Exporter le rapport',
    noRuns: 'Aucune exécution',
    runDetails: "Détails de l'exécution",
  },

  // Tools
  tools: {
    title: 'Outils',
    category: {
      system: 'Système',
      file: 'Fichier',
      network: 'Réseau',
      git: 'Git',
      docker: 'Docker',
      qa: 'Qualité',
      web: 'Web',
      general: 'Général',
    },
    status: {
      success: 'Succès',
      error: 'Erreur',
      running: 'En cours',
      pending: 'En attente',
    },
  },

  // Agents
  agents: {
    title: 'Agents',
    capabilities: 'Capacités',
    allowedTools: 'Outils autorisés',
    status: {
      active: 'Actif',
      inactive: 'Inactif',
      busy: 'Occupé',
      error: 'Erreur',
    },
  },

  // Models
  models: {
    title: 'Modèles',
    select: 'Sélectionner un modèle',
    categories: {
      cloud: 'Cloud',
      local: 'Local',
      code: 'Code',
      vision: 'Vision',
      embedding: 'Embedding',
      general: 'Général',
    },
  },

  // Errors
  errors: {
    generic: 'Une erreur est survenue',
    network: 'Erreur de connexion réseau',
    timeout: 'Délai dépassé',
    unauthorized: 'Non autorisé',
    notFound: 'Non trouvé',
    serverError: 'Erreur serveur',
    wsDisconnected: 'WebSocket déconnecté',
    wsReconnecting: 'Reconnexion WebSocket...',
    rateLimit: 'Limite de requêtes dépassée',
    invalidInput: 'Entrée invalide',
  },

  // Validation
  validation: {
    required: 'Ce champ est requis',
    minLength: 'Minimum {min} caractères',
    maxLength: 'Maximum {max} caractères',
    invalidEmail: 'Adresse email invalide',
    invalidUrl: 'URL invalide',
    passwordMismatch: 'Les mots de passe ne correspondent pas',
  },

  // Accessibility
  a11y: {
    skipToMain: 'Passer au contenu principal',
    menuOpen: 'Ouvrir le menu',
    menuClose: 'Fermer le menu',
    sidebarOpen: 'Ouvrir la barre latérale',
    sidebarClose: 'Fermer la barre latérale',
    expandSection: 'Développer la section',
    collapseSection: 'Réduire la section',
    loading: 'Chargement en cours',
    closeDialog: 'Fermer la boîte de dialogue',
    previous: 'Précédent',
    next: 'Suivant',
    currentPage: 'Page actuelle',
    totalPages: 'sur {total}',
  },
}

/**
 * Helper function to get nested message by key path
 * @param {string} key - Dot-separated key path (e.g., 'chat.placeholder')
 * @param {Object} params - Optional parameters for interpolation
 * @returns {string} Message string
 */
export function t(key, params = {}) {
  const keys = key.split('.')
  let value = messages

  for (const k of keys) {
    value = value?.[k]
    if (value === undefined) {
      console.warn(`[i18n] Missing translation key: ${key}`)
      return key
    }
  }

  if (typeof value !== 'string') {
    console.warn(`[i18n] Key does not resolve to string: ${key}`)
    return key
  }

  // Simple parameter interpolation
  return value.replace(/\{(\w+)\}/g, (match, param) => {
    return params[param] !== undefined ? String(params[param]) : match
  })
}

export default messages
