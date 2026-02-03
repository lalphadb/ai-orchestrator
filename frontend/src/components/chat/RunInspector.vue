<template>
  <div class="h-full flex flex-col bg-gray-900/50 border-l border-gray-700/50">
    <!-- Header -->
    <div
      class="p-3 border-b border-gray-700/50 flex items-center justify-between bg-gradient-to-r from-gray-800/50 to-transparent"
    >
      <h3 class="font-medium text-gray-300 flex items-center gap-2">
        <svg class="w-4 h-4 text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
          />
        </svg>
        Run Inspector
      </h3>
      <div class="flex items-center gap-2">
        <span
          v-if="run?.run_id"
          class="text-xs text-gray-500 font-mono bg-gray-800/50 px-2 py-0.5 rounded"
        >
          #{{ run.run_id.slice(0, 8) }}
        </span>
        <span class="px-2 py-0.5 rounded-full text-xs font-medium" :class="verdictClass">
          {{ verdictLabel }}
        </span>
      </div>
    </div>

    <!-- Run Selector (Phase 2: Multi-Run Support) -->
    <div
      v-if="availableRuns.length > 1"
      class="px-3 py-2 border-b border-gray-700/30 bg-gray-800/20"
    >
      <label class="text-xs text-gray-400 mb-1 block">Active Run:</label>
      <select
        v-model="selectedRunId"
        @change="selectRun"
        class="w-full px-2 py-1.5 bg-gray-800 border border-gray-700 rounded text-xs text-gray-300 focus:border-primary-500 focus:outline-none"
      >
        <option v-for="r in availableRuns" :key="r.run_id" :value="r.run_id">
          Run {{ r.run_id.slice(0, 8) }} - {{ r.workflowPhase }} ({{ formatDuration(r) }})
        </option>
      </select>
    </div>

    <!-- WS Disconnected Badge -->
    <div
      v-if="chat.wsState !== 'connected'"
      class="px-3 py-2 bg-red-500/10 border-b border-red-500/30 flex items-center gap-2"
    >
      <svg class="w-4 h-4 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M18.364 5.636a9 9 0 010 12.728m0 0l-2.829-2.829m2.829 2.829L21 21M15.536 8.464a5 5 0 010 7.072m0 0l-2.829-2.829m-4.243 2.829a4.978 4.978 0 01-1.414-2.83m-1.414 5.658a9 9 0 01-2.167-9.238m7.824 2.167a1 1 0 111.414 1.414m-1.414-1.414L3 3m8.293 8.293l1.414 1.414"
        />
      </svg>
      <span class="text-xs text-red-300 font-medium">WebSocket déconnecté</span>
    </div>

    <!-- No run -->
    <div
      v-if="!run"
      class="flex-1 flex items-center justify-center text-gray-500 text-sm p-4 text-center"
    >
      <div>
        <div
          class="w-16 h-16 mx-auto mb-4 rounded-full bg-gradient-to-br from-primary-500/20 to-purple-600/20 flex items-center justify-center"
        >
          <svg
            class="w-8 h-8 text-primary-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="1.5"
              d="M13 10V3L4 14h7v7l9-11h-7z"
            />
          </svg>
        </div>
        <p class="text-gray-400">Envoyez un message pour voir<br />la trace d'execution ici</p>
      </div>
    </div>

    <!-- Run content -->
    <div v-else class="flex-1 overflow-y-auto flex flex-col">
      <!-- Workflow Stepper - Improved Design -->
      <div class="p-4 border-b border-gray-700/30 bg-gradient-to-b from-gray-800/30 to-transparent">
        <div class="flex items-center justify-between text-xs mb-3">
          <span class="text-gray-400 font-medium">Pipeline Workflow</span>
          <div class="flex items-center gap-2">
            <span
              v-if="run.repairCycles > 0"
              class="px-2 py-0.5 rounded-full bg-orange-500/20 text-orange-300 text-[10px]"
            >
              {{ run.repairCycles }} repair{{ run.repairCycles > 1 ? 's' : '' }}
            </span>
            <span v-if="run.duration" class="text-gray-400 font-mono">{{
              formatDuration(run.duration)
            }}</span>
          </div>
        </div>

        <!-- Stepper with icons -->
        <div class="flex items-center justify-between">
          <div
            v-for="(phase, idx) in WORKFLOW_PHASES"
            :key="phase"
            class="flex flex-col items-center relative"
            :style="{ flex: idx < WORKFLOW_PHASES.length - 1 ? '1' : '0' }"
          >
            <!-- Phase node -->
            <div
              class="w-8 h-8 rounded-lg flex items-center justify-center transition-all duration-300 relative z-10"
              :class="getPhaseClass(phase)"
            >
              <!-- Phase icon -->
              <component :is="getPhaseIcon(phase)" />
            </div>

            <!-- Phase label -->
            <span
              class="text-[10px] mt-1.5 font-medium transition-colors"
              :class="
                isPhaseActive(phase)
                  ? 'text-primary-400'
                  : isPhaseComplete(phase)
                    ? 'text-green-400'
                    : 'text-gray-500'
              "
            >
              {{ getPhaseLabel(phase) }}
            </span>

            <!-- Connector line -->
            <div
              v-if="idx < WORKFLOW_PHASES.length - 1"
              class="absolute top-4 left-[calc(50%+16px)] w-[calc(100%-32px)] h-0.5 transition-colors duration-300"
              :class="isPhaseComplete(phase) ? 'bg-green-500' : 'bg-gray-700'"
            ></div>
          </div>
        </div>
      </div>

      <!-- Tabs - Improved styling -->
      <div class="flex border-b border-gray-700/30 bg-gray-800/20">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          class="flex-1 px-3 py-2.5 text-xs font-medium transition-all relative"
          :class="activeTab === tab.id ? 'text-primary-400' : 'text-gray-500 hover:text-gray-300'"
          @click="activeTab = tab.id"
        >
          <span class="flex items-center justify-center gap-1.5">
            <component :is="tab.icon" class="w-3.5 h-3.5" />
            {{ tab.label }}
            <span
              v-if="tab.badge"
              class="px-1.5 py-0.5 rounded-full text-[10px] font-medium"
              :class="
                activeTab === tab.id
                  ? 'bg-primary-500/30 text-primary-300'
                  : 'bg-gray-700 text-gray-400'
              "
            >
              {{ tab.badge }}
            </span>
          </span>
          <!-- Active indicator -->
          <div
            v-if="activeTab === tab.id"
            class="absolute bottom-0 left-0 right-0 h-0.5 bg-primary-500"
          ></div>
        </button>
      </div>

      <!-- Tab Content -->
      <div class="flex-1 overflow-y-auto p-3">
        <!-- Tools Tab -->
        <div v-if="activeTab === 'tools'" class="space-y-2">
          <div v-if="run.tools.length === 0" class="text-gray-500 text-sm text-center py-8">
            <svg
              class="w-10 h-10 mx-auto mb-2 text-gray-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="1.5"
                d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
              />
            </svg>
            Aucun outil utilise
          </div>
          <div
            v-for="(tool, idx) in run.tools"
            :key="'tool-' + idx"
            class="bg-gray-800/50 rounded-lg p-3 border border-gray-700/50 hover:border-blue-500/30 transition-colors"
          >
            <div class="flex items-center gap-2 mb-2">
              <div
                class="w-7 h-7 rounded-lg bg-gradient-to-br from-blue-500/30 to-blue-600/20 flex items-center justify-center"
              >
                <svg
                  class="w-3.5 h-3.5 text-blue-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                  />
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                  />
                </svg>
              </div>
              <span class="text-sm font-medium text-blue-300">{{ tool.tool }}</span>
              <span class="text-[10px] px-1.5 py-0.5 rounded bg-gray-700/50 text-gray-400"
                >Iter {{ tool.iteration }}</span
              >
            </div>
            <div v-if="chat.settings.showToolParams && tool.params" class="mt-2">
              <pre
                class="text-xs text-gray-400 bg-gray-900/50 rounded-lg p-2 overflow-x-auto border border-gray-700/30"
                >{{ formatParams(tool.params) }}</pre
              >
            </div>
          </div>
        </div>

        <!-- Thinking Tab (NEW) -->
        <div v-if="activeTab === 'thinking'" class="space-y-2">
          <div v-if="!run.thinking || run.thinking.length === 0" class="text-gray-500 text-sm text-center py-8">
            <svg
              class="w-10 h-10 mx-auto mb-2 text-gray-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="1.5"
                d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
              />
            </svg>
            Pas de traces de reflexion
          </div>
          <div
            v-for="(thought, idx) in run.thinking || []"
            :key="'thought-' + idx"
            class="bg-purple-900/20 rounded-lg p-3 border border-purple-700/30"
          >
            <div class="flex items-center gap-2 mb-2">
              <div class="w-6 h-6 rounded-full bg-purple-500/20 flex items-center justify-center">
                <svg
                  class="w-3 h-3 text-purple-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                  />
                </svg>
              </div>
              <span class="text-xs text-purple-300 font-medium">{{
                thought.phase || 'Reflexion'
              }}</span>
              <span class="text-[10px] text-gray-500">Iter {{ thought.iteration }}</span>
            </div>
            <p class="text-sm text-purple-200/80 leading-relaxed">{{ thought.message }}</p>
          </div>
        </div>

        <!-- Verification Tab -->
        <div v-if="activeTab === 'verification'" class="space-y-3">
          <div
            v-if="!run.verification || run.verification.length === 0"
            class="text-gray-500 text-sm text-center py-8"
          >
            <svg
              class="w-10 h-10 mx-auto mb-2 text-gray-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="1.5"
                d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"
              />
            </svg>
            Pas de verification QA executee
          </div>

          <!-- Verification Items (temps reel) -->
          <div
            v-for="item in run.verification || []"
            :key="item.check_name"
            class="bg-gray-800/50 rounded-lg p-3 border transition-colors"
            :class="getVerificationItemClass(item)"
          >
            <div class="flex items-center gap-2">
              <div
                class="w-6 h-6 rounded-lg flex items-center justify-center"
                :class="{
                  'bg-yellow-500/20': item.status === 'running',
                  'bg-green-500/20': item.status === 'passed',
                  'bg-red-500/20': item.status === 'failed',
                }"
              >
                <svg
                  v-if="item.status === 'running'"
                  class="w-3.5 h-3.5 text-yellow-400 animate-spin"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                  />
                </svg>
                <svg
                  v-else-if="item.status === 'passed'"
                  class="w-3.5 h-3.5 text-green-400"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fill-rule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clip-rule="evenodd"
                  />
                </svg>
                <svg
                  v-else
                  class="w-3.5 h-3.5 text-red-400"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fill-rule="evenodd"
                    d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                    clip-rule="evenodd"
                  />
                </svg>
              </div>
              <span
                class="text-sm font-medium"
                :class="
                  item.status === 'passed'
                    ? 'text-green-300'
                    : item.status === 'failed'
                      ? 'text-red-300'
                      : 'text-yellow-300'
                "
              >
                {{ item.check_name }}
              </span>
            </div>
            <div v-if="item.output" class="mt-2">
              <pre
                class="text-xs text-gray-400 bg-gray-900/50 rounded-lg p-2 overflow-x-auto max-h-24 border border-gray-700/30"
                >{{ item.output }}</pre
              >
            </div>
            <div v-if="item.error" class="mt-2 text-xs text-red-400 flex items-start gap-1">
              <svg class="w-3 h-3 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fill-rule="evenodd"
                  d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
                  clip-rule="evenodd"
                />
              </svg>
              {{ item.error }}
            </div>
          </div>

          <!-- Verdict Final -->
          <div
            v-if="run.verdict"
            class="mt-4 p-4 rounded-xl border"
            :class="
              run.verdict.status === 'PASS'
                ? 'bg-green-500/10 border-green-500/30'
                : 'bg-red-500/10 border-red-500/30'
            "
          >
            <div class="flex items-center gap-3 mb-3">
              <div
                class="w-10 h-10 rounded-xl flex items-center justify-center"
                :class="run.verdict.status === 'PASS' ? 'bg-green-500/20' : 'bg-red-500/20'"
              >
                <svg
                  v-if="run.verdict.status === 'PASS'"
                  class="w-6 h-6 text-green-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <svg
                  v-else
                  class="w-6 h-6 text-red-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <div>
                <span
                  class="font-semibold text-lg"
                  :class="run.verdict.status === 'PASS' ? 'text-green-300' : 'text-red-300'"
                >
                  Verdict: {{ run.verdict.status }}
                </span>
                <div class="flex items-center gap-2 mt-0.5">
                  <div class="w-20 h-1.5 bg-gray-700 rounded-full overflow-hidden">
                    <div
                      class="h-full rounded-full transition-all"
                      :class="run.verdict.status === 'PASS' ? 'bg-green-500' : 'bg-red-500'"
                      :style="{ width: `${run.verdict.confidence * 100}%` }"
                    ></div>
                  </div>
                  <span class="text-xs text-gray-400"
                    >{{ Math.round(run.verdict.confidence * 100) }}% confiance</span
                  >
                </div>
              </div>
            </div>
            <div v-if="run.verdict.issues?.length" class="mt-3 pt-3 border-t border-gray-700/30">
              <p class="text-xs text-gray-500 mb-2 font-medium">Problemes detectes:</p>
              <ul class="space-y-1">
                <li
                  v-for="issue in run.verdict.issues"
                  :key="issue"
                  class="flex items-start gap-2 text-sm text-red-300"
                >
                  <svg class="w-4 h-4 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fill-rule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                      clip-rule="evenodd"
                    />
                  </svg>
                  {{ issue }}
                </li>
              </ul>
            </div>
          </div>
        </div>

        <!-- Raw Tab -->
        <div v-if="activeTab === 'raw'" class="space-y-2">
          <div class="text-xs text-gray-500 mb-2 flex items-center gap-2">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"
              />
            </svg>
            Donnees brutes du run
          </div>
          <pre
            class="text-xs text-gray-400 bg-gray-900/70 rounded-lg p-3 overflow-x-auto max-h-96 border border-gray-700/30 font-mono"
            >{{ formatRaw() }}</pre
          >
        </div>
      </div>
    </div>

    <!-- Footer with actions -->
    <div
      v-if="run?.complete"
      class="p-3 border-t border-gray-700/50 bg-gradient-to-t from-gray-800/30 to-transparent space-y-2"
    >
      <!-- Verdict badge -->
      <div v-if="run.verdict" class="flex items-center justify-between mb-2 px-1">
        <span class="text-xs text-gray-500">Verdict final:</span>
        <span
          class="px-2.5 py-1 rounded-lg text-xs font-semibold"
          :class="
            run.verdict.status === 'PASS'
              ? 'bg-green-500/20 text-green-300'
              : 'bg-red-500/20 text-red-300'
          "
        >
          {{ run.verdict.status }}
        </span>
      </div>

      <!-- Actions -->
      <div class="flex gap-2">
        <button
          :disabled="isReVerifying || !run.complete"
          class="flex-1 px-3 py-2 bg-gradient-to-r from-blue-600/30 to-blue-500/20 hover:from-blue-600/50 hover:to-blue-500/30 text-blue-300 text-xs rounded-lg transition-all flex items-center justify-center gap-1.5 border border-blue-500/30 disabled:opacity-50 disabled:cursor-not-allowed"
          title="Relancer la verification QA"
          @click="handleReVerify"
        >
          <svg
            v-if="!isReVerifying"
            class="w-3.5 h-3.5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
          <div
            v-else
            class="w-3.5 h-3.5 border-2 border-blue-300 border-t-transparent rounded-full animate-spin"
          ></div>
          {{ isReVerifying ? 'Vérification...' : 'Re-verify' }}
        </button>
        <button
          v-if="run.verdict?.status === 'FAIL'"
          :disabled="isRepairing || !run.complete"
          class="flex-1 px-3 py-2 bg-gradient-to-r from-orange-600/30 to-yellow-500/20 hover:from-orange-600/50 hover:to-yellow-500/30 text-orange-300 text-xs rounded-lg transition-all flex items-center justify-center gap-1.5 border border-orange-500/30 disabled:opacity-50 disabled:cursor-not-allowed"
          title="Forcer un cycle de reparation"
          @click="handleRepair"
        >
          <svg
            v-if="!isRepairing"
            class="w-3.5 h-3.5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M11 4a2 2 0 114 0v1a1 1 0 001 1h3a1 1 0 011 1v3a1 1 0 01-1 1h-1a2 2 0 100 4h1a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1v-1a2 2 0 10-4 0v1a1 1 0 01-1 1H7a1 1 0 01-1-1v-3a1 1 0 00-1-1H4a2 2 0 110-4h1a1 1 0 001-1V7a1 1 0 011-1h3a1 1 0 001-1V4z"
            />
          </svg>
          <div
            v-else
            class="w-3.5 h-3.5 border-2 border-orange-300 border-t-transparent rounded-full animate-spin"
          ></div>
          {{ isRepairing ? 'Réparation...' : 'Repair' }}
        </button>
      </div>
      <div class="flex gap-2">
        <button
          class="flex-1 px-3 py-1.5 bg-gray-700/50 hover:bg-gray-700 text-gray-300 text-xs rounded-lg transition-colors flex items-center justify-center gap-1.5"
          @click="copyTrace"
        >
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
            />
          </svg>
          Copier
        </button>
        <button
          class="flex-1 px-3 py-1.5 bg-gray-700/50 hover:bg-gray-700 text-gray-300 text-xs rounded-lg transition-colors flex items-center justify-center gap-1.5"
          @click="downloadReport"
        >
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          Exporter
        </button>
      </div>
    </div>

    <!-- Error state -->
    <div v-if="run?.error" class="p-3 border-t border-gray-700/50">
      <div class="bg-red-500/10 rounded-xl p-4 border border-red-500/30">
        <div class="flex items-center gap-3 mb-3">
          <div class="w-10 h-10 rounded-xl bg-red-500/20 flex items-center justify-center">
            <svg class="w-6 h-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <span class="font-semibold text-red-300">Erreur d'execution</span>
        </div>
        <p class="text-sm text-red-200 mb-4">{{ run.error }}</p>
        <button
          class="w-full px-4 py-2 bg-red-600 hover:bg-red-500 text-white text-sm rounded-lg transition-colors font-medium"
          @click="chat.retryLastMessage()"
        >
          Reessayer
        </button>
      </div>
    </div>

    <!-- Toast Notification -->
    <Toast
      :show="toast.show"
      :type="toast.type"
      :message="toast.message"
      :description="toast.description"
      @close="toast.show = false"
    />
  </div>
