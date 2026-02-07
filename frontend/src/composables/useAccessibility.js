/**
 * Accessibility composable
 * Provides keyboard navigation, focus management, and ARIA utilities
 */

import { ref, onMounted, onUnmounted } from 'vue'

/**
 * Composable for keyboard navigation
 * @returns {Object} Keyboard navigation utilities
 */
export function useKeyboardNavigation() {
  const focusedIndex = ref(0)
  const itemsRef = ref([])

  /**
   * Register an item for keyboard navigation
   * @param {HTMLElement} el - Element to register
   */
  function registerItem(el) {
    if (el && !itemsRef.value.includes(el)) {
      itemsRef.value.push(el)
    }
  }

  /**
   * Unregister an item
   * @param {HTMLElement} el - Element to unregister
   */
  function unregisterItem(el) {
    const index = itemsRef.value.indexOf(el)
    if (index > -1) {
      itemsRef.value.splice(index, 1)
    }
  }

  /**
   * Handle keyboard navigation
   * @param {KeyboardEvent} event - Keyboard event
   */
  function handleKeyDown(event) {
    const items = itemsRef.value.filter((el) => !el.disabled && el.offsetParent !== null)
    if (items.length === 0) return

    switch (event.key) {
      case 'ArrowDown':
      case 'ArrowRight':
        event.preventDefault()
        focusedIndex.value = (focusedIndex.value + 1) % items.length
        items[focusedIndex.value]?.focus()
        break
      case 'ArrowUp':
      case 'ArrowLeft':
        event.preventDefault()
        focusedIndex.value = (focusedIndex.value - 1 + items.length) % items.length
        items[focusedIndex.value]?.focus()
        break
      case 'Home':
        event.preventDefault()
        focusedIndex.value = 0
        items[0]?.focus()
        break
      case 'End':
        event.preventDefault()
        focusedIndex.value = items.length - 1
        items[items.length - 1]?.focus()
        break
    }
  }

  return {
    focusedIndex,
    registerItem,
    unregisterItem,
    handleKeyDown,
  }
}

/**
 * Composable for focus trapping (modals, dialogs)
 * @param {Ref<HTMLElement>} containerRef - Container element ref
 * @returns {Object} Focus trap utilities
 */
export function useFocusTrap(containerRef) {
  const isActive = ref(false)
  let previouslyFocused = null

  /**
   * Get all focusable elements within container
   * @returns {Array<HTMLElement>} Focusable elements
   */
  function getFocusableElements() {
    if (!containerRef.value) return []

    const selector = [
      'button:not([disabled])',
      'a[href]',
      'input:not([disabled])',
      'select:not([disabled])',
      'textarea:not([disabled])',
      '[tabindex]:not([tabindex="-1"])',
      '[contenteditable]',
    ].join(', ')

    return Array.from(containerRef.value.querySelectorAll(selector)).filter(
      (el) => el.offsetParent !== null
    )
  }

  /**
   * Handle tab key to trap focus
   * @param {KeyboardEvent} event - Keyboard event
   */
  function handleTab(event) {
    if (!isActive.value) return

    const focusableElements = getFocusableElements()
    if (focusableElements.length === 0) return

    const firstElement = focusableElements[0]
    const lastElement = focusableElements[focusableElements.length - 1]

    if (event.shiftKey) {
      if (document.activeElement === firstElement) {
        event.preventDefault()
        lastElement.focus()
      }
    } else {
      if (document.activeElement === lastElement) {
        event.preventDefault()
        firstElement.focus()
      }
    }
  }

  /**
   * Handle escape key
   * @param {KeyboardEvent} event - Keyboard event
   * @param {Function} onEscape - Callback when escape is pressed
   */
  function handleEscape(event, onEscape) {
    if (event.key === 'Escape' && isActive.value) {
      onEscape?.()
    }
  }

  /**
   * Activate focus trap
   */
  function activate() {
    previouslyFocused = document.activeElement
    isActive.value = true

    // Focus first element
    const focusableElements = getFocusableElements()
    if (focusableElements.length > 0) {
      focusableElements[0].focus()
    }
  }

  /**
   * Deactivate focus trap
   */
  function deactivate() {
    isActive.value = false
    previouslyFocused?.focus()
  }

  return {
    isActive,
    activate,
    deactivate,
    handleTab,
    handleEscape,
  }
}

/**
 * Generate unique ID for ARIA attributes
 * @param {string} prefix - ID prefix
 * @returns {string} Unique ID
 */
let idCounter = 0
export function generateId(prefix = 'id') {
  idCounter += 1
  return `${prefix}-${idCounter}`
}

/**
 * Composable for skip link functionality
 * @param {string} mainContentId - ID of main content element
 */
export function useSkipLink(mainContentId) {
  onMounted(() => {
    const skipLink = document.createElement('a')
    skipLink.href = `#${mainContentId}`
    skipLink.className =
      'sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-primary focus:text-white focus:rounded'
    skipLink.textContent = 'Passer au contenu principal'
    skipLink.setAttribute('data-skip-link', '')

    document.body.insertBefore(skipLink, document.body.firstChild)
  })

  onUnmounted(() => {
    const skipLink = document.querySelector('[data-skip-link]')
    skipLink?.remove()
  })
}

/**
 * Announce message to screen readers
 * @param {string} message - Message to announce
 * @param {'polite'|'assertive'} priority - Announcement priority
 */
export function announceToScreenReader(message, priority = 'polite') {
  const announcement = document.createElement('div')
  announcement.setAttribute('role', 'status')
  announcement.setAttribute('aria-live', priority)
  announcement.setAttribute('aria-atomic', 'true')
  announcement.className = 'sr-only'
  announcement.textContent = message

  document.body.appendChild(announcement)

  // Remove after announcement
  setTimeout(() => {
    announcement.remove()
  }, 1000)
}

/**
 * Check if user prefers reduced motion
 * @returns {boolean} True if reduced motion is preferred
 */
export function prefersReducedMotion() {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

/**
 * Accessible click handler (supports Enter and Space keys)
 * @param {KeyboardEvent} event - Keyboard event
 * @param {Function} callback - Click callback
 */
export function handleAccessibleClick(event, callback) {
  if (event.key === 'Enter' || event.key === ' ') {
    event.preventDefault()
    callback()
  }
}

export default {
  useKeyboardNavigation,
  useFocusTrap,
  useSkipLink,
  generateId,
  announceToScreenReader,
  prefersReducedMotion,
  handleAccessibleClick,
}
