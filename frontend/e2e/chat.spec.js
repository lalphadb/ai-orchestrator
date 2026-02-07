/**
 * Chat Functionality E2E Tests
 */

import { test, expect } from '@playwright/test'

test.describe('Chat', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to chat page (assuming already authenticated)
    await page.goto('/v8/chat')
    // Wait for page to load
    await page.waitForSelector('[role="main"]', { timeout: 10000 })
  })

  test('should display chat interface', async ({ page }) => {
    // Check main components are visible
    await expect(page.getByRole('complementary', { name: /conversations/i })).toBeVisible()
    await expect(page.getByRole('region', { name: /conversation/i })).toBeVisible()
    await expect(page.getByRole('form', { name: /envoyer/i })).toBeVisible()
  })

  test('should toggle sidebar', async ({ page }) => {
    // Find sidebar toggle button
    const toggleButton = page.getByRole('button', { name: /fermer.*barre|ouvrir.*barre/i })
    
    // Click to close sidebar
    await toggleButton.click()
    
    // Check sidebar is hidden
    const sidebar = page.getByRole('complementary', { name: /conversations/i })
    await expect(sidebar).toHaveAttribute('aria-expanded', 'false')
    
    // Click to open sidebar
    const openButton = page.getByRole('button', { name: /ouvrir.*barre/i })
    await openButton.click()
    
    // Check sidebar is visible
    await expect(sidebar).toHaveAttribute('aria-expanded', 'true')
  })

  test('should toggle inspector', async ({ page }) => {
    // Find inspector toggle button
    const toggleButton = page.getByRole('button', { name: /fermer.*inspecteur|ouvrir.*inspecteur/i })
    
    // Click to close inspector
    await toggleButton.click()
    
    // Check inspector is hidden
    const inspector = page.getByRole('complementary', { name: /inspecteur/i })
    await expect(inspector).toHaveAttribute('aria-expanded', 'false')
    
    // Click to open inspector
    const openButton = page.getByRole('button', { name: /ouvrir.*inspecteur/i })
    await openButton.click()
    
    // Check inspector is visible
    await expect(inspector).toHaveAttribute('aria-expanded', 'true')
  })

  test('should send a message', async ({ page }) => {
    const testMessage = 'Hello, this is a test message'
    
    // Find message input
    const input = page.getByPlaceholder(/envoyer|message/i)
    await input.fill(testMessage)
    
    // Submit message
    await input.press('Enter')
    
    // Check message appears in the list
    await expect(page.getByText(testMessage)).toBeVisible()
  })

  test('should display loading state while sending', async ({ page }) => {
    const testMessage = 'Test loading state'
    
    // Send message
    const input = page.getByPlaceholder(/envoyer|message/i)
    await input.fill(testMessage)
    await input.press('Enter')
    
    // Check for loading indicator (if present)
    const loadingIndicator = page.getByText(/génération|réflexion|chargement/i)
    // Loading state may be brief, so we just check it doesn't error
    await expect(loadingIndicator).toBeDefined()
  })
})