</template>

<script setup>
import { ref, computed, h, watch } from 'vue'
import { useChatStore } from '@/stores/chat'
import Toast from '@/components/common/Toast.vue'

const chat = useChatStore()
const WORKFLOW_PHASES = chat.WORKFLOW_PHASES

const activeTab = ref('tools')

// Phase 2: Multi-Run Support
const selectedRunId = ref(chat.activeRunId)

// Watch for changes in chat.activeRunId (e.g., when new run starts)
watch(
  () => chat.activeRunId,
  (newRunId) => {
    if (newRunId) {
      selectedRunId.value = newRunId
    }
  }
)

const availableRuns = computed(() => {
  const convId = chat.currentConversation?.id
  if (!convId) return []

  const runIds = chat.runsByConversation.get(convId)
  if (!runIds) return []

  return Array.from(runIds)
    .map((id) => chat.runs.get(id))
    .filter((r) => r) // Filter out deleted runs
    .sort((a, b) => new Date(b.startedAt).getTime() - new Date(a.startedAt).getTime()) // Most recent first (v8: use startedAt ISO string)
})

const run = computed(() => {
  if (!selectedRunId.value) return null
  return chat.runs.get(selectedRunId.value)
})

function selectRun() {
  chat.activeRunId = selectedRunId.value
}

