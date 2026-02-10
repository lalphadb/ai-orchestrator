<!-- components/ui/CodeBlock.vue -->
<template>
  <div class="code-block">
    <div class="code-block__header">
      <div class="code-block__language">{{ language }}</div>
      <button class="code-block__copy" @click="copyCode">
        <svg
          v-if="copied"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <polyline points="20,6 9,17 4,12"></polyline>
        </svg>
        <svg
          v-else
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
        </svg>
      </button>
    </div>
    <pre
      class="code-block__pre"
    ><code ref="codeRef" class="code-block__code" :class="`language-${language}`">{{ code }}</code></pre>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import hljs from 'highlight.js/lib/core'
import javascript from 'highlight.js/lib/languages/javascript'
import python from 'highlight.js/lib/languages/python'
import bash from 'highlight.js/lib/languages/bash'
import json from 'highlight.js/lib/languages/json'
import xml from 'highlight.js/lib/languages/xml'
import css from 'highlight.js/lib/languages/css'

// Register languages
hljs.registerLanguage('javascript', javascript)
hljs.registerLanguage('python', python)
hljs.registerLanguage('bash', bash)
hljs.registerLanguage('json', json)
hljs.registerLanguage('xml', xml)
hljs.registerLanguage('css', css)

const props = defineProps({
  code: {
    type: String,
    required: true,
  },
  language: {
    type: String,
    default: 'text',
  },
})

const copied = ref(false)
const codeRef = ref(null)

const copyCode = async () => {
  try {
    await navigator.clipboard.writeText(props.code)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch (err) {
    console.error('Failed to copy code:', err)
  }
}

onMounted(() => {
  if (codeRef.value) {
    hljs.highlightElement(codeRef.value)
  }
})
</script>

<style scoped>
.code-block {
  background: var(--bg-surface);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  overflow: hidden;
  font-family: var(--font-mono);
}

.code-block__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-3) var(--space-4);
  background: var(--bg-surface-hover);
  border-bottom: 1px solid var(--border-default);
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
  color: var(--text-tertiary);
}

.code-block__language {
  text-transform: uppercase;
}

.code-block__copy {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: var(--radius-md);
  background: transparent;
  border: 1px solid var(--border-default);
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.code-block__copy:hover {
  background: var(--bg-surface-active);
  color: var(--text-secondary);
  border-color: var(--border-strong);
}

.code-block__pre {
  margin: 0;
  padding: var(--space-4);
  overflow-x: auto;
  max-height: 300px;
  overflow-y: auto;
}

.code-block__code {
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  line-height: var(--leading-relaxed);
  color: var(--text-secondary);
  tab-size: 2;
  white-space: pre-wrap;
  word-break: break-word;
}

/* Highlight.js theme override */
.code-block__code :deep(.hljs-keyword) {
  color: #c678dd;
}

.code-block__code :deep(.hljs-built_in) {
  color: #e5c07b;
}

.code-block__code :deep(.hljs-function) {
  color: #61afef;
}

.code-block__code :deep(.hljs-string) {
  color: #98c379;
}

.code-block__code :deep(.hljs-number) {
  color: #d19a66;
}

.code-block__code :deep(.hljs-comment) {
  color: #5c6370;
  font-style: italic;
}

.code-block__code :deep(.hljs-variable) {
  color: #e06c75;
}

.code-block__code :deep(.hljs-title) {
  color: #61afef;
}

.code-block__code :deep(.hljs-section) {
  color: #e06c75;
}

.code-block__code :deep(.hljs-symbol) {
  color: #56b6c2;
}

.code-block__code :deep(.hljs-bullet) {
  color: #56b6c2;
}

.code-block__code :deep(.hljs-meta) {
  color: #c678dd;
}

.code-block__code :deep(.hljs-link) {
  color: #e5c07b;
  text-decoration: underline;
}
</style>
