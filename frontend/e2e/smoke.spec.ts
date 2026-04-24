import { test, expect } from '@playwright/test'

/**
 * Smoke test — validates the critical user path:
 * login → change forced password → dashboard → contacts → client invoices → payments.
 *
 * Requires a clean backend (fresh DB bootstrapped with admin/changeme).
 */

const ADMIN_USER = 'admin'
const BOOTSTRAP_PASSWORD = 'changeme'
const NEW_PASSWORD = 'SecurePass1'

test.describe('Smoke test — happy path', () => {
  test('login → dashboard → contacts → invoices → payments', async ({ page }) => {
    // ── Step 1: Login ────────────────────────────────────────────────
    await page.goto('/login')
    await expect(page.locator('h1')).toContainText('Solde')

    await page.locator('#username').fill(ADMIN_USER)
    await page.locator('#password input').fill(BOOTSTRAP_PASSWORD)
    await page.locator('button[type="submit"]').click()

    // ── Step 2: Forced password change (BL-053) ──────────────────────
    // After login with bootstrap password, the app redirects to profile
    await page.waitForURL('**/profile')
    await expect(page.locator('text=Sécurité du compte')).toBeVisible()

    await page.locator('#profile-current-password input').fill(BOOTSTRAP_PASSWORD)
    await page.locator('#profile-new-password input').fill(NEW_PASSWORD)
    await page.locator('#profile-confirm-password input').fill(NEW_PASSWORD)
    await page.getByRole('button', { name: 'Changer le mot de passe' }).click()

    // Password changed → redirected to login
    await page.waitForURL('**/login')

    // ── Step 3: Re-login with new password ───────────────────────────
    await page.locator('#username').fill(ADMIN_USER)
    await page.locator('#password input').fill(NEW_PASSWORD)
    await page.locator('button[type="submit"]').click()

    // ── Step 4: Dashboard ────────────────────────────────────────────
    await page.waitForURL('**/dashboard')
    await expect(page.getByRole('heading', { name: 'Tableau de bord' })).toBeVisible()

    // ── Step 5: Navigate to Contacts ─────────────────────────────────
    await page.getByRole('link', { name: 'Contacts' }).click()
    await page.waitForURL('**/contacts')
    await expect(page.getByRole('heading', { name: 'Contacts', exact: true })).toBeVisible()

    // ── Step 6: Navigate to Client Invoices ──────────────────────────
    await page.getByRole('link', { name: 'Factures clients' }).click()
    await page.waitForURL('**/invoices/client')
    await expect(page.getByRole('heading', { name: 'Factures clients', exact: true })).toBeVisible()

    // ── Step 7: Navigate to Payments ─────────────────────────────────
    await page.getByRole('link', { name: 'Paiements' }).click()
    await page.waitForURL('**/payments')
    await expect(page.getByRole('heading', { name: 'Paiements', exact: true })).toBeVisible()
  })
})