function formatDuration(runOrMs) {
  if (!runOrMs) return '-'

  // If it's a run object, calculate duration from v8 ISO timestamps
  if (typeof runOrMs === 'object' && runOrMs.startedAt) {
    const startMs = new Date(runOrMs.startedAt).getTime()
    const endMs = runOrMs.endedAt ? new Date(runOrMs.endedAt).getTime() : Date.now()
    const ms = endMs - startMs
    if (ms < 1000) return `${ms}ms`
    return `${(ms / 1000).toFixed(1)}s`
  }

  // If it's just a number (ms)
  const ms = typeof runOrMs === 'number' ? runOrMs : 0
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}
const toast = ref({
  show: false,
  type: 'success',
  message: '',
  description: '',
})

// Tab icons as render functions
const ToolsIcon = () =>
  h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
    h('path', {
      'stroke-linecap': 'round',
      'stroke-linejoin': 'round',
      'stroke-width': '2',
      d: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z',
    }),
  ])

const ThinkingIcon = () =>
  h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
    h('path', {
      'stroke-linecap': 'round',
      'stroke-linejoin': 'round',
      'stroke-width': '2',
      d: 'M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z',
    }),
  ])

const VerificationIcon = () =>
  h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
    h('path', {
      'stroke-linecap': 'round',
      'stroke-linejoin': 'round',
      'stroke-width': '2',
      d: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z',
    }),
  ])

