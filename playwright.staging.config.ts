import { defineConfig, devices } from '@playwright/test'

const stagingWebUrl = process.env.STAGING_WEB_URL
if (!stagingWebUrl) throw new Error('STAGING_WEB_URL is required for staging E2E runs.')

try {
  new URL(stagingWebUrl)
} catch {
  throw new Error('STAGING_WEB_URL must be an absolute URL.')
}

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: false,
  forbidOnly: true,
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? 'github' : 'list',
  globalSetup: './tests/e2e/staging-setup.ts',
  use: {
    baseURL: stagingWebUrl,
    trace: 'on-first-retry',
    ...devices['Desktop Chrome'],
  },
})
