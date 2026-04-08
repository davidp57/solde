import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { loginApi, refreshApi, getMeApi } from '../api/auth'
import type { UserRead } from '../api/types'

const ACCESS_TOKEN_KEY = 'access_token'
const REFRESH_TOKEN_KEY = 'refresh_token'

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref<string | null>(null)
  const refreshToken = ref<string | null>(null)
  const user = ref<UserRead | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  const isAuthenticated = computed(() => accessToken.value !== null)
  const isAdmin = computed(() => user.value?.role === 'ADMIN')
  const isTresorier = computed(
    () => user.value?.role === 'ADMIN' || user.value?.role === 'TRESORIER',
  )

  function saveTokens(access: string, refresh: string): void {
    accessToken.value = access
    refreshToken.value = refresh
    localStorage.setItem(ACCESS_TOKEN_KEY, access)
    localStorage.setItem(REFRESH_TOKEN_KEY, refresh)
  }

  function clearTokens(): void {
    accessToken.value = null
    refreshToken.value = null
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  }

  function initFromStorage(): void {
    const access = localStorage.getItem(ACCESS_TOKEN_KEY)
    const refresh = localStorage.getItem(REFRESH_TOKEN_KEY)
    if (access) accessToken.value = access
    if (refresh) refreshToken.value = refresh
  }

  async function login(username: string, password: string): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const tokens = await loginApi({ username, password })
      saveTokens(tokens.access_token, tokens.refresh_token)
      user.value = await getMeApi(tokens.access_token)
    } catch (err: unknown) {
      clearTokens()
      user.value = null
      const status = (err as { response?: { status?: number } }).response?.status
      if (status === 401) {
        error.value = 'invalid_credentials'
      } else if (!status) {
        error.value = 'network_error'
      } else {
        error.value = 'unknown_error'
      }
    } finally {
      loading.value = false
    }
  }

  function logout(): void {
    clearTokens()
    user.value = null
    error.value = null
  }

  async function refreshAccessToken(): Promise<boolean> {
    if (!refreshToken.value) {
      logout()
      return false
    }
    try {
      const tokens = await refreshApi(refreshToken.value)
      saveTokens(tokens.access_token, tokens.refresh_token)
      return true
    } catch {
      logout()
      return false
    }
  }

  async function fetchMe(): Promise<void> {
    if (!accessToken.value) return
    try {
      user.value = await getMeApi(accessToken.value)
    } catch {
      logout()
    }
  }

  return {
    accessToken,
    refreshToken,
    user,
    loading,
    error,
    isAuthenticated,
    isAdmin,
    isTresorier,
    initFromStorage,
    login,
    logout,
    refreshAccessToken,
    fetchMe,
  }
})