const RawIcon = () =>
  h('svg', { fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
    h('path', {
      'stroke-linecap': 'round',
      'stroke-linejoin': 'round',
      'stroke-width': '2',
      d: 'M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4',
    }),
  ])

const tabs = computed(() => [
  { id: 'tools', label: 'Tools', badge: run.value?.tools?.length ?? 0, icon: ToolsIcon },
  {
    id: 'thinking',
    label: 'Thinking',
    badge: run.value?.thinking?.length ?? 0,
    icon: ThinkingIcon,
  },
  {
    id: 'verification',
    label: 'QA',
    badge: run.value?.verification?.length ?? 0,
    icon: VerificationIcon,
  },
  { id: 'raw', label: 'Raw', icon: RawIcon },
])

// Loading states for action buttons (CRQ-2026-0203-001 Phase 5: Safe property access)
const isReVerifying = computed(() => {
  return run.value?.workflowPhase === 'verify' && !run.value?.complete
})

const isRepairing = computed(() => {
  return run.value?.workflowPhase === 'repair' && !run.value?.complete
})

const verdictClass = computed(() => {
  if (!run.value) return 'bg-gray-700 text-gray-400'

  // CRQ-2026-0203-001 Phase 5: Check verdict first
  if (run.value.verdict?.status === 'PASS') return 'bg-green-500/20 text-green-300'
  if (run.value.verdict?.status === 'FAIL') return 'bg-red-500/20 text-red-300'

  // CRQ-2026-0203-001 Phase 5: Safe workflowPhase access with fallback
  const phase = run.value?.workflowPhase
  switch (phase) {
    case 'spec':
      return 'bg-purple-500/20 text-purple-300'
    case 'plan':
      return 'bg-blue-500/20 text-blue-300'
    case 'execute':
      return 'bg-yellow-500/20 text-yellow-300'
    case 'verify':
      return 'bg-cyan-500/20 text-cyan-300'
    case 'repair':
      return 'bg-orange-500/20 text-orange-300'
    case 'complete':
      return 'bg-green-500/20 text-green-300'
    case 'failed':
      return 'bg-red-500/20 text-red-300'
    default:
      return 'bg-gray-700 text-gray-400'
  }
})

