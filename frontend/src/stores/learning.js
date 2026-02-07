/**
 * Store Pinia pour le système d'apprentissage
 * Gère les feedbacks positifs/négatifs/corrections
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/api'

export const useLearningStore = defineStore('learning', () => {
  const stats = ref(null)
  const feedbackStats = ref(null)
  const patterns = ref([])

  /**
   * Envoie un feedback positif
   */
  async function sendPositiveFeedback(messageId, conversationId, query, response, toolsUsed = []) {
    try {
      const result = await api.post('/learning/feedback', {
        message_id: messageId,
        conversation_id: conversationId,
        feedback_type: 'positive',
        query,
        response,
        tools_used: toolsUsed,
      })

      console.log('✅ Feedback positif envoyé:', result)
      return result
    } catch (error) {
      console.error('❌ Erreur feedback positif:', error.message)
      throw error
    }
  }

  /**
   * Envoie un feedback négatif
   */
  async function sendNegativeFeedback(messageId, conversationId, query, response, toolsUsed = []) {
    try {
      const result = await api.post('/learning/feedback', {
        message_id: messageId,
        conversation_id: conversationId,
        feedback_type: 'negative',
        query,
        response,
        tools_used: toolsUsed,
      })

      console.log('✅ Feedback négatif envoyé:', result)
      return result
    } catch (error) {
      console.error('❌ Erreur feedback négatif:', error.message)
      throw error
    }
  }

  /**
   * Envoie une correction
   */
  async function sendCorrection(
    messageId,
    conversationId,
    query,
    response,
    correction,
    toolsUsed = [],
    comment = null
  ) {
    try {
      const result = await api.post('/learning/feedback', {
        message_id: messageId,
        conversation_id: conversationId,
        feedback_type: 'correction',
        query,
        response,
        correction,
        comment,
        tools_used: toolsUsed,
      })

      console.log('✅ Correction envoyée:', result)
      return result
    } catch (error) {
      console.error('❌ Erreur envoi correction:', error.message)
      throw error
    }
  }

  /**
   * Charge les statistiques d'apprentissage
   */
  async function loadStats() {
    try {
      const response = await api.get('/learning/stats')
      stats.value = response
      return response
    } catch (error) {
      console.error('❌ Erreur chargement stats:', error)
      throw error
    }
  }

  /**
   * Charge les statistiques de feedback
   */
  async function loadFeedbackStats(hours = 24) {
    try {
      const response = await api.get(`/learning/feedback/stats?hours=${hours}`)
      feedbackStats.value = response
      return response
    } catch (error) {
      console.error('❌ Erreur chargement feedback stats:', error)
      throw error
    }
  }

  /**
   * Charge les patterns appris
   */
  async function loadPatterns(limit = 10) {
    try {
      const response = await api.get(`/learning/patterns?limit=${limit}`)
      patterns.value = response.patterns || []
      return patterns.value
    } catch (error) {
      console.error('❌ Erreur chargement patterns:', error)
      throw error
    }
  }

  return {
    stats,
    feedbackStats,
    patterns,
    sendPositiveFeedback,
    sendNegativeFeedback,
    sendCorrection,
    loadStats,
    loadFeedbackStats,
    loadPatterns,
  }
})
