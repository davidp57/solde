import { fileURLToPath, URL } from 'node:url'

import { defineConfig, type PluginOption } from 'vite'
import vue from '@vitejs/plugin-vue'

const isVitest = process.env.VITEST === 'true' || process.env.NODE_ENV === 'test'
const plugins: PluginOption[] = [vue()]

if (!isVitest) {
  const { default: vueDevTools } = await import('vite-plugin-vue-devtools')
  plugins.push(vueDevTools())
}

// https://vite.dev/config/
export default defineConfig({
  plugins,
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
