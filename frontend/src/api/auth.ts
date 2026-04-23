import axios from 'axios'
import apiClient from './client'
import type {
  LoginRequest,
  PasswordChangeRequest,
  TokenResponse,
  UserRead,
  UserSelfUpdate,
} from './types'

export async function loginApi(request: LoginRequest): Promise<TokenResponse> {
  // FastAPI OAuth2PasswordRequestForm expects form data
  const form = new URLSearchParams()
  form.append('username', request.username)
  form.append('password', request.password)

  const response = await axios.post<TokenResponse>('/api/auth/login', form, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    withCredentials: true,
  })
  return response.data
}

export async function refreshApi(): Promise<TokenResponse> {
  const response = await axios.post<TokenResponse>('/api/auth/refresh', null, {
    withCredentials: true,
  })
  return response.data
}

export async function logoutApi(accessToken: string): Promise<void> {
  await axios.post('/api/auth/logout', null, {
    headers: { Authorization: `Bearer ${accessToken}` },
    withCredentials: true,
  })
}

export async function getMeApi(accessToken: string): Promise<UserRead> {
  const response = await axios.get<UserRead>('/api/auth/me', {
    headers: { Authorization: `Bearer ${accessToken}` },
  })
  return response.data
}

export async function updateMyProfileApi(payload: UserSelfUpdate): Promise<UserRead> {
  const response = await apiClient.patch<UserRead>('/api/auth/me', payload)
  return response.data
}

export async function changeMyPasswordApi(payload: PasswordChangeRequest): Promise<void> {
  await apiClient.post('/api/auth/me/change-password', payload)
}
