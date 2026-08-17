import { defineConfig, devices } from '@playwright/test'
import os from 'node:os'
import path from 'node:path'

const databasePath = path.join(os.tmpdir(), `cash-flow-simulator-e2e-${process.pid}.sqlite`)
const backendPort = process.env.E2E_BACKEND_PORT ?? '8000'
const frontendPort = process.env.E2E_FRONTEND_PORT ?? '5173'

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: false,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 2 : 0,
  reporter: process.env.CI ? 'github' : 'list',
  use: {
    baseURL: `http://127.0.0.1:${frontendPort}`,
    trace: 'on-first-retry',
    ...devices['Desktop Chrome'],
  },
  webServer: [
    {
      command: `python -m uvicorn backend.api:app --host 127.0.0.1 --port ${backendPort}`,
      url: `http://127.0.0.1:${backendPort}/ready`,
      reuseExistingServer: false,
      timeout: 120_000,
      env: {
        DATABASE_PATH: databasePath,
        CORS_ORIGINS: `http://127.0.0.1:${frontendPort}`,
      },
    },
    {
      command: `npm run dev -- --host 127.0.0.1 --port ${frontendPort}`,
      url: `http://127.0.0.1:${frontendPort}`,
      reuseExistingServer: false,
      timeout: 120_000,
      env: {
        VITE_API_URL: `http://127.0.0.1:${backendPort}`,
      },
    },
  ],
})