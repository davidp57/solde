import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { loginApi, refreshApi, logoutApi, getMeApi } from '../api/auth'
import type { UserRead } from '../api/types'

const ACCESS_TOKEN_KEY = 'access_token'
const DEV_AUTO_LOGIN_SUPPRESSED_KEY = 'dev_auto_login_suppressed'

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref<string | null>(null)
  const user = ref<UserRead | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)
  const devAutoLoginAttempted = ref(false)

  const isAuthenticated = computed(() => accessToken.value !== null)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isGestionnaire = computed(() => user.value?.role === 'secretaire')
  const isTresorier = computed(
    () => user.value?.role === 'admin' || user.value?.role === 'tresorier',
  )
  const canAccessManagement = computed(
    () =>
      user.value?.role === 'secretaire' ||
      user.value?.role === 'tresorier' ||
      user.value?.role === 'admin',
  )
  const canAccessAccounting = computed(
    () => user.value?.role === 'tresorier' || user.value?.role === 'admin',
  )
  const canManageApplication = computed(() => user.value?.role === 'admin')
  const mustChangePassword = computed(() => user.value?.must_change_password === true)

  function saveAccessToken(access: string): void {
    accessToken.value = access
    localStorage.setItem(ACCESS_TOKEN_KEY, access)
  }

  function clearTokens(): void {
    accessToken.value = null
    localStorage.removeItem(ACCESS_TOKEN_KEY)
  }

  function canUseDevAutoLogin(): boolean {
    const isDevRuntime = import.meta.env.DEV || import.meta.env.MODE === 'test'
    return isDevRuntime && import.meta.env.VITE_DEV_AUTO_LOGIN === 'true'
  }

  function isDevAutoLoginSuppressed(): boolean {
    return sessionStorage.getItem(DEV_AUTO_LOGIN_SUPPRESSED_KEY) === 'true'
  }

  function clearDevAutoLoginSuppression(): void {
    sessionStorage.removeItem(DEV_AUTO_LOGIN_SUPPRESSED_KEY)
  }

  function initFromStorage(): void {
    const access = localStorage.getItem(ACCESS_TOKEN_KEY)
    if (access) accessToken.value = access
  }

  async function login(username: string, password: string): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const tokens = await loginApi({ username, password })
      clearDevAutoLoginSuppression()
      saveAccessToken(tokens.access_token)
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

  function logout(options?: { preventDevAutoLogin?: boolean }): void {
    if (options?.preventDevAutoLogin) {
      sessionStorage.setItem(DEV_AUTO_LOGIN_SUPPRESSED_KEY, 'true')
    }
    if (accessToken.value) {
      logoutApi(accessToken.value).catch(() => { /* best effort */ })
    }
    clearTokens()
    user.value = null
    error.value = null
    devAutoLoginAttempted.value = false
  }

  async function maybeAutoLoginForDev(): Promise<boolean> {
    if (
      accessToken.value ||
      devAutoLoginAttempted.value ||
      !canUseDevAutoLogin() ||
      isDevAutoLoginSuppressed()
    ) {
      return isAuthenticated.value
    }

    devAutoLoginAttempted.value = true
    const username = import.meta.env.VITE_DEV_AUTO_LOGIN_USERNAME || 'admin'
    const password = import.meta.env.VITE_DEV_AUTO_LOGIN_PASSWORD || 'changeme'
    await login(username, password)
    return isAuthenticated.value
  }

  async function refreshAccessToken(): Promise<boolean> {
    try {
      const tokens = await refreshApi()
      saveAccessToken(tokens.access_token)
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
    user,
    loading,
    error,
    isAuthenticated,
    isAdmin,
    isGestionnaire,
    isTresorier,
    canAccessManagement,
    canAccessAccounting,
    canManageApplication,
    mustChangePassword,
    initFromStorage,
    login,
    logout,
    maybeAutoLoginForDev,
    refreshAccessToken,
    fetchMe,
  }
})