const verdictLabel = computed(() => {
  if (!run.value) return 'Inactif'

  // CRQ-2026-0203-001 Phase 5: Safe property access with fallbacks
  if (run.value.verdict?.status) return run.value.verdict.status
  return run.value?.workflowPhase ?? 'Starting'
})

// Phase icons
function getPhaseIcon(phase) {
  const icons = {
    spec: () =>
      h('svg', { class: 'w-4 h-4', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
        h('path', {
          'stroke-linecap': 'round',
          'stroke-linejoin': 'round',
          'stroke-width': '2',
          d: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z',
        }),
      ]),
    plan: () =>
      h('svg', { class: 'w-4 h-4', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
        h('path', {
          'stroke-linecap': 'round',
          'stroke-linejoin': 'round',
          'stroke-width': '2',
          d: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4',
        }),
      ]),
    execute: () =>
      h('svg', { class: 'w-4 h-4', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
        h('path', {
          'stroke-linecap': 'round',
          'stroke-linejoin': 'round',
          'stroke-width': '2',
          d: 'M13 10V3L4 14h7v7l9-11h-7z',
        }),
      ]),
    verify: () =>
      h('svg', { class: 'w-4 h-4', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
        h('path', {
          'stroke-linecap': 'round',
          'stroke-linejoin': 'round',
          'stroke-width': '2',
          d: 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z',
        }),
      ]),
    repair: () =>
      h('svg', { class: 'w-4 h-4', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
        h('path', {
          'stroke-linecap': 'round',
          'stroke-linejoin': 'round',
          'stroke-width': '2',
          d: 'M11 4a2 2 0 114 0v1a1 1 0 001 1h3a1 1 0 011 1v3a1 1 0 01-1 1h-1a2 2 0 100 4h1a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1v-1a2 2 0 10-4 0v1a1 1 0 01-1 1H7a1 1 0 01-1-1v-3a1 1 0 00-1-1H4a2 2 0 110-4h1a1 1 0 001-1V7a1 1 0 011-1h3a1 1 0 001-1V4z',
        }),
      ]),
    complete: () =>
      h('svg', { class: 'w-4 h-4', fill: 'none', stroke: 'currentColor', viewBox: '0 0 24 24' }, [
        h('path', {
          'stroke-linecap': 'round',
          'stroke-linejoin': 'round',
          'stroke-width': '2',
          d: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
        }),
      ]),
  }
  return icons[phase] || icons.spec
}

