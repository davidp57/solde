import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { defineConfig } from '@playwright/test'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const rootDir = path.resolve(__dirname, '..')
const venvScriptsDir = process.platform === 'win32' ? 'Scripts' : 'bin'
const venvPythonName = process.platform === 'win32' ? 'python.exe' : 'python'
const pythonExe =
  process.env.PLAYWRIGHT_PYTHON ??
  path.join(rootDir, '.venv', venvScriptsDir, venvPythonName)

export default defineConfig({
  testDir: './e2e',
  timeout: 60_000,
  retries: 0,
  use: {
    baseURL: 'http://localhost:5173',
    headless: true,
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { browserName: 'chromium' },
    },
  ],
  /* Start both backend and frontend before running tests */
  webServer: [
    {
      command: `"${pythonExe}" -m uvicorn backend.main:app --port 8000`,
      cwd: rootDir,
      port: 8000,
      reuseExistingServer: true,
      timeout: 30_000,
      env: {
        DATABASE_URL: 'sqlite+aiosqlite:///./data/e2e-test.db',
        DEBUG: 'true',
        JWT_SECRET_KEY: 'e2e-test-secret-key-at-least-32-characters-long',
      },
    },
    {
      command: 'npx vite --port 5173',
      port: 5173,
      reuseExistingServer: true,
      timeout: 30_000,
    },
  ],
})
