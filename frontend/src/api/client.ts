import axios from 'axios'
import { useAuthStore } from '../stores/auth'

const apiClient = axios.create({
  baseURL: '',
  timeout: 15000,
  withCredentials: true,
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
type RefreshQueueEntry = {
  resolve: (token: string) => void
  reject: (error: unknown) => void
}

let refreshQueue: RefreshQueueEntry[] = []

function processQueueSuccess(token: string): void {
  refreshQueue.forEach(({ resolve }) => resolve(token))
  refreshQueue = []
}

function processQueueError(error: unknown): void {
  refreshQueue.forEach(({ reject }) => reject(error))
  refreshQueue = []
}

// Handle 401: refresh token then retry, or logout
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config

    if (error.response?.status !== 401 || !original || original._retry) {
      return Promise.reject(error)
    }

    const auth = useAuthStore()

    if (!auth.isAuthenticated) {
      auth.logout()
      return Promise.reject(error)
    }

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        refreshQueue.push({
          resolve: (token: string) => {
            original.headers = original.headers ?? {}
            original.headers.Authorization = `Bearer ${token}`
            resolve(apiClient(original))
          },
          reject,
        })
      })
    }

    original._retry = true
    isRefreshing = true

    try {
      const success = await auth.refreshAccessToken()

      if (!success || !auth.accessToken) {
        processQueueError(error)
        return Promise.reject(error)
      }

      processQueueSuccess(auth.accessToken)
      original.headers = original.headers ?? {}
      original.headers.Authorization = `Bearer ${auth.accessToken}`
      return apiClient(original)
    } catch (refreshError) {
      processQueueError(refreshError)
      return Promise.reject(refreshError)
    } finally {
      isRefreshing = false
    }
  },
)

export default apiClient
