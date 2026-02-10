<!-- views/TestUIView.vue -->
<template>
  <div class="test-ui-page">
    <h1 class="heading-1">Test des nouveaux composants UI</h1>

    <div class="test-section">
      <h2 class="heading-2">GlassCard</h2>
      <div class="component-grid">
        <GlassCard variant="default">
          <p>Ceci est une GlassCard par défaut</p>
        </GlassCard>
        <GlassCard variant="elevated" glow>
          <p>Cette GlassCard est elevée avec effet glow</p>
        </GlassCard>
        <GlassCard variant="bordered" hoverable>
          <p>Cette GlassCard est bordée et survolable</p>
        </GlassCard>
      </div>
    </div>

    <div class="test-section">
      <h2 class="heading-2">ModernButton</h2>
      <div class="component-grid">
        <ModernButton variant="primary">Bouton Principal</ModernButton>
        <ModernButton variant="secondary">Bouton Secondaire</ModernButton>
        <ModernButton variant="ghost">Bouton Ghost</ModernButton>
        <ModernButton variant="danger">Bouton Danger</ModernButton>
        <ModernButton variant="primary" loading>Chargement...</ModernButton>
        <ModernButton variant="primary" icon-only>
          <template #icon-left>
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="8" x2="12" y2="12"></line>
              <line x1="12" y1="16" x2="12.01" y2="16"></line>
            </svg>
          </template>
        </ModernButton>
      </div>
    </div>

    <div class="test-section">
      <h2 class="heading-2">StatusOrb</h2>
      <div class="component-grid">
        <div class="status-item">
          <StatusOrb status="default" label="Défaut" />
        </div>
        <div class="status-item">
          <StatusOrb status="active" label="Actif" pulse />
        </div>
        <div class="status-item">
          <StatusOrb status="success" label="Succès" pulse />
        </div>
        <div class="status-item">
          <StatusOrb status="warning" label="Avertissement" />
        </div>
        <div class="status-item">
          <StatusOrb status="error" label="Erreur" />
        </div>
        <div class="status-item">
          <StatusOrb status="processing" label="En cours" pulse />
        </div>
      </div>
    </div>

    <div class="test-section">
      <h2 class="heading-2">Autres composants</h2>
      <div class="component-grid">
        <SkeletonLoader variant="text" :lines="3" />
        <SkeletonLoader variant="card" />
        <SkeletonLoader variant="avatar" />
        <SkeletonLoader variant="button" />

        <EmptyState
          title="Aucun élément trouvé"
          description="Il n'y a rien à afficher ici pour le moment."
        >
          <template #actions>
            <ModernButton variant="primary">Créer un élément</ModernButton>
          </template>
        </EmptyState>

        <MetricCard title="Taux de succès" value="98.5%" status="success" trend="+2.3%" />

        <div class="thinking-test">
          <p>Indicateur de réflexion :</p>
          <ThinkingDots />
        </div>
      </div>
    </div>

    <div class="test-section">
      <h2 class="heading-2">Pipeline Steps</h2>
      <PipelineSteps
        :steps="pipelineSteps"
        :current-step="currentStep"
        :completed-steps="completedSteps"
      />
    </div>

    <div class="test-section">
      <h2 class="heading-2">Code Block</h2>
      <CodeBlock :code="sampleCode" language="javascript" />
    </div>

    <div class="test-section">
      <h2 class="heading-2">Agent Card</h2>
      <AgentCard
        :name="sampleAgent.name"
        :description="sampleAgent.description"
        :status="sampleAgent.status"
        @click="handleAgentClick"
      />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import GlassCard from '@/components/ui/GlassCard.vue'
import ModernButton from '@/components/ui/ModernButton.vue'
import StatusOrb from '@/components/ui/StatusOrb.vue'
import SkeletonLoader from '@/components/ui/SkeletonLoader.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import MetricCard from '@/components/ui/MetricCard.vue'
import ThinkingDots from '@/components/ui/ThinkingDots.vue'
import PipelineSteps from '@/components/ui/PipelineSteps.vue'
import CodeBlock from '@/components/ui/CodeBlock.vue'
import AgentCard from '@/components/ui/AgentCard.vue'

const currentStep = ref('execute')
const completedSteps = ref(['spec', 'plan'])

const pipelineSteps = [
  { id: 'spec', title: 'Spécification', description: 'Analyse de la demande' },
  { id: 'plan', title: 'Planification', description: "Création du plan d'exécution" },
  { id: 'execute', title: 'Exécution', description: 'Exécution du plan' },
  { id: 'verify', title: 'Vérification', description: 'Vérification des résultats' },
  { id: 'repair', title: 'Réparation', description: 'Correction si nécessaire' },
]

const sampleCode = `function calculateSum(a, b) {
  // Cette fonction calcule la somme de deux nombres
  return a + b;
}

console.log(calculateSum(5, 3)); // Affiche 8`

const sampleAgent = {
  id: 'web.researcher',
  name: 'Web Researcher',
  description: 'Recherche des informations sur le web',
  status: 'active',
  capabilities: ['web', 'research'],
  tools: ['web_search', 'web_read', 'http_request'],
}

const handleAgentClick = (agent) => {
  console.log('Agent clicked:', agent)
}
</script>

<style scoped>
.test-ui-page {
  padding: var(--space-8);
  max-width: var(--container-xl);
  margin: 0 auto;
}

.test-section {
  margin-bottom: var(--space-12);
}

.component-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: var(--space-6);
  margin-top: var(--space-4);
}

.status-item {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.thinking-test {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--space-2);
}

:deep(.agent-card) {
  height: 100%;
}
</style>
