import { expect, test } from '@playwright/test'

test('registers, saves a scenario, and exposes saved item controls', async ({ page }) => {
  const email = `e2e-${Date.now()}-${crypto.randomUUID()}@example.com`
  const password = 'correct-horse-battery-staple'

  await page.goto('/')
  await page.getByRole('tab', { name: 'Create account' }).click()
  await page.getByLabel('Email address').fill(email)
  await page.getByLabel('Password').fill(password)
  await page.getByRole('button', { name: /Create my workspace/ }).click()

  await expect(page.getByRole('heading', { name: 'Projection', exact: true })).toBeVisible()
  await page.getByRole('button', { name: 'Sign out' }).click()
  await page.getByRole('tab', { name: 'Sign in' }).click()
  await page.getByLabel('Email address').fill(email)
  await page.getByLabel('Password').fill(password)
  await page.getByRole('button', { name: /Sign in to cashflow/ }).click()
  await expect(page.getByRole('heading', { name: 'Projection', exact: true })).toBeVisible()
  await page.getByRole('button', { name: /Add item/ }).click()

  const itemForm = page.locator('form.item-form')
  await expect(itemForm.getByRole('heading', { name: 'Start your account' })).toBeVisible()
  await itemForm.getByLabel('Starting balance').fill('1200')
  await itemForm.getByLabel('Name').fill('Rent')
  await itemForm.getByLabel('Amount').fill('450')
  await itemForm.getByLabel('First date').fill('2026-08-20')
  await itemForm.getByRole('button', { name: 'Save and project' }).click()

  await expect(page.getByText('Rent').first()).toBeVisible()
  const projectionPanel = page.locator('section.projection-panel').first()
  await expect(projectionPanel.getByRole('heading', { name: '90-day projection' })).toBeVisible()
  await expect(projectionPanel.locator('svg[aria-label="Projected balance line chart"]')).toBeVisible()

  await page.getByRole('button', { name: /Add item/ }).click()
  const incomeForm = page.locator('form.item-form')
  await incomeForm.getByRole('button', { name: 'Income', exact: true }).click()
  await incomeForm.getByLabel('Name').fill('Paycheck')
  await incomeForm.getByLabel('Amount').fill('900')
  await incomeForm.getByLabel('First date').fill('2026-08-21')
  await incomeForm.getByRole('button', { name: 'Save and project' }).click()

  await expect(page.getByText('Paycheck')).toBeVisible()
  await page.getByRole('button', { name: 'Bills', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Bills', exact: true })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Edit Rent' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Pause Rent' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Delete Rent' })).toBeVisible()
  await page.getByRole('button', { name: 'Pause Rent' }).click()
  await expect(page.getByRole('button', { name: 'Resume Rent' })).toBeVisible()
  await page.getByRole('button', { name: 'Resume Rent' }).click()
  await expect(page.getByRole('button', { name: 'Pause Rent' })).toBeVisible()

  await page.getByRole('button', { name: 'Income', exact: true }).click()
  await expect(page.getByRole('heading', { name: 'Income', exact: true })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Edit Paycheck' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Pause Paycheck' })).toBeVisible()
  await expect(page.getByRole('button', { name: 'Delete Paycheck' })).toBeVisible()
})