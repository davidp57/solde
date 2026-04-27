import { fileURLToPath, URL } from 'node:url'
import { readFileSync } from 'node:fs'

import { defineConfig, type PluginOption } from 'vite'
import vue from '@vitejs/plugin-vue'

const isVitest = process.env.VITEST === 'true' || process.env.NODE_ENV === 'test'
const plugins: PluginOption[] = [vue()]

if (!isVitest) {
  const { default: vueDevTools } = await import('vite-plugin-vue-devtools')
  plugins.push(vueDevTools())
}

const pyproject = readFileSync(new URL('../pyproject.toml', import.meta.url), 'utf-8')
const versionMatch = pyproject.match(/^version\s*=\s*"([^"]+)"/m)
const appVersion = versionMatch ? versionMatch[1] : '0.0.0'

// https://vite.dev/config/
export default defineConfig({
  plugins,
  define: {
    __APP_VERSION__: JSON.stringify(appVersion),
  },
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    allowedHosts: ['.ngrok-free.dev'],
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
})
