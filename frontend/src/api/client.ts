import axios from 'axios'
import { useAuthStore } from '../stores/auth'

const apiClient = axios.create({
  baseURL: '',
  timeout: 15000,
})

// Inject Authorization header on every request
apiClient.interceptors.request.use((config) => {
  const auth = useAuthStore()
  if (auth.accessToken) {
    config.headers.Authorization = `Bearer ${auth.accessToken}`
  }
  return config
})

let isRefreshing = false
let refreshQueue: Array<(token: string) => void> = []

function processQueue(token: string): void {
  refreshQueue.forEach((resolve) => resolve(token))
  refreshQueue = []
}

// Handle 401: refresh token then retry, or logout
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config

    if (error.response?.status !== 401 || original._retry) {
      return Promise.reject(error)
    }

    const auth = useAuthStore()

    if (!auth.refreshToken) {
      auth.logout()
      return Promise.reject(error)
    }

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        refreshQueue.push((token: string) => {
          original.headers.Authorization = `Bearer ${token}`
          resolve(apiClient(original))
        })
        // Attach reject for cleanup (unused but prevents unhandled rejection)
        void reject
      })
    }

    original._retry = true
    isRefreshing = true

    const success = await auth.refreshAccessToken()
    isRefreshing = false

    if (!success || !auth.accessToken) {
      return Promise.reject(error)
    }

    processQueue(auth.accessToken)
    original.headers.Authorization = `Bearer ${auth.accessToken}`
    return apiClient(original)
  },
)

export default apiClient