function getPhaseLabel(phase) {
  const labels = {
    spec: 'Spec',
    plan: 'Plan',
    execute: 'Exec',
    verify: 'QA',
    repair: 'Fix',
    complete: 'Done',
  }
  return labels[phase] || phase
}

function getPhaseClass(phase) {
  if (isPhaseComplete(phase)) return 'bg-green-500/20 text-green-400 border border-green-500/30'
  if (isPhaseActive(phase))
    return 'bg-primary-500/20 text-primary-400 border border-primary-500/50 ring-2 ring-primary-500/30 animate-pulse'
  return 'bg-gray-700/50 text-gray-500 border border-gray-600/30'
}

function isPhaseComplete(phase) {
  if (!run.value) return false

  // CRQ-2026-0203-001 Phase 5: Safe phase comparison with fallbacks
  const currentPhase = run.value?.workflowPhase
  if (!currentPhase) return false

  const currentIdx = WORKFLOW_PHASES.indexOf(currentPhase)
  const phaseIdx = WORKFLOW_PHASES.indexOf(phase)

  // If currentPhase is invalid (indexOf returns -1), no phases are complete
  if (currentIdx === -1) return false

  return currentIdx > phaseIdx
}

function isPhaseActive(phase) {
  if (!run.value) return false

  // CRQ-2026-0203-001 Phase 5: Safe phase comparison
  const currentPhase = run.value?.workflowPhase
  return currentPhase === phase
}

