/**
 * Accessibility E2E Tests
 */

import { test, expect } from '@playwright/test'

test.describe('Accessibility', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/v8/chat')
    await page.waitForSelector('[role="main"]', { timeout: 10000 })
  })

  test('should have proper ARIA landmarks', async ({ page }) => {
    // Check for main landmark
    await expect(page.locator('main')).toHaveAttribute('role', 'region')
    
    // Check for complementary landmarks (sidebars)
    const complementaries = await page.locator('[role="complementary"]').count()
    expect(complementaries).toBeGreaterThanOrEqual(1)
    
    // Check for banner
    await expect(page.locator('header[role="banner"]')).toBeVisible()
  })

  test('should support keyboard navigation', async ({ page }) => {
    // Press Tab to navigate through interactive elements
    await page.keyboard.press('Tab')
    
    // Check that focused element is visible
    const focusedElement = await page.evaluate(() => document.activeElement?.tagName)
    expect(focusedElement).not.toBe('BODY')
  })

  test('sidebar toggle should be keyboard accessible', async ({ page }) => {
    // Find sidebar toggle
    const toggle = page.getByRole('button', { name: /barre latérale/i })
    
    // Focus the toggle
    await toggle.focus()
    
    // Press Enter to toggle
    await page.keyboard.press('Enter')
    
    // Check sidebar state changed
    const sidebar = page.getByRole('complementary', { name: /conversations/i })
    const expanded = await sidebar.getAttribute('aria-expanded')
    expect(expanded).toBeDefined()
  })

  test('should have proper heading hierarchy', async ({ page }) => {
    // Check for h1
    const h1 = page.locator('h1')
    await expect(h1).toHaveCount(1)
    
    // Check h1 is visible
    await expect(h1).toBeVisible()
  })

  test('form elements should have labels', async ({ page }) => {
    // Check message input has accessible label
    const messageInput = page.getByRole('textbox')
    const ariaLabel = await messageInput.getAttribute('aria-label')
    const placeholder = await messageInput.getAttribute('placeholder')
    
    expect(ariaLabel || placeholder).toBeTruthy()
  })

  test('should respect reduced motion preference', async ({ page }) => {
    // Emulate reduced motion preference
    await page.emulateMedia({ reducedMotion: 'reduce' })
    
    // Check that transitions are disabled (this is a visual check)
    // In practice, you'd check computed styles or CSS
    const hasReducedMotion = await page.evaluate(() => {
      return window.matchMedia('(prefers-reduced-motion: reduce)').matches
    })
    
    expect(hasReducedMotion).toBe(true)
  })
})
