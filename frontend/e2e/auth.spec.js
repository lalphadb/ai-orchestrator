/**
 * Authentication E2E Tests
 */

import { test, expect } from '@playwright/test'

test.describe('Authentication', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
  })

  test('should display login form', async ({ page }) => {
    // Check form elements are visible
    await expect(page.getByLabel(/email/i)).toBeVisible()
    await expect(page.getByLabel(/mot de passe|password/i)).toBeVisible()
    await expect(page.getByRole('button', { name: /connexion|login/i })).toBeVisible()
  })

  test('should show error for invalid credentials', async ({ page }) => {
    // Fill in invalid credentials
    await page.getByLabel(/email/i).fill('invalid@example.com')
    await page.getByLabel(/mot de passe|password/i).fill('wrongpassword')
    await page.getByRole('button', { name: /connexion|login/i }).click()

    // Check error message
    await expect(page.getByText(/erreur|error|invalide|invalid/i)).toBeVisible()
  })

  test('should navigate to dashboard after successful login', async ({ page }) => {
    // Note: This test assumes test credentials exist
    // In a real scenario, you might need to seed the database
    await page.getByLabel(/email/i).fill('test@example.com')
    await page.getByLabel(/mot de passe|password/i).fill('testpassword')
    await page.getByRole('button', { name: /connexion|login/i }).click()

    // Should redirect to dashboard
    await expect(page).toHaveURL(/.*dashboard.*/)
  })
})