function getVerificationItemClass(item) {
  if (item.status === 'passed') return 'border-green-500/30'
  if (item.status === 'failed') return 'border-red-500/30'
  return 'border-yellow-500/30'
}

function formatParams(params) {
  if (typeof params === 'string') return params
  return JSON.stringify(params, null, 2)
}

function formatRaw() {
  if (!run.value) return '{}'
  return JSON.stringify(
    {
      id: run.value.id,
      model: run.value.model,
      workflowPhase: run.value.workflowPhase,
      duration: run.value.duration,
      iterations: run.value.complete?.iterations,
      tools_used: run.value.complete?.tools_used,
      verification: run.value.verification,
      verdict: run.value.verdict,
      phaseHistory: run.value.phaseHistory,
      thinking: run.value.thinking,
      tools: run.value.tools,
    },
    null,
    2
  )
}

function showToast(type, message, description = '') {
  toast.value = { show: true, type, message, description }
}

async function handleReVerify() {
  try {
    await chat.rerunVerification()
    showToast('success', 'Vérification relancée', "Les checks QA sont en cours d'exécution")
  } catch (error) {
    showToast('error', 'Échec de la vérification', error.message)
  }
}

async function handleRepair() {
  try {
    await chat.forceRepair()
    showToast('success', 'Réparation lancée', 'Le cycle de correction a démarré')
  } catch (error) {
    showToast('error', 'Échec de la réparation', error.message)
  }
}

function copyTrace() {
  const report = chat.exportRunReport()
  if (report) {
    navigator.clipboard.writeText(report)
    showToast('success', 'Trace copiée', 'Le rapport a été copié dans le presse-papiers')
  } else {
    showToast('warning', 'Aucune trace', 'Aucun rapport disponible pour le moment')
  }
}

function downloadReport() {
  const report = chat.exportRunReport()
  if (report) {
    const blob = new Blob([report], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `run-report-${run.value?.id || 'unknown'}.json`
    a.click()
    URL.revokeObjectURL(url)
    showToast('success', 'Rapport téléchargé', 'Le rapport JSON a été enregistré')
  } else {
    showToast('warning', 'Aucun rapport', 'Aucun rapport disponible pour le moment')
  }
}
</script>
