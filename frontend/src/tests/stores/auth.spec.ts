/// <reference types="vitest/globals" />

import { setActivePinia, createPinia } from 'pinia'
import * as authApi from '../../api/auth'
import { useAuthStore } from '../../stores/auth'

const mockLoginApi = vi.spyOn(authApi, 'loginApi')
const mockRefreshApi = vi.spyOn(authApi, 'refreshApi')
const mockGetMeApi = vi.spyOn(authApi, 'getMeApi')

const mockUser = {
  id: 1,
  username: 'admin',
  email: 'admin@example.com',
  role: 'admin' as const,
  is_active: true,
  created_at: '2025-01-01T00:00:00',
}

const mockTokens = {
  access_token: 'access.token.value',
  refresh_token: 'refresh.token.value',
  token_type: 'bearer',
}

describe('useAuthStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    mockLoginApi.mockReset()
    mockRefreshApi.mockReset()
    mockGetMeApi.mockReset()
  })

  it('has correct initial state when localStorage is empty', () => {
    const store = useAuthStore()
    expect(store.accessToken).toBeNull()
    expect(store.refreshToken).toBeNull()
    expect(store.user).toBeNull()
    expect(store.loading).toBe(false)
    expect(store.error).toBeNull()
  })

  it('isAuthenticated is false when no token', () => {
    const store = useAuthStore()
    expect(store.isAuthenticated).toBe(false)
  })

  it('isAuthenticated is true when accessToken is set', () => {
    const store = useAuthStore()
    store.accessToken = 'some.token'
    expect(store.isAuthenticated).toBe(true)
  })

  it('isAdmin returns true only for ADMIN role', () => {
    const store = useAuthStore()
    store.user = { ...mockUser, role: 'admin' }
    expect(store.isAdmin).toBe(true)
    store.user = { ...mockUser, role: 'tresorier' }
    expect(store.isAdmin).toBe(false)
  })

  it('login success sets tokens and fetches user', async () => {
    mockLoginApi.mockResolvedValueOnce(mockTokens)
    mockGetMeApi.mockResolvedValueOnce(mockUser)

    const store = useAuthStore()
    await store.login('admin', 'password')

    expect(store.accessToken).toBe(mockTokens.access_token)
    expect(store.refreshToken).toBe(mockTokens.refresh_token)
    expect(store.user).toEqual(mockUser)
    expect(store.error).toBeNull()
    expect(store.loading).toBe(false)
  })

  it('login success persists tokens to localStorage', async () => {
    mockLoginApi.mockResolvedValueOnce(mockTokens)
    mockGetMeApi.mockResolvedValueOnce(mockUser)

    const store = useAuthStore()
    await store.login('admin', 'password')

    expect(localStorage.getItem('access_token')).toBe(mockTokens.access_token)
    expect(localStorage.getItem('refresh_token')).toBe(mockTokens.refresh_token)
  })

  it('login failure sets error and clears tokens', async () => {
    mockLoginApi.mockRejectedValueOnce({ response: { status: 401 } })

    const store = useAuthStore()
    await store.login('admin', 'wrong')

    expect(store.accessToken).toBeNull()
    expect(store.user).toBeNull()
    expect(store.error).not.toBeNull()
    expect(store.loading).toBe(false)
  })

  it('logout clears state and localStorage', () => {
    const store = useAuthStore()
    store.accessToken = mockTokens.access_token
    store.refreshToken = mockTokens.refresh_token
    store.user = mockUser
    localStorage.setItem('access_token', mockTokens.access_token)
    localStorage.setItem('refresh_token', mockTokens.refresh_token)

    store.logout()

    expect(store.accessToken).toBeNull()
    expect(store.refreshToken).toBeNull()
    expect(store.user).toBeNull()
    expect(localStorage.getItem('access_token')).toBeNull()
    expect(localStorage.getItem('refresh_token')).toBeNull()
  })

  it('initFromStorage restores tokens from localStorage', () => {
    localStorage.setItem('access_token', mockTokens.access_token)
    localStorage.setItem('refresh_token', mockTokens.refresh_token)

    const store = useAuthStore()
    store.initFromStorage()

    expect(store.accessToken).toBe(mockTokens.access_token)
    expect(store.refreshToken).toBe(mockTokens.refresh_token)
  })

  it('refreshAccessToken updates accessToken on success', async () => {
    const newAccess = 'new.access.token'
    mockRefreshApi.mockResolvedValueOnce({
      ...mockTokens,
      access_token: newAccess,
    })

    const store = useAuthStore()
    store.refreshToken = mockTokens.refresh_token
    const result = await store.refreshAccessToken()

    expect(result).toBe(true)
    expect(store.accessToken).toBe(newAccess)
    expect(localStorage.getItem('access_token')).toBe(newAccess)
  })

  it('refreshAccessToken calls logout on failure', async () => {
    mockRefreshApi.mockRejectedValueOnce(new Error('expired'))

    const store = useAuthStore()
    store.refreshToken = 'expired.token'
    const result = await store.refreshAccessToken()

    expect(result).toBe(false)
    expect(store.accessToken).toBeNull()
  })
})
